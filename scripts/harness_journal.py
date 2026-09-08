"""Opt-in local development journal. Not a sandbox, approval store or bug oracle.

Python 3.11+ standard library; fixed check/verify only, no commands from database.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess

import agent_harness as h

DB = "tmp/agent-harness/journal.sqlite3"
VERSION = "1"
STATES = ("reported", "reproduced", "fix_proposed", "verified_local", "reviewed_closed")
TRANSITION_SCAN_LIMIT = 10_000
CATEGORIES = {"design_gap", "contract_conflict", "code_defect", "test_gap", "operational"}
GUIDANCE = {
    "design_gap": "Review the invariant and add positive/negative counterexamples before implementation.",
    "contract_conflict": "Reconcile producer/consumer definitions, then add a boundary regression.",
    "code_defect": "Reproduce on a synthetic fixture; a reported finding is not a confirmed defect.",
    "test_gap": "Specify the missing assertion, oracle and failure schedule before claiming coverage.",
    "operational": "Inspect local operation evidence; distinguish infrastructure failure from product defects.",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def encoded(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def sha(value) -> str:
    return hashlib.sha256(encoded(value).encode()).hexdigest()


def identifier(value: str) -> str:
    h.require(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{2,63}", value),
              "Invalid journal identifier")
    return value


def database_path(root: Path) -> Path:
    path = h.local(root, DB)
    for suffix in ("-journal", "-wal", "-shm"):
        h.local(root, DB + suffix)
    return path


def connect(root: Path, write: bool = False) -> sqlite3.Connection:
    path = database_path(root)
    h.require(path.is_file(), "Journal missing; explicitly run init first")
    con = sqlite3.connect(path.as_uri() + ("?mode=rw" if write else "?mode=ro"), uri=True,
                          timeout=3, isolation_level=None)
    try:
        con.execute("PRAGMA trusted_schema=OFF")
        con.execute("PRAGMA foreign_keys=ON")
        if not write:
            con.execute("PRAGMA query_only=ON")
        metadata = dict(con.execute("SELECT key,value FROM metadata"))
        h.require(metadata == {"version": VERSION, "root": str(root.resolve())},
                  "Wrong journal schema/repository; no automatic migration or reset")
        return con
    except Exception:
        con.close()
        raise


def initialize(root: Path) -> dict:
    path = database_path(root)
    if path.exists():
        with closing(connect(root)):
            return {"result": "already_initialized", "path": DB}
    # Never silently put the journal in the tracked tree or overwrite an existing file.
    ignored = subprocess.run(["git", "-C", str(root), "check-ignore", "--no-index", "-q", "--", DB],
                             capture_output=True, timeout=30)
    h.require(ignored.returncode == 0, "Journal path must be Git-ignored")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb"):
        pass
    # On failure leave the partial file for explicit investigation; never auto-delete/reset.
    with closing(sqlite3.connect(path.as_uri() + "?mode=rw", uri=True)) as con:
        con.execute("PRAGMA trusted_schema=OFF")
        con.executescript("""
            BEGIN IMMEDIATE;
            CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE runs(run_id TEXT PRIMARY KEY, baseline_hash TEXT NOT NULL,
                              scope_json TEXT NOT NULL);
            CREATE TABLE events(event_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
                request_hash TEXT NOT NULL, kind TEXT NOT NULL, created_utc TEXT NOT NULL,
                finished_utc TEXT, outcome TEXT NOT NULL, request_json TEXT NOT NULL, result_json TEXT);
            CREATE INDEX events_run ON events(run_id, created_utc);
        """)
        con.executemany("INSERT INTO metadata VALUES (?,?)", [("version", VERSION), ("root", str(root.resolve()))])
        con.commit()
    return {"result": "initialized", "path": DB, "authority": "diagnostic_only"}


def snapshot(root: Path, run_id: str) -> dict:
    path = h.run_path(root, identifier(run_id))
    h.require(path.stat().st_size <= 4_000_000, "Baseline exceeds journal snapshot limit")
    record = h.read_json(path)
    h.require(record.get("root") == str(root.resolve()) and record.get("schema_version") == 1,
              "Baseline repository/version mismatch")
    task = record["task"]
    identifier(task["id"])
    fields = {}
    for key in ("allowed_files", "required_outputs", "read_first", "checks", "actions"):
        values = h.string_list(task[key], key)
        h.require(len(values) <= 100, "Snapshot list too large")
        if key in {"allowed_files", "required_outputs", "read_first"}:
            for name in values:
                h.local(root, name)
        fields[key] = values
    # No objective/request prose, inventory contents, source bodies, credentials or raw output.
    fields.update({"run_id": run_id, "task_id": task["id"], "baseline_hash": h.digest(path),
                   "task_hash": record["task_sha256"], "state_hash": record["state_sha256"],
                   "baseline_head": record["head"], "task_path": record["task_path"]})
    h.local(root, fields["task_path"])
    for key in ("baseline_hash", "task_hash", "state_hash", "baseline_head"):
        h.require(isinstance(fields[key], str) and re.fullmatch(r"[0-9a-f]{40,64}", fields[key]),
                  "Malformed baseline hash")
    return fields


def checker_fingerprint() -> dict:
    # Provenance only; hashes are local and unsigned, not a trust root.
    base = Path(__file__).resolve().parent
    return {name: h.digest(base / name) for name in ("agent_harness.py", "harness_journal.py")}


def reserve(root: Path, scope: dict, event_id: str, kind: str, request: dict) -> bool:
    identifier(event_id)
    with closing(connect(root, write=True)) as con:
        con.execute("BEGIN IMMEDIATE")
        row = con.execute("SELECT baseline_hash FROM runs WHERE run_id=?", (scope["run_id"],)).fetchone()
        h.require(row is None or row[0] == scope["baseline_hash"],
                  "Journal run baseline changed; reconcile, do not overwrite history")
        con.execute("INSERT OR IGNORE INTO runs VALUES (?,?,?)",
                    (scope["run_id"], scope["baseline_hash"], encoded(scope)))
        old = con.execute("SELECT request_hash,run_id,kind FROM events WHERE event_id=?", (event_id,)).fetchone()
        if old:
            h.require(old == (sha(request), scope["run_id"], kind), "Event key conflict; no automatic rerun")
            con.commit()
            return False
        con.execute("INSERT INTO events VALUES (?,?,?,?,?,NULL,'pending',?,NULL)",
                    (event_id, scope["run_id"], sha(request), kind, now(), encoded(request)))
        con.commit()
        return True


def finish(root: Path, event_id: str, outcome: str, result: dict) -> None:
    with closing(connect(root, write=True)) as con:
        con.execute("BEGIN IMMEDIATE")
        changed = con.execute("UPDATE events SET outcome=?,result_json=?,finished_utc=? "
                              "WHERE event_id=? AND outcome='pending'",
                              (outcome, encoded(result), now(), event_id)).rowcount
        h.require(changed == 1, "Event no longer pending; cannot overwrite terminal evidence")
        con.commit()


def read_event(con: sqlite3.Connection, event_id: str) -> dict:
    identifier(event_id)
    row = con.execute("SELECT run_id,kind,outcome,created_utc,finished_utc,request_json,result_json "
                      "FROM events WHERE event_id=?", (event_id,)).fetchone()
    h.require(row is not None, "Unknown journal event")
    return {"event_id": event_id, "run_id": row[0], "kind": row[1], "outcome": row[2],
            "created_utc": row[3], "finished_utc": row[4], "request": json.loads(row[5]),
            "observation": json.loads(row[6]) if row[6] else None,
            "evidence_scope": "historical_local_observation_NOT_current_authority"}


def event(root: Path, event_id: str) -> dict:
    with closing(connect(root)) as con:
        return read_event(con, event_id)


def failure_code(exc: Exception) -> str:
    # Never persist raw exception text: it may contain private paths/content from a checker.
    if isinstance(exc, subprocess.TimeoutExpired):
        return "check_timeout"
    for prefix, code in (("Out-of-scope", "scope_drift"), ("Task changed", "task_drift"),
                         ("State changed", "state_drift"), ("HEAD changed", "head_drift"),
                         ("Roadmap changed", "plan_drift"), ("Missing/empty output", "missing_output"),
                         ("Verification modified", "verification_side_effect")):
        if str(exc).startswith(prefix):
            return code
    return "check_blocked_or_operational_error"


def check_summary(item: dict) -> dict:
    result = {"profile": item["check"], "exit_code": item["exit_code"]}
    if item["check"] == "harness":
        match = re.search(r"\bRan (\d+) tests? in", item.get("stderr", ""))
        result["tests_run"] = int(match[1]) if match else None
    elif item["check"] == "structure":
        try:
            data = json.loads(item.get("stdout", ""))
            for name in ("checks", "passed", "python_files_syntax_checked", "pdf_source_hashes_verified"):
                result[name] = data.get(name) if type(data.get(name)) is int else None
            for name in ("skipped", "failures"):
                result[name + "_count"] = len(data[name]) if isinstance(data.get(name), list) else None
        except (ValueError, TypeError, AttributeError):
            result["summary"] = "unavailable"
    return result


def capture(root: Path, run_id: str, event_id: str, phase: str, require_local_data: bool = False) -> dict:
    h.require(phase in {"check", "verify"}, "Only fixed check/verify permitted")
    h.require(phase == "verify" or not require_local_data, "Local-data flag requires verify")
    scope = snapshot(root, run_id)
    request = {"phase": phase, "require_local_data": require_local_data,
               "baseline_hash": scope["baseline_hash"], "checker_hashes": checker_fingerprint()}
    if reserve(root, scope, event_id, "check", request):
        # A crash leaves pending evidence; duplicate keys never execute the check again.
        try:
            h.require(h.digest(h.run_path(root, run_id)) == scope["baseline_hash"], "Task changed during capture")
            observed_tree = sha(h.inventory(root))
            observed = h.check_run(root, run_id) if phase == "check" else h.verify(root, run_id, require_local_data)
            h.require(sha(h.inventory(root)) == observed_tree, "Verification modified observed tree during capture")
            h.require(h.digest(h.run_path(root, run_id)) == scope["baseline_hash"], "Task changed during capture")
            h.require(checker_fingerprint() == request["checker_hashes"], "Verification modified checker")
            outcome = "passed" if observed.get("all_checks_passed", True) else "failed"
            safe = {"code": "fixed_checks_passed" if outcome == "passed" else "fixed_check_failure",
                    "changed_file_count": len(observed.get("changed_files", [])),
                    "observed_tree_sha256": observed_tree,
                    "checks": [check_summary(item) for item in observed.get("verification", [])],
                    "meaning": "mechanical_only_NOT_acceptance"}
        except (h.HarnessError, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
            outcome, safe = "blocked", {"code": failure_code(exc), "meaning": "inspect_local_evidence"}
        finish(root, event_id, outcome, safe)
    return event(root, event_id)


def evidence_ref(root: Path, evidence: str, line: int) -> dict:
    h.require(type(line) is int and line > 0, "Invalid evidence line")
    h.require(evidence.startswith("docs/") and evidence.endswith(".md"), "Finding evidence must be a reviewed docs Markdown reference")
    ref = h.local(root, evidence)
    h.require(ref.is_file() and ref.stat().st_size <= 1_000_000, "Evidence missing or too large")
    h.require(line <= len(ref.read_text(encoding="utf-8-sig").splitlines()), "Evidence line outside document")
    return {"evidence": evidence, "line": line, "evidence_sha256": h.digest(ref)}


def finding(root: Path, run_id: str, event_id: str, category: str, severity: str,
            evidence: str, line: int) -> dict:
    h.require(category in CATEGORIES and severity in {"P0", "P1", "P2", "P3"}, "Unknown finding category/severity")
    ref = evidence_ref(root, evidence, line)
    scope = snapshot(root, run_id)
    request = {"category": category, "reported_severity": severity, **ref, "baseline_hash": scope["baseline_hash"]}
    if reserve(root, scope, event_id, "finding", request):
        finish(root, event_id, "reported", {"authority": "reporter_assertion_NOT_confirmed_defect",
                                            "auto_fix": False})
    return event(root, event_id)


def finding_history(con: sqlite3.Connection, finding_id: str) -> dict:
    origin = read_event(con, finding_id)
    h.require(origin["kind"] == "finding" and origin["outcome"] == "reported", "Not a completed reported finding")
    rows = con.execute("SELECT event_id,request_json FROM events WHERE kind='finding_transition' LIMIT ?",
                       (TRANSITION_SCAN_LIMIT + 1,)).fetchall()
    h.require(len(rows) <= TRANSITION_SCAN_LIMIT, "Lifecycle scan limit reached; explicit indexing/schema review needed")
    by_parent = {}
    for event_id, raw in rows:
        request = json.loads(raw)
        if request.get("finding_id") == finding_id:
            parent = request["from_event"]
            h.require(parent not in by_parent, "Branched finding history; inspect without rewriting")
            by_parent[parent] = event_id
    chain = [origin]
    state = "reported"
    while chain[-1]["event_id"] in by_parent:
        next_event = read_event(con, by_parent.pop(chain[-1]["event_id"]))
        h.require(state != STATES[-1] and next_event["outcome"] == "recorded" and
                  next_event["request"]["to_state"] == STATES[STATES.index(state) + 1],
                  "Invalid finding transition history")
        state = next_event["request"]["to_state"]
        chain.append(next_event)
    h.require(not by_parent, "Orphaned finding transitions")
    return {"finding_id": finding_id, "origin_run": origin["run_id"], "state": state,
            "head_event": chain[-1]["event_id"], "history": chain,
            "authority": "recorded_evidence_workflow_NOT_authenticated_signoff_or_GO"}


def history(root: Path, finding_id: str) -> dict:
    with closing(connect(root)) as con:
        con.execute("BEGIN")
        return finding_history(con, identifier(finding_id))


def verified_binding(root: Path, con: sqlite3.Connection, scope: dict, chain: dict,
                     verification_id: str) -> dict:
    verified = read_event(con, identifier(verification_id))
    proposal = next(item for item in chain["history"] if item["request"].get("to_state") == "fix_proposed")
    h.require(verified["kind"] == "check" and verified["outcome"] == "passed" and
              verified["request"].get("phase") == "verify", "A passed verify event is required, not a scope check")
    recent = con.execute("SELECT event_id,request_json FROM events WHERE run_id=? AND kind='check' "
                         "ORDER BY rowid DESC LIMIT ?", (scope["run_id"], TRANSITION_SCAN_LIMIT + 1)).fetchall()
    h.require(len(recent) <= TRANSITION_SCAN_LIMIT, "Verification scan limit reached")
    latest_verify = next((key for key, raw in recent if json.loads(raw).get("phase") == "verify"), None)
    h.require(latest_verify == verification_id, "Use the latest verify; do not hide a newer failure or pending run")
    h.require(verified["run_id"] == scope["run_id"] == proposal["run_id"], "Verification must belong to the proposed repair run")
    h.require(verified["request"].get("baseline_hash") == scope["baseline_hash"] and
              verified["request"].get("checker_hashes") == checker_fingerprint(), "Stale verification baseline/checker")
    checks = verified["observation"].get("checks", [])
    h.require(len(checks) == len(scope["checks"]) and
              {item.get("profile") for item in checks} == set(scope["checks"]) and
              all(type(item.get("exit_code")) is int and item["exit_code"] == 0 for item in checks),
              "Incomplete or failed verification profiles")
    ordered = lambda event_id: con.execute("SELECT rowid FROM events WHERE event_id=?", (event_id,)).fetchone()[0]
    h.require(ordered(verification_id) > ordered(proposal["event_id"]), "Verification predates fix proposal")
    tree_hash = sha(h.inventory(root))
    h.require(verified["observation"].get("observed_tree_sha256") == tree_hash, "Verification does not match current observed tree")
    return {"verification_event": verification_id, "verification_hash": sha(verified),
            "verified_tree_sha256": tree_hash, "require_local_data": verified["request"].get("require_local_data", False)}


def transition(root: Path, run_id: str, finding_id: str, event_id: str, from_event: str,
               to_state: str, actor: str, evidence: str, line: int,
               verification: str | None = None, reviewer: str | None = None,
               review_evidence: str | None = None, review_line: int | None = None) -> dict:
    for value in (run_id, finding_id, event_id, from_event, actor):
        identifier(value)
    h.require(to_state in STATES[1:], "Unsupported target finding state")
    needs_verify = to_state in {"verified_local", "reviewed_closed"}
    h.require(bool(verification) == needs_verify, "Verification argument required only for verified/closed states")
    if verification:
        identifier(verification)
    is_close = to_state == "reviewed_closed"
    h.require((reviewer is not None and review_evidence is not None and review_line is not None) if is_close
              else (reviewer is None and review_evidence is None and review_line is None),
              "Closure requires explicit reviewer and review document; no inferred review")
    if reviewer:
        identifier(reviewer)
    scope = snapshot(root, run_id)
    request = {"finding_id": finding_id, "from_event": from_event, "to_state": to_state,
               "actor_label": actor, **evidence_ref(root, evidence, line),
               "verification_event": verification, "reviewer_label": reviewer,
               "review_ref": evidence_ref(root, review_evidence, review_line) if is_close else None,
               "baseline_hash": scope["baseline_hash"], "checker_hashes": checker_fingerprint()}
    # One transaction for predecessor check + append: no half-transition on crash.
    with closing(connect(root, write=True)) as con:
        con.execute("BEGIN IMMEDIATE")
        old = con.execute("SELECT request_hash,run_id,kind FROM events WHERE event_id=?", (event_id,)).fetchone()
        if old:
            h.require(old == (sha(request), run_id, "finding_transition"), "Event key conflict")
            return read_event(con, event_id)  # Historical retry; no currentness/approval claim.
        chain = finding_history(con, finding_id)
        h.require(chain["head_event"] == from_event, "Stale finding predecessor; reread history")
        h.require(chain["state"] != STATES[-1] and to_state == STATES[STATES.index(chain["state"]) + 1],
                  "Finding states cannot be skipped, rewound or auto-closed")
        h.check_run(root, run_id, require_outputs=False)
        h.require(snapshot(root, run_id) == scope, "Baseline changed during transition")
        row = con.execute("SELECT baseline_hash FROM runs WHERE run_id=?", (run_id,)).fetchone()
        h.require(row is None or row[0] == scope["baseline_hash"], "Journal run baseline changed")
        binding = verified_binding(root, con, scope, chain, verification) if needs_verify else {}
        if is_close:
            workers = {item["request"].get("actor_label", "").casefold() for item in chain["history"]
                       if item["request"].get("to_state") in {"fix_proposed", "verified_local"}}
            h.require(reviewer.casefold() not in workers, "Reviewer label must differ from repair/verification actor labels")
        # Pin docs after checks too; source content is never parsed as instructions or review approval.
        h.require(evidence_ref(root, evidence, line)["evidence_sha256"] == request["evidence_sha256"], "Evidence changed")
        if is_close:
            h.require(evidence_ref(root, review_evidence, review_line) == request["review_ref"], "Review evidence changed")
        result = {"state": to_state, **binding, "auto_fix": False,
                  "authority": "recorded_evidence_NOT_authenticated_review_or_product_GO"}
        con.execute("INSERT OR IGNORE INTO runs VALUES (?,?,?)", (run_id, scope["baseline_hash"], encoded(scope)))
        timestamp = now()
        con.execute("INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?)",
                    (event_id, run_id, sha(request), "finding_transition", timestamp, timestamp,
                     "recorded", encoded(request), encoded(result)))
        con.commit()
        return read_event(con, event_id)


def report(root: Path, run_id: str | None = None, limit: int = 20) -> dict:
    h.require(type(limit) is int and 1 <= limit <= 100, "Report limit must be 1..100")
    if run_id is not None:
        identifier(run_id)
    with closing(connect(root)) as con:
        rows = con.execute("SELECT event_id FROM events WHERE (? IS NULL OR run_id=?) "
                           "ORDER BY created_utc DESC,event_id DESC LIMIT ?", (run_id, run_id, limit)).fetchall()
        total = con.execute("SELECT count(*) FROM events WHERE (? IS NULL OR run_id=?)", (run_id, run_id)).fetchone()[0]
        run = con.execute("SELECT scope_json FROM runs WHERE run_id=?", (run_id,)).fetchone() if run_id else None
    events = [event(root, row[0]) for row in rows]
    finding_ids = {item["event_id"] if item["kind"] == "finding" else item["request"].get("finding_id")
                   for item in events if item["kind"] in {"finding", "finding_transition"} and item["outcome"] != "pending"}
    states = [history(root, key) for key in sorted(finding_ids)]
    return {"scope_snapshot": json.loads(run[0]) if run else None, "total_events": total,
            "returned_events": len(rows), "events": events,
            "finding_states": [{key: value for key, value in state.items() if key != "history"} for state in states],
            "limits": "Opt-in, incomplete, mutable local evidence; no bug completeness or product GO"}


def suggest(root: Path, run_id: str | None = None) -> dict:
    records = report(root, run_id, 100)
    proposals = []
    handled = set()
    states = {item["finding_id"]: item["state"] for item in records["finding_states"]}
    for item in records["events"]:
        if item["kind"] in {"finding", "finding_transition"} and item["outcome"] != "pending":
            key = item["event_id"] if item["kind"] == "finding" else item["request"]["finding_id"]
            if key in handled or states.get(key) == "reviewed_closed":
                continue
            handled.add(key)
            text = {"reproduced": "Propose one bounded fix and regression; proposal is not authorization.",
                    "fix_proposed": "Obtain repair authority, implement in scope, then capture verification.",
                    "verified_local": "Obtain explicit review evidence; tests alone must not close the finding."}.get(states.get(key))
            if text is None:
                text = GUIDANCE.get(item["request"].get("category"), "Review the original finding evidence manually.")
        elif item["outcome"] in {"failed", "blocked"}:
            text = "Inspect the failure evidence, reconcile scope if necessary, then propose one bounded regression task."
        elif item["outcome"] == "pending":
            text = "Operation may still run or may have been interrupted. Inspect it; do not infer failure/success or auto-retry."
        else:
            continue
        proposals.append({"event_id": item["event_id"], "proposal": text, "requires_review": True})
    return {"result": "proposals_only", "sampled_events": records["returned_events"],
            "total_events": records["total_events"], "proposals": proposals,
            "mutations_performed": False, "warning": "No commands, code, scope, approvals or task cards generated/executed"}


def exit_code(result: dict) -> int:
    return 1 if result.get("outcome") in {"blocked", "failed", "pending"} else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    cap = sub.add_parser("capture")
    cap.add_argument("--run", required=True)
    cap.add_argument("--event", required=True)
    cap.add_argument("--phase", choices=["check", "verify"], required=True)
    cap.add_argument("--require-local-data", action="store_true")
    note = sub.add_parser("finding")
    for flag in ("run", "event", "category", "severity", "evidence"):
        note.add_argument("--" + flag, required=True)
    note.add_argument("--line", required=True, type=int)
    move = sub.add_parser("transition")
    for flag in ("run", "finding", "event", "from-event", "actor", "evidence"):
        move.add_argument("--" + flag, required=True)
    move.add_argument("--to", choices=STATES[1:], required=True)
    move.add_argument("--line", required=True, type=int)
    move.add_argument("--verification")
    move.add_argument("--reviewer")
    move.add_argument("--review-evidence")
    move.add_argument("--review-line", type=int)
    view = sub.add_parser("history")
    view.add_argument("--finding", required=True)
    for name in ("report", "suggest"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--run")
        if name == "report":
            cmd.add_argument("--limit", default=20, type=int)
    args = parser.parse_args()
    try:
        if args.command == "init":
            result = initialize(h.ROOT)
        elif args.command == "capture":
            result = capture(h.ROOT, args.run, args.event, args.phase, args.require_local_data)
        elif args.command == "finding":
            result = finding(h.ROOT, args.run, args.event, args.category, args.severity, args.evidence, args.line)
        elif args.command == "transition":
            result = transition(h.ROOT, args.run, args.finding, args.event, args.from_event, args.to,
                                args.actor, args.evidence, args.line, args.verification, args.reviewer,
                                args.review_evidence, args.review_line)
        elif args.command == "history":
            result = history(h.ROOT, args.finding)
        elif args.command == "report":
            result = report(h.ROOT, args.run, args.limit)
        else:
            result = suggest(h.ROOT, args.run)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return exit_code(result)
    except (h.HarnessError, OSError, ValueError, KeyError, TypeError, sqlite3.Error, subprocess.SubprocessError):
        print(encoded({"result": "JOURNAL_BLOCKED", "reason": "Invalid input, stale/unsafe path or unavailable journal; no automatic reset/retry. Check local state; a reserved event may remain pending."}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
