"""Deterministic harness tests in disposable synthetic repositories; no pilot data."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("agent_harness", Path(__file__).resolve().parents[1] / "agent_harness.py")
h = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(h)


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="academic-harness-test-")
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name).resolve()
        h.git(self.root, "init", "-q", "--template=")
        h.git(self.root, "-c", "user.name=Harness Test", "-c", "user.email=harness@example.invalid",
              "-c", "core.hooksPath=.disabled-hooks", "-c", "commit.gpgsign=false",
              "commit", "-q", "--allow-empty", "-m", "Synthetic baseline")
        self.write(".gitignore", "/tmp/\n/ignored/\n")
        self.write("AGENTS.md", "Synthetic test rules")
        self.write("docs/plan.md", "Synthetic plan: WP-03 then WP-02 then WP-04; ASTRA pending")
        self.write("docs/last.md", "Synthetic prior handoff")
        self.state = {
            "schema_version": 1, "stage": "pre_product_research", "plan": "docs/plan.md",
            "plan_sha256": h.digest(self.root / "docs/plan.md"), "next_work_package": "WP-03",
            "astra": {"status": "pending_review_and_explicit_user_go"}, "read_first": ["AGENTS.md"],
            "evidence_limits": ["Synthetic is not human acceptance"],
            "sequence": ["WP-03", "WP-02", "WP-04", "ASTRA-01", "P6"], "last_handoff": "docs/last.md",
        }
        self.task = {
            "schema_version": 1, "id": "WP03-TEST", "work_package": "WP-03", "kind": "research",
            "objective": "Create a synthetic evaluation inventory document",
            "request_basis": "Synthetic user request in a deterministic unit test only",
            "actions": ["documentation"], "read_first": ["AGENTS.md"],
            "allowed_files": ["docs/result.md", "docs/handoff.md"],
            "required_outputs": ["docs/result.md", "docs/handoff.md"],
            "acceptance": ["Manual check that denominators are explicit"],
            "checks": ["harness", "structure"], "max_changed_files": 2, "handoff": "docs/handoff.md",
        }
        self.save(h.STATE, self.state)
        self.save("docs/task.json", self.task)

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def save(self, name, value):
        self.write(name, json.dumps(value))

    def start(self):
        return h.begin(self.root, "docs/task.json", "test-run")

    def complete_outputs(self):
        self.write("docs/result.md", "Synthetic inventory; dev only")
        self.write("docs/handoff.md", "Synthetic handoff; pending review")

    def assert_task_blocked(self, task):
        with self.assertRaises(h.HarnessError):
            h.validate_task(self.root, task, self.state)

    def test_valid_research_task(self):
        h.validate_task(self.root, self.task, h.load_state(self.root))

    def test_product_actions_trigger_gate(self):
        for action in sorted(h.PRODUCT_ACTIONS):
            with self.subTest(action=action):
                task = dict(self.task, actions=[action])
                with self.assertRaisesRegex(h.HarnessError, "ASTRA-01"):
                    h.validate_task(self.root, task, self.state)

    def test_unsupported_external_or_mutating_actions(self):
        for action in ["external_ocr", "model_run", "publish", "train", "deploy", "git_push", "approve", "gold_promotion"]:
            with self.subTest(action=action):
                self.assert_task_blocked(dict(self.task, actions=[action]))

    def test_next_package_drift(self):
        for wp in ["WP-02", "WP-04", "E0.10", "P6"]:
            with self.subTest(wp=wp):
                self.assert_task_blocked(dict(self.task, work_package=wp))

    def test_harness_maintenance_requires_separate_kind(self):
        self.assert_task_blocked(dict(self.task, actions=["harness_maintenance"]))

    def test_unknown_fields_cannot_supply_approval_or_commands(self):
        for key in ["approved", "astra_go", "shell_command"]:
            with self.subTest(key=key):
                self.assert_task_blocked(dict(self.task, **{key: True}))

    def test_state_cannot_unlock_product(self):
        for delta in [{"stage": "product"}, {"astra": {"status": "GO"}}, {"approved": True}]:
            with self.subTest(delta=delta):
                self.save(h.STATE, dict(self.state, **delta))
                with self.assertRaises(h.HarnessError):
                    h.load_state(self.root)

    def test_state_rejects_unknown_next_or_sequence(self):
        for delta in [{"next_work_package": "P6"}, {"sequence": ["WP-03", "P6"]}]:
            self.save(h.STATE, dict(self.state, **delta))
            with self.assertRaises(h.HarnessError):
                h.load_state(self.root)

    def test_stale_plan_is_blocked(self):
        self.write("docs/plan.md", "Roadmap edited after snapshot")
        with self.assertRaisesRegex(h.HarnessError, "Roadmap changed"):
            h.load_state(self.root)

    def test_missing_read_reference(self):
        self.assert_task_blocked(dict(self.task, read_first=["docs/missing.md"]))

    def test_canonical_paths_reject_traversal_and_globs(self):
        for name in ["../secret", "E:/secret", "/secret", "docs/../secret", "docs\\x", "docs/*", ".git/config", "docs//x", "docs/a:stream"]:
            with self.subTest(name=name):
                with self.assertRaises(h.HarnessError):
                    h.local(self.root, name)

    def test_product_and_historical_paths_are_protected(self):
        for name in ["ai-core/src/academic_ai/a.py", "backend/src/a.py", "frontend/src/a.ts", "infra/a.yml",
                     "data/processed/snapshot.json", "pyproject.toml", "backend/package.json", ".env",
                     "ai-core/experiments/retrieval-r4/run.py", "FRONTEND/SRC/a.ts"]:
            with self.subTest(name=name):
                self.assertTrue(h.protected(name))
                self.assert_task_blocked(dict(self.task, allowed_files=[name]))

    def test_research_cannot_edit_controls(self):
        for name in [h.STATE, "AGENTS.md", "scripts/agent_harness.py", "scripts/harness_journal.py", "docs/harness/README.md", "scripts/tests/test_agent_harness.py"]:
            with self.subTest(name=name):
                self.assert_task_blocked(dict(self.task, allowed_files=[name]))

    def test_only_fixed_check_profiles(self):
        for checks in [["structure"], ["harness", "structure", "python -c evil"], ["harness", "harness", "structure"]]:
            self.assert_task_blocked(dict(self.task, checks=checks))

    def test_invalid_budgets_or_outputs(self):
        for delta in [{"max_changed_files": True}, {"max_changed_files": 0}, {"max_changed_files": 31},
                      {"max_changed_files": 1}, {"required_outputs": ["docs/outside.md"]}, {"acceptance": []},
                      {"handoff": "docs/not-required.md"}, {"schema_version": True}]:
            with self.subTest(delta=delta):
                self.assert_task_blocked(dict(self.task, **delta))

    def test_duplicate_json_keys_rejected(self):
        self.write("docs/duplicate.json", '{"approved": false, "approved": true}')
        with self.assertRaisesRegex(h.HarnessError, "Duplicate"):
            h.read_json(self.root / "docs/duplicate.json")

    def test_baseline_preserves_dirty_tracked_and_untracked(self):
        self.write("docs/tracked.md", "original")
        h.git(self.root, "add", "docs/tracked.md")
        self.write("docs/tracked.md", "preexisting user edit")
        self.write("docs/untracked.md", "preexisting untracked")
        self.start()
        self.complete_outputs()
        report = h.check_run(self.root, "test-run")
        self.assertEqual(report["changed_files"], ["docs/handoff.md", "docs/result.md"])
        self.assertIn("NOT_acceptance", report["result"])
        self.assertEqual(report["astra"], "pending_review_and_explicit_user_go")

    def test_new_untracked_scope_escape(self):
        self.start()
        self.complete_outputs()
        self.write("docs/unplanned.md", "new")
        with self.assertRaisesRegex(h.HarnessError, "Out-of-scope"):
            h.check_run(self.root, "test-run")

    def test_preexisting_untracked_modification_detected(self):
        self.write("docs/user.md", "user work")
        self.start()
        self.write("docs/user.md", "changed")
        with self.assertRaisesRegex(h.HarnessError, "Out-of-scope"):
            h.check_run(self.root, "test-run", require_outputs=False)
        self.assertEqual((self.root / "docs/user.md").read_text(), "changed")

    def test_deletion_and_rename_detected(self):
        self.assertEqual(h.changes({"docs/old.md": "hash"}, {"docs/new.md": "hash"}), ["docs/new.md", "docs/old.md"])
        self.assertEqual(h.changes({"docs/a.md": "hash"}, {"docs/a.md": None}), ["docs/a.md"])
        self.assertEqual(h.changes({"docs/a.md": None}, {}), [])

    def test_task_cannot_widen_after_begin(self):
        self.start()
        task = copy.deepcopy(self.task)
        task["allowed_files"].append("docs/extra.md")
        self.save("docs/task.json", task)
        with self.assertRaisesRegex(h.HarnessError, "Task changed"):
            h.check_run(self.root, "test-run")

    def test_state_cannot_change_during_run(self):
        self.start()
        self.save(h.STATE, dict(self.state, next_work_package="WP-02"))
        with self.assertRaisesRegex(h.HarnessError, "State changed"):
            h.check_run(self.root, "test-run")

    def test_head_change_detected(self):
        self.start()
        h.git(self.root, "-c", "user.name=Harness Test", "-c", "user.email=harness@example.invalid",
              "-c", "core.hooksPath=.disabled-hooks", "-c", "commit.gpgsign=false",
              "commit", "-q", "--allow-empty", "-m", "Synthetic concurrent commit")
        with self.assertRaisesRegex(h.HarnessError, "HEAD changed"):
            h.check_run(self.root, "test-run")

    def test_all_existing_experiment_profiles_are_read_only(self):
        for folder in sorted(h.HISTORICAL_EXPERIMENTS):
            with self.subTest(folder=folder):
                self.assertTrue(h.protected(f"ai-core/experiments/{folder}/run.py"))
        self.assertFalse(h.protected("ai-core/experiments/new-bounded-scorer-v0.1/test_scorer.py"))

    def test_internal_symlink_is_rejected(self):
        # Mock metadata to exercise the link branch even on Windows without symlink privilege.
        original = Path.is_symlink
        target = self.root / "docs/result.md"
        with patch.object(Path, "is_symlink", lambda p: p == target or original(p)):
            with self.assertRaisesRegex(h.HarnessError, "Linked/reparse"):
                h.local(self.root, "docs/result.md")

    def test_missing_and_empty_outputs_fail(self):
        self.start()
        with self.assertRaisesRegex(h.HarnessError, "Missing/empty output"):
            h.check_run(self.root, "test-run")
        self.complete_outputs()
        self.write("docs/result.md", "")
        with self.assertRaisesRegex(h.HarnessError, "Missing/empty output"):
            h.check_run(self.root, "test-run")

    def test_begin_does_not_overwrite_baseline(self):
        self.start()
        before = h.digest(h.run_path(self.root, "test-run"))
        with self.assertRaises(FileExistsError):
            self.start()
        self.assertEqual(before, h.digest(h.run_path(self.root, "test-run")))

    def test_ignored_output_not_silently_accepted(self):
        self.write(".gitignore", "/tmp/\n/docs/result.md\n")
        with self.assertRaisesRegex(h.HarnessError, "Ignored/uncheckable"):
            self.start()

    def test_run_id_cannot_escape_scratch(self):
        for name in ["../bad", "/bad", "x.json", "a/b", "E:bad"]:
            with self.assertRaises(h.HarnessError):
                h.run_path(self.root, name)

    def test_failed_verification_not_reported_as_pass(self):
        self.start()
        self.complete_outputs()
        failed = subprocess.CompletedProcess([], 1, "", "synthetic failure")
        # Do not execute another unittest runner recursively inside a unit test.
        with patch.object(h, "check_run", return_value={"checks": ["harness"]}), \
             patch.object(h, "inventory", return_value={}), \
             patch.object(h.subprocess, "run", return_value=failed):
            report = h.verify(self.root, "test-run", False)
        self.assertFalse(report["all_checks_passed"])
        self.assertEqual(report["verification"][0]["exit_code"], 1)

    def test_verification_detects_file_side_effect(self):
        with patch.object(h, "check_run", return_value={"checks": []}), \
             patch.object(h, "inventory", side_effect=[{}, {"docs/mutated.md": "hash"}]):
            with self.assertRaisesRegex(h.HarnessError, "Verification modified"):
                h.verify(self.root, "test-run", False)


if __name__ == "__main__":
    unittest.main()
