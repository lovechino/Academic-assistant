"""Local journal regressions on temporary synthetic data; no product/model calls."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing, redirect_stdout
import io
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness_journal as j


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="academic-journal-test-")
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name).resolve()
        j.h.git(self.root, "init", "-q", "--template=")
        (self.root / ".gitignore").write_text("/tmp/\n", encoding="utf-8")
        (self.root / "docs").mkdir()
        (self.root / "docs/evidence.md").write_text("Synthetic finding, unconfirmed.\n", encoding="utf-8")
        self.record = {"schema_version": 1, "root": str(self.root), "head": "a" * 40,
                       "task_sha256": "b" * 64, "state_sha256": "c" * 64,
                       "task_path": "docs/task.json",
                       "task": {"id": "SYNTHETIC-TASK", "allowed_files": ["docs/result.md"],
                                "required_outputs": ["docs/result.md"], "read_first": ["docs/evidence.md"],
                                "checks": ["harness", "structure"], "actions": ["documentation"],
                                "objective": "PRIVATE_NOT_TO_COPY", "request_basis": "SECRET_NOT_TO_COPY"}}
        self.baseline = j.h.run_path(self.root, "synthetic-run")
        self.baseline.parent.mkdir(parents=True)
        self.baseline.write_text(json.dumps(self.record), encoding="utf-8")
        j.initialize(self.root)

    def capture(self, event_id="capture-one", phase="check"):
        return j.capture(self.root, "synthetic-run", event_id, phase)

    def note(self, event_id="finding-one"):
        return j.finding(self.root, "synthetic-run", event_id, "design_gap", "P1", "docs/evidence.md", 1)

    def test_init_is_idempotent_and_report_empty(self):
        self.assertEqual(j.initialize(self.root)["result"], "already_initialized")
        self.assertEqual(j.report(self.root)["total_events"], 0)

    def test_read_missing_database_does_not_create(self):
        other = self.root / "other"
        other.mkdir()
        with self.assertRaises(j.h.HarnessError):
            j.report(other)
        self.assertFalse((other / j.DB).exists())

    def test_wrong_repository_and_version_are_not_reset(self):
        for key, value in (("root", "different-root"), ("version", "999")):
            with self.subTest(key=key), closing(sqlite3.connect(self.root / j.DB)) as con:
                con.execute("UPDATE metadata SET value=? WHERE key=?", (value, key))
                con.commit()
                with self.assertRaises(j.h.HarnessError):
                    j.initialize(self.root)
                con.execute("UPDATE metadata SET value=? WHERE key=?", (str(self.root) if key == "root" else j.VERSION, key))
                con.commit()

    def test_corrupt_database_not_overwritten(self):
        path = self.root / j.DB
        path.write_bytes(b"synthetic broken database")
        with self.assertRaises(sqlite3.DatabaseError):
            j.initialize(self.root)
        self.assertEqual(path.read_bytes(), b"synthetic broken database")

    def test_readonly_connection_cannot_write(self):
        with closing(j.connect(self.root)) as con, self.assertRaises(sqlite3.OperationalError):
            con.execute("DELETE FROM metadata")

    def test_snapshot_minimizes_prose(self):
        self.note()
        output = j.encoded(j.report(self.root, "synthetic-run"))
        self.assertNotIn("PRIVATE_NOT_TO_COPY", output)
        self.assertNotIn("SECRET_NOT_TO_COPY", output)
        self.assertIn("docs/result.md", output)

    def test_check_persists_only_safe_summary(self):
        with patch.object(j.h, "check_run", return_value={"changed_files": ["PRIVATE_PATH"], "secret": "RAW_BODY"}):
            result = self.capture()
        self.assertEqual(result["outcome"], "passed")
        output = j.encoded(j.report(self.root))
        self.assertNotIn("PRIVATE_PATH", output)
        self.assertNotIn("RAW_BODY", output)

    def test_verify_failure_preserves_exit_codes_not_raw_output(self):
        observed = {"all_checks_passed": False, "verification": [
            {"check": "harness", "exit_code": 1, "stdout": "SECRET", "stderr": "PASSWORD"}]}
        with patch.object(j.h, "verify", return_value=observed) as verify:
            result = j.capture(self.root, "synthetic-run", "verify-one", "verify", True)
        verify.assert_called_once_with(self.root, "synthetic-run", True)
        self.assertEqual(result["outcome"], "failed")
        self.assertEqual(j.exit_code(result), 1)
        self.assertNotIn("SECRET", j.encoded(result))
        self.assertNotIn("PASSWORD", j.encoded(result))

    def test_stale_scope_or_head_logged_without_exception_prose(self):
        for number, (message, expected) in enumerate((("Out-of-scope secret", "scope_drift"), ("HEAD changed secret", "head_drift"))):
            with patch.object(j.h, "check_run", side_effect=j.h.HarnessError(message)):
                result = self.capture(f"blocked-{number}")
            self.assertEqual(result["outcome"], "blocked")
            self.assertEqual(result["observation"]["code"], expected)
            self.assertNotIn("secret", j.encoded(result))

    def test_timeout_is_operational_not_product_bug(self):
        with patch.object(j.h, "verify", side_effect=subprocess.TimeoutExpired("private", 60)):
            result = self.capture(phase="verify")
        self.assertEqual(result["observation"]["code"], "check_timeout")

    def test_duplicate_event_never_reruns_checker(self):
        with patch.object(j.h, "check_run", return_value={}) as checker:
            first = self.capture()
            again = self.capture()
        checker.assert_called_once()
        self.assertEqual(first, again)

    def test_event_conflict_does_not_execute_second_command(self):
        with patch.object(j.h, "check_run", return_value={}):
            self.capture()
        with patch.object(j.h, "verify") as verify, self.assertRaises(j.h.HarnessError):
            self.capture(phase="verify")
        verify.assert_not_called()

    def test_concurrent_duplicate_only_one_checker_call(self):
        with patch.object(j.h, "check_run", return_value={}) as checker:
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: self.capture(), range(2)))
        self.assertEqual(checker.call_count, 1)
        self.assertTrue(all(item["outcome"] in {"pending", "passed"} for item in results))
        self.assertEqual(j.report(self.root)["total_events"], 1)

    def test_crash_leaves_pending_and_duplicate_does_not_retry(self):
        with patch.object(j.h, "check_run", side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
            self.capture()
        with patch.object(j.h, "check_run") as checker:
            result = self.capture()
        checker.assert_not_called()
        self.assertEqual(result["outcome"], "pending")
        self.assertEqual(j.exit_code(result), 1)

    def test_failed_db_finish_never_claims_success(self):
        with patch.object(j.h, "check_run", return_value={}), \
             patch.object(j, "finish", side_effect=sqlite3.OperationalError("locked")), \
             self.assertRaises(sqlite3.OperationalError):
            self.capture()
        self.assertEqual(j.event(self.root, "capture-one")["outcome"], "pending")

    def test_baseline_mutation_rejected_no_rebaseline(self):
        self.note()
        self.record["head"] = "d" * 40
        self.baseline.write_text(json.dumps(self.record), encoding="utf-8")
        with self.assertRaisesRegex(j.h.HarnessError, "baseline changed"):
            self.note("finding-two")
        self.assertEqual(j.report(self.root)["total_events"], 1)

    def test_terminal_cannot_be_overwritten(self):
        self.note()
        with self.assertRaises(j.h.HarnessError):
            j.finish(self.root, "finding-one", "passed", {})
        self.assertEqual(j.event(self.root, "finding-one")["outcome"], "reported")

    def test_report_and_suggest_do_not_mutate_database(self):
        self.note()
        before = j.h.digest(self.root / j.DB)
        result = j.suggest(self.root, "synthetic-run")
        self.assertEqual(before, j.h.digest(self.root / j.DB))
        self.assertFalse(result["mutations_performed"])
        self.assertEqual(result["proposals"][0]["requires_review"], True)

    def test_finding_is_reported_not_automatically_verified(self):
        first = self.note()
        self.assertEqual(first["outcome"], "reported")
        self.assertEqual(first, self.note())
        self.assertIn("NOT_confirmed", first["observation"]["authority"])

    def test_finding_path_and_fields_are_restricted(self):
        for evidence, line in (("../private.md", 1), ("docs/../private.md", 1), (".env", 1), ("docs/evidence.md", 999)):
            with self.subTest(evidence=evidence), self.assertRaises(j.h.HarnessError):
                j.finding(self.root, "synthetic-run", "finding-bad", "design_gap", "P1", evidence, line)
        with self.assertRaises(j.h.HarnessError):
            j.finding(self.root, "synthetic-run", "finding-bad", "approve", "P1", "docs/evidence.md", 1)

    def test_ids_and_limits_cannot_inject_sql_or_paths(self):
        for value in ("../evil", "x'; DROP TABLE events;--", "x\nGO"):
            with self.assertRaises(j.h.HarnessError):
                j.event(self.root, value)
        for limit in (0, 101, True):
            with self.assertRaises(j.h.HarnessError):
                j.report(self.root, limit=limit)

    def test_no_arbitrary_command_phase(self):
        with patch.object(j.h, "check_run") as checker, self.assertRaises(j.h.HarnessError):
            self.capture(phase="deploy")
        checker.assert_not_called()

    def test_tree_changes_during_capture_block_observation(self):
        def mutate(*args):
            (self.root / "docs/unexpected.md").write_text("synthetic mutation", encoding="utf-8")
            return {}
        with patch.object(j.h, "check_run", side_effect=mutate):
            result = self.capture()
        self.assertEqual(result["outcome"], "blocked")
        self.assertEqual(result["observation"]["code"], "verification_side_effect")

    def test_check_summary_numeric_projection_and_unknown(self):
        result = j.check_summary({"check": "structure", "exit_code": 0, "stdout": json.dumps({
            "checks": 9, "passed": 9, "skipped": ["PRIVATE_PATH"], "failures": [], "secret": "PRIVATE"})})
        self.assertEqual(result["checks"], 9)
        self.assertEqual(result["skipped_count"], 1)
        self.assertNotIn("PRIVATE", j.encoded(result))
        self.assertIsNone(result["pdf_source_hashes_verified"])
        self.assertEqual(j.check_summary({"check": "structure", "exit_code": 1, "stdout": "bad"})["summary"], "unavailable")
        self.assertEqual(j.check_summary({"check": "harness", "exit_code": 0, "stderr": "Ran 57 tests in 2.0s"})["tests_run"], 57)

    def test_locked_database_reports_error_without_event(self):
        with closing(j.connect(self.root, write=True)) as con:
            con.execute("BEGIN IMMEDIATE")
            with self.assertRaises(sqlite3.OperationalError):
                self.note()
            con.rollback()
        self.assertEqual(j.report(self.root)["total_events"], 0)

    def test_linked_db_rejected(self):
        original = Path.is_symlink
        target = self.root / j.DB
        with patch.object(Path, "is_symlink", lambda path: path == target or original(path)):
            with self.assertRaises(j.h.HarnessError):
                j.report(self.root)

    def test_cli_failure_is_nonzero_and_has_no_raw_exception(self):
        with patch.object(sys, "argv", ["journal", "report"]), patch.object(j.h, "ROOT", self.root), \
             patch.object(j, "report", side_effect=sqlite3.OperationalError("SECRET")), redirect_stdout(io.StringIO()) as stream:
            code = j.main()
        self.assertEqual(code, 1)
        self.assertNotIn("SECRET", stream.getvalue())

    def move(self, event_id, parent, state, **extra):
        with patch.object(j.h, "check_run", return_value={}):
            return j.transition(self.root, "synthetic-run", "finding-one", event_id, parent, state,
                                "worker-dev", "docs/evidence.md", 1, **extra)

    def proposed(self):
        self.note()
        self.move("reproduce-one", "finding-one", "reproduced")
        self.move("proposal-one", "reproduce-one", "fix_proposed")

    def verified_observation(self, event_id="verify-life", passed=True):
        result = {"all_checks_passed": passed, "verification": [
            {"check": "harness", "exit_code": 0 if passed else 1, "stderr": "Ran 1 test in 0.1s"},
            {"check": "structure", "exit_code": 0, "stdout": "{}"}]}
        with patch.object(j.h, "verify", return_value=result):
            return self.capture(event_id, "verify")

    def test_lifecycle_full_sequence_preserves_original_and_hides_closed_suggestion(self):
        self.proposed()
        original = j.event(self.root, "finding-one")
        self.verified_observation()
        self.move("verified-one", "proposal-one", "verified_local", verification="verify-life")
        self.assertEqual(j.history(self.root, "finding-one")["state"], "verified_local")
        self.assertTrue(any("review evidence" in x["proposal"] for x in j.suggest(self.root)["proposals"]))
        self.move("closed-one", "verified-one", "reviewed_closed", verification="verify-life",
                  reviewer="reviewer-independent", review_evidence="docs/evidence.md", review_line=1)
        state = j.history(self.root, "finding-one")
        self.assertEqual(state["state"], "reviewed_closed")
        self.assertEqual(len(state["history"]), 5)
        self.assertEqual(j.event(self.root, "finding-one"), original)
        self.assertEqual(j.suggest(self.root)["proposals"], [])
        self.assertIn("NOT_authenticated", state["authority"])
        with self.assertRaises(j.h.HarnessError):
            self.move("reopen-invalid", "closed-one", "reproduced")

    def test_lifecycle_cannot_skip_or_infer_closure_from_pass(self):
        self.note()
        self.verified_observation()
        for target in ("fix_proposed", "verified_local", "reviewed_closed"):
            options = {"verification": "verify-life"} if target != "fix_proposed" else {}
            if target == "reviewed_closed":
                options.update(reviewer="reviewer-independent", review_evidence="docs/evidence.md", review_line=1)
            with self.subTest(target=target), self.assertRaises(j.h.HarnessError):
                self.move("skip-attempt", "finding-one", target, **options)
        self.assertEqual(j.history(self.root, "finding-one")["state"], "reported")

    def test_lifecycle_duplicate_conflict_and_stale_predecessor(self):
        self.note()
        first = self.move("reproduce-one", "finding-one", "reproduced")
        self.assertEqual(first, self.move("reproduce-one", "finding-one", "reproduced"))
        for event_id, parent, state in (("reproduce-one", "reproduce-one", "fix_proposed"),
                                        ("stale-event", "finding-one", "fix_proposed")):
            with self.assertRaises(j.h.HarnessError):
                self.move(event_id, parent, state)
        self.assertEqual(len(j.history(self.root, "finding-one")["history"]), 2)

    def test_lifecycle_concurrent_predecessor_has_one_winner(self):
        self.note()
        def attempt(key):
            try:
                j.transition(self.root, "synthetic-run", "finding-one", key, "finding-one", "reproduced",
                             "worker-dev", "docs/evidence.md", 1)
                return "recorded"
            except j.h.HarnessError:
                return "stale"
        with patch.object(j.h, "check_run", return_value={}):
            with ThreadPoolExecutor(max_workers=2) as pool:
                outcomes = list(pool.map(attempt, ("concurrent-one", "concurrent-two")))
        self.assertEqual(sorted(outcomes), ["recorded", "stale"])
        self.assertEqual(len(j.history(self.root, "finding-one")["history"]), 2)

    def test_lifecycle_verify_requires_post_proposal_pass_not_scope_check(self):
        self.note()
        self.verified_observation("verify-before")
        self.move("reproduce-one", "finding-one", "reproduced")
        self.move("proposal-one", "reproduce-one", "fix_proposed")
        with patch.object(j.h, "check_run", return_value={}):
            self.capture("scope-only")
        self.verified_observation("verify-failed", passed=False)
        for evidence in ("verify-before", "scope-only", "verify-failed"):
            with self.subTest(evidence=evidence), self.assertRaises(j.h.HarnessError):
                self.move("verified-invalid", "proposal-one", "verified_local", verification=evidence)
        self.assertEqual(j.history(self.root, "finding-one")["state"], "fix_proposed")

    def test_lifecycle_newer_failed_verify_cannot_be_hidden_by_old_pass(self):
        self.proposed()
        self.verified_observation("verify-old-pass")
        self.verified_observation("verify-new-fail", passed=False)
        with self.assertRaises(j.h.HarnessError):
            self.move("verified-hidden-fail", "proposal-one", "verified_local", verification="verify-old-pass")
        self.verified_observation("verify-current-pass")
        self.move("verified-current", "proposal-one", "verified_local", verification="verify-current-pass")

    def test_lifecycle_stale_tree_checker_and_wrong_run_rejected(self):
        self.proposed()
        self.verified_observation()
        with patch.object(j, "checker_fingerprint", return_value={"fake": "changed"}), self.assertRaises(j.h.HarnessError):
            self.move("verified-stale", "proposal-one", "verified_local", verification="verify-life")
        with closing(j.connect(self.root, write=True)) as con:
            scope = j.snapshot(self.root, "synthetic-run")
            con.execute("INSERT INTO runs VALUES ('another-run',?,?)", (scope["baseline_hash"], j.encoded(scope)))
            con.execute("UPDATE events SET run_id='another-run' WHERE event_id='verify-life'")
        with self.assertRaises(j.h.HarnessError):
            self.move("verified-wrong-run", "proposal-one", "verified_local", verification="verify-life")
        with closing(j.connect(self.root, write=True)) as con:
            con.execute("UPDATE events SET run_id='synthetic-run' WHERE event_id='verify-life'")
        (self.root / "docs/evidence.md").write_text("Changed synthetic evidence.\n", encoding="utf-8")
        with self.assertRaises(j.h.HarnessError):
            self.move("verified-tree-stale", "proposal-one", "verified_local", verification="verify-life")

    def test_lifecycle_review_fields_and_same_worker_label_rejected(self):
        self.proposed()
        self.verified_observation()
        self.move("verified-one", "proposal-one", "verified_local", verification="verify-life")
        with self.assertRaises(j.h.HarnessError):
            self.move("closed-missing", "verified-one", "reviewed_closed", verification="verify-life")
        with self.assertRaises(j.h.HarnessError):
            self.move("closed-self", "verified-one", "reviewed_closed", verification="verify-life",
                      reviewer="WORKER-DEV", review_evidence="docs/evidence.md", review_line=1)
        with self.assertRaises(j.h.HarnessError):
            self.move("closed-no-line", "verified-one", "reviewed_closed", verification="verify-life",
                      reviewer="reviewer-independent", review_evidence="docs/evidence.md", review_line=999)
        self.assertEqual(j.history(self.root, "finding-one")["state"], "verified_local")

    def test_lifecycle_error_rolls_back_and_legacy_db_needs_no_migration(self):
        self.note()
        before = j.h.digest(self.root / j.DB)
        with patch.object(j, "now", side_effect=RuntimeError("simulated crash")), self.assertRaises(RuntimeError):
            self.move("crashed-transition", "finding-one", "reproduced")
        self.assertEqual(j.h.digest(self.root / j.DB), before)
        self.assertEqual(j.initialize(self.root)["result"], "already_initialized")
        self.assertEqual(j.history(self.root, "finding-one")["state"], "reported")
        with closing(j.connect(self.root)) as con:
            self.assertEqual(con.execute("SELECT value FROM metadata WHERE key='version'").fetchone()[0], "1")

    def test_lifecycle_history_readonly_and_scan_limit_fails_explicitly(self):
        self.proposed()
        before = j.h.digest(self.root / j.DB)
        self.assertEqual(j.history(self.root, "finding-one")["head_event"], "proposal-one")
        self.assertEqual(j.report(self.root)["finding_states"][0]["state"], "fix_proposed")
        self.assertEqual(j.h.digest(self.root / j.DB), before)
        with patch.object(j, "TRANSITION_SCAN_LIMIT", 1), self.assertRaises(j.h.HarnessError):
            j.history(self.root, "finding-one")


if __name__ == "__main__":
    unittest.main()
