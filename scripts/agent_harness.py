"""Local pre-product work harness; a drift detector, NOT a security sandbox.

No model calls, arbitrary command execution, approval writes or phase transitions.
Python 3.11+, standard library. Run from any directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
STATE = "docs/harness/project-state.json"
GATE = "Đã tới ASTRA-01: cần review AI Core workflow"
CHECKS = {
    "harness": ["-m", "unittest", "discover", "-s", "scripts/tests", "-p", "test_agent_harness*.py", "-v"],
    "structure": ["scripts/verify_structure.py"],
    "context-integrity": ["-m", "unittest", "discover", "-s", "ai-core/experiments/context-integrity-v0.1", "-p", "test_*.py", "-v"],
}
TASK_KEYS = {"schema_version", "id", "work_package", "objective", "request_basis", "kind",
             "actions", "read_first", "allowed_files", "required_outputs", "acceptance",
             "checks", "max_changed_files", "handoff"}
SAFE_ACTIONS = {"documentation", "offline_synthetic", "harness_maintenance", "public_web_research"}
PRODUCT_ACTIONS = {"product_runtime", "product_dependencies", "index_writer", "implementation_workflow"}
HISTORICAL_EXPERIMENTS = {
    "workflow-tabletop", "evidence-mapping", "evidence-contract", "pdf-pilot", "html-structure",
    "source-serialization", "context-review", "chunking-r1", "dense-retrieval-r2",
    "retrieval-r3", "retrieval-r4", "security-fixtures", "context-integrity-v0.1",
}


class HarnessError(ValueError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise HarnessError(message)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def local(root: Path, name: str) -> Path:
    require(isinstance(name, str) and bool(name), "Empty/non-string path")
    require(not any(c in name for c in "\\:*?[]\0") and not any(ord(c) < 32 for c in name),
            f"Non-canonical path: {name!r}")
    p = PurePosixPath(name)
    require(not p.is_absolute() and all(x not in {".", "..", ""} for x in name.split("/")),
            f"Path traversal/absolute path: {name}")
    require(p.parts[0].lower() != ".git", "Git metadata is outside harness scope")
    target = root / name
    require(target.resolve().is_relative_to(root.resolve()), f"Path escapes repository: {name}")
    # Reject symlinks/junctions, even when they resolve back into the repo.
    for ancestor in [target, *target.parents]:
        if ancestor == root:
            break
        attributes = getattr(ancestor.lstat(), "st_file_attributes", 0) if ancestor.exists() else 0
        require(not ancestor.is_symlink() and not attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT,
                f"Linked/reparse path unsupported: {name}")
    return target


def read_json(path: Path) -> dict:
    def unique(pairs):
        obj = {}
        for key, value in pairs:
            require(key not in obj, f"Duplicate JSON key: {key}")
            obj[key] = value
        return obj
    value = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique)
    require(isinstance(value, dict), "Expected JSON object")
    return value


def git(root: Path, *args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=False, timeout=30)
    require(result.returncode == 0, f"git {' '.join(args)} failed: {result.stderr.decode(errors='replace')}")
    return result.stdout


def inventory(root: Path) -> dict[str, str | None]:
    # Also hash PREEXISTING untracked files; git diff HEAD alone would miss them.
    names = git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z").decode("utf-8").split("\0")
    result = {}
    for name in sorted(set(names) - {""}):
        path = local(root, name)
        require(not path.is_dir(), f"Submodule/directory unsupported: {name}")
        result[name] = digest(path) if path.exists() else None
    return result


def changes(before: dict, after: dict) -> list[str]:
    # Missing and tracked-but-deleted both mean absent bytes.
    return sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))


def load_state(root: Path) -> dict:
    state = read_json(local(root, STATE))
    require(set(state) == {"schema_version", "stage", "plan", "plan_sha256", "next_work_package",
                           "astra", "read_first", "evidence_limits", "sequence", "last_handoff"},
            "Unknown/missing state fields")
    require(type(state["schema_version"]) is int and state["schema_version"] == 1, "Unsupported state version")
    require(state["stage"] == "pre_product_research", "This harness profile cannot authorize product work")
    require(state["astra"] == {"status": "pending_review_and_explicit_user_go"},
            "ASTRA cannot be unlocked by editing a JSON flag; review + explicit user GO required")
    require(state["next_work_package"] in {"WP-03", "WP-02", "WP-04"}, "Unknown next work package")
    require(state["sequence"] == ["WP-03", "WP-02", "WP-04", "ASTRA-01", "P6"], "Unreviewed sequence change")
    require(digest(local(root, state["plan"])) == state["plan_sha256"],
            "Roadmap changed: reconcile state against the active user request; do not silently refresh hash")
    for name in [*string_list(state["read_first"], "read_first"), state["last_handoff"]]:
        require(local(root, name).is_file(), f"Missing state reference: {name}")
    string_list(state["evidence_limits"], "evidence_limits")
    return state


def string_list(value, label: str) -> list[str]:
    require(isinstance(value, list) and bool(value) and all(isinstance(x, str) and x.strip() for x in value),
            f"{label} must be a nonempty string list")
    require(len(value) == len(set(value)), f"Duplicate values: {label}")
    return value


def protected(name: str) -> bool:
    name = name.lower()
    p = PurePosixPath(name)
    return (name.startswith(("data/", "infra/", "ai-core/src/", "backend/src/", "frontend/src/",
                             "frontend/public/"))
            or (len(p.parts) >= 3 and p.parts[:2] == ("ai-core", "experiments")
                and p.parts[2] in HISTORICAL_EXPERIMENTS)
            or p.name in {"pyproject.toml", "package.json", "package-lock.json", "uv.lock", "poetry.lock",
                           "pnpm-lock.yaml", "yarn.lock", "dockerfile", "docker-compose.yml"}
            or p.name.startswith((".env", "requirements")))


def validate_task(root: Path, task: dict, state: dict) -> None:
    require(set(task) == TASK_KEYS, "Unknown/missing task fields (no approval/command overrides)")
    require(type(task["schema_version"]) is int and task["schema_version"] == 1, "Unsupported task version")
    require(isinstance(task["id"], str) and re.fullmatch(r"[A-Z0-9][A-Z0-9-]{2,63}", task["id"]), "Invalid task ID")
    for field in ["objective", "request_basis"]:
        require(isinstance(task[field], str) and len(task[field].strip()) >= 20, f"Missing meaningful {field}")
    actions = set(string_list(task["actions"], "actions"))
    require(not actions & PRODUCT_ACTIONS, GATE)
    require(actions <= SAFE_ACTIONS, "Unsupported action: external processing/model runs/publication need separate review")
    require(task["kind"] in {"research", "maintenance"}, "Unsupported task kind")
    if task["kind"] == "research":
        require(task["work_package"] == state["next_work_package"], "Work package drift: reconcile request/plan first")
        require("harness_maintenance" not in actions, "Research cannot edit its own harness policy")
    else:
        require(task["work_package"] == "HARNESS-01" and actions <= {"harness_maintenance", "documentation", "public_web_research"},
                "Only explicit HARNESS-01 maintenance supported")
    for field in ["read_first", "allowed_files", "required_outputs", "acceptance", "checks"]:
        string_list(task[field], field)
    require({"harness", "structure"} <= set(task["checks"]) <= set(CHECKS), "Missing/unknown fixed check profile")
    require(type(task["max_changed_files"]) is int and 1 <= task["max_changed_files"] <= 30, "Invalid change budget (1..30)")
    require(len(task["allowed_files"]) <= task["max_changed_files"], "Allowlist exceeds change budget")
    for name in task["read_first"]:
        require(local(root, name).is_file(), f"Missing task input: {name}")
    for name in task["allowed_files"]:
        local(root, name)
        require(not protected(name), f"Protected path: {name}. {GATE} for product work; historical data needs separate protocol")
        require(name.startswith(("docs/", "contracts/", "scripts/", "ai-core/experiments/"))
                or name in {"AGENTS.md", "README.md"}, f"Unsupported write surface: {name}")
        if task["kind"] == "research":
            require(not (name in {"AGENTS.md", STATE, "scripts/agent_harness.py", "scripts/harness_journal.py"}
                         or name.startswith(("docs/harness/", "scripts/tests/"))), "Research cannot change harness controls")
    require(set(task["required_outputs"]) <= set(task["allowed_files"]), "Outputs outside allowlist")
    require(task["handoff"] in task["required_outputs"], "Handoff must be a required output")


def run_path(root: Path, run_id: str) -> Path:
    require(bool(re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9-]{2,63}", run_id)), "Invalid run ID")
    return local(root, f"tmp/agent-harness/{run_id}.json")


def begin(root: Path, task_path: str, run_id: str) -> dict:
    state = load_state(root)
    task = read_json(local(root, task_path))
    validate_task(root, task, state)
    before = inventory(root)
    for name in task["allowed_files"]:
        ignored = subprocess.run(["git", "-C", str(root), "check-ignore", "--no-index", "-q", "--", name], check=False, timeout=30)
        require(ignored.returncode == 1, f"Ignored/uncheckable output: {name}")
    record = {"schema_version": 1, "root": str(root.resolve()), "task_path": task_path, "task": task,
              "task_sha256": digest(local(root, task_path)), "state_sha256": digest(local(root, STATE)),
              "head": git(root, "rev-parse", "HEAD").decode().strip(), "files": before,
              "created_utc": datetime.now(timezone.utc).isoformat()}
    path = run_path(root, run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
    return {"result": "baseline_created", "run": run_id, "task": task["id"], "files_observed": len(before),
            "warning": "Baseline is local, mutable and unsigned. Git-ignored files/operations are not monitored."}


def check_run(root: Path, run_id: str, require_outputs: bool = True) -> dict:
    record = read_json(run_path(root, run_id))
    require(record.get("schema_version") == 1 and record.get("root") == str(root.resolve()), "Wrong run version/repository")
    require(digest(local(root, record["task_path"])) == record["task_sha256"], "Task changed after begin; do not rebaseline to hide drift")
    require(read_json(local(root, record["task_path"])) == record["task"], "Baseline task mismatch")
    require(digest(local(root, STATE)) == record["state_sha256"], "State changed during run; reconcile separately")
    require(git(root, "rev-parse", "HEAD").decode().strip() == record["head"], "HEAD changed; reconcile concurrent/committed work")
    task = record["task"]
    validate_task(root, task, load_state(root))
    after = inventory(root)
    delta = changes(record["files"], after)
    outside = sorted(set(delta) - set(task["allowed_files"]))
    require(not outside, f"Out-of-scope changes (possibly concurrent user edits; NEVER revert automatically): {outside}")
    require(len(delta) <= task["max_changed_files"], "Change budget exceeded")
    if require_outputs:
        for name in task["required_outputs"]:
            require(local(root, name).is_file() and local(root, name).stat().st_size > 0, f"Missing/empty output: {name}")
    return {"result": "scope_checked_NOT_acceptance", "task": task["id"], "changed_files": delta,
            "checks": task["checks"], "manual_acceptance": task["acceptance"],
            "handoff": task["handoff"], "astra": "pending_review_and_explicit_user_go"}


def verify(root: Path, run_id: str, require_local_data: bool) -> dict:
    report = check_run(root, run_id)
    outputs = []
    before = inventory(root)
    for name in report["checks"]:
        args = [sys.executable, "-B", *CHECKS[name]]
        if name == "structure" and require_local_data:
            args.append("--require-local-data")
        result = subprocess.run(args, cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        outputs.append({"check": name, "argv": args, "exit_code": result.returncode,
                        "stdout": result.stdout, "stderr": result.stderr})
    require(not changes(before, inventory(root)), "Verification modified observed files; inspect before proceeding")
    report = check_run(root, run_id)
    report.update({"verification": outputs, "verified_utc": datetime.now(timezone.utc).isoformat(),
                   "all_checks_passed": all(x["exit_code"] == 0 for x in outputs),
                   "evidence_scope": "local mechanical checks, NOT model reliability/product acceptance",
                   "require_local_data": require_local_data})
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    task_cmd = commands.add_parser("check-task")
    task_cmd.add_argument("--task", required=True)
    start = commands.add_parser("begin")
    start.add_argument("--task", required=True)
    start.add_argument("--run", required=True)
    for name in ["check", "verify"]:
        command = commands.add_parser(name)
        command.add_argument("--run", required=True)
        if name == "verify":
            command.add_argument("--require-local-data", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "status":
            report = load_state(ROOT)
        elif args.command == "check-task":
            state = load_state(ROOT)
            task = read_json(local(ROOT, args.task))
            validate_task(ROOT, task, state)
            report = {"result": "declared_task_valid_NOT_authorization", "task": task["id"]}
        elif args.command == "begin":
            report = begin(ROOT, args.task, args.run)
        elif args.command == "check":
            report = check_run(ROOT, args.run)
        else:
            report = verify(ROOT, args.run, args.require_local_data)
        print(json.dumps(report, ensure_ascii=True, indent=2))
        return 0 if report.get("all_checks_passed", True) else 1
    except (HarnessError, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"result": "BLOCKED", "reason": str(exc)}, ensure_ascii=True, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
