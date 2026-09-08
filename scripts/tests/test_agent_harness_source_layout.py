"""Synthetic pre-product placement checks; no product code or source PDF access."""
import importlib.util
from pathlib import Path
import stat
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location("source_layout", Path(__file__).resolve().parents[1] / "verify_source_layout.py")
layout = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(layout)


class PlacementTests(unittest.TestCase):
    def report(self, *extra):
        return layout.check_paths([*layout.SCAFFOLD_FILES, *extra])

    def test_current_markers_and_design_reference_pass(self):
        self.assertEqual(self.report(*layout.ROOT_FILES, *layout.REFERENCE_FILES)["status"], "passed")

    def test_each_missing_marker_fails(self):
        for marker in layout.SCAFFOLD_FILES:
            with self.subTest(marker=marker):
                result = layout.check_paths([p for p in layout.SCAFFOLD_FILES if p != marker])
                self.assertIn(f"Missing source marker: {marker}", result["failures"])

    def test_competing_roots_fail(self):
        for folder in ["src", "app", "apps", "services", "packages", "shared", "common", "utils", "ai_core"]:
            with self.subTest(folder=folder):
                self.assertEqual(self.report(f"{folder}/qa.py")["status"], "failed")

    def test_even_correct_runtime_addresses_wait_for_go(self):
        for name in ["ai-core/src/academic_ai/application/academic_qa.py",
                     "ai-core/src/academic_ai/retrieval/packing.py", "ai-core/src/academic_ai/public.py",
                     "backend/src/academic_backend/application/academic_qa.py",
                     "frontend/src/features/academic-qa/index.ts", "backend/tests/unit/test_qa.py"]:
            with self.subTest(name=name):
                self.assertEqual(self.report(name)["status"], "failed")

    def test_nested_or_disguised_component_paths_fail(self):
        for name in ["backend/services/qa.py", "ai-core/src/academic_ai/agents/qa.py",
                     "frontend/src/lib/agents/README.md", "frontend/public/private.pdf",
                     "backend/src/academic_backend/domain/authorization.py.md"]:
            with self.subTest(name=name):
                self.assertEqual(self.report(name)["status"], "failed")

    def test_packages_prompts_and_deployment_are_not_skeleton(self):
        for name in ["package.json", "backend/pyproject.toml", "frontend/package.json",
                     "infra/docker-compose.yml", "ai-core/prompts/qa.txt",
                     "backend/migrations/0001.sql", "tests/test_cross_component.py"]:
            with self.subTest(name=name):
                self.assertEqual(self.report(name)["status"], "failed")

    def test_research_and_tooling_paths_remain_placement_only(self):
        for name in ["docs/example.md", "contracts/example.md", "data/README.md",
                     "ai-core/experiments/approved-fixture/test_fixture.py", "scripts/tool.py"]:
            with self.subTest(name=name):
                self.assertEqual(self.report(name)["status"], "passed")

    def test_bad_paths_rejected(self):
        for name in ["../src.py", "/tmp/src.py", "C:/src.py", "docs\\qa.py", "docs//qa.py",
                     "docs/../qa.py", "docs/./qa.py", "docs/a\n.py", "docs/*.py"]:
            with self.subTest(name=name):
                self.assertEqual(self.report(name)["status"], "failed")

    def test_case_collisions_and_wrong_component_case_fail(self):
        self.assertEqual(self.report("Backend/README.md")["status"], "failed")
        report = self.report("docs/A.md", "docs/a.md")
        self.assertTrue(any("Case-colliding" in f for f in report["failures"]))

    def test_duplicate_inventory_entries_are_harmless(self):
        self.assertEqual(self.report(layout.SCAFFOLD_FILES[0])["status"], "passed")

    def test_missing_git_is_not_pass(self):
        with patch.object(layout.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, b"", b"")):
            with self.assertRaises(ValueError):
                layout.check_layout(Path("."))

    def test_timeout_is_not_a_success(self):
        with patch.object(layout.subprocess, "run", side_effect=subprocess.TimeoutExpired("git", 30)):
            with self.assertRaises(subprocess.TimeoutExpired):
                layout.check_layout(Path("."))


class GitInventoryTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="academic-placement-test-")
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name).resolve()
        self.git("init", "-q", "--template=")
        for name in layout.SCAFFOLD_FILES:
            self.write(name, "Synthetic marker; no product behavior")
        self.write(".gitignore", "/ignored/\n")

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True, timeout=30)

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_untracked_source_is_seen_without_executing_or_writing(self):
        self.write("src/oops.py", "raise RuntimeError('Must never execute')")
        before = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        report = layout.check_layout(self.root)
        after = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(report["status"], "failed")
        self.assertTrue(any("src/oops.py" in f for f in report["failures"]))

    def test_ignored_files_are_explicitly_outside_coverage(self):
        self.write("ignored/qa.py", "Not inspected or authorized by a layout pass")
        self.assertEqual(layout.check_layout(self.root)["status"], "passed")

    def test_tracked_deleted_marker_is_missing(self):
        name = layout.SCAFFOLD_FILES[0]
        self.git("add", "--", name)
        (self.root / name).unlink()
        self.assertIn(f"Missing source marker: {name}", layout.check_layout(self.root)["failures"])

    def test_link_and_reparse_paths_fail_before_descending(self):
        # Simulated filesystem metadata; does not require Windows symlink privileges.
        original = Path.lstat
        target = self.root / "backend"
        for mode, attributes in [(stat.S_IFLNK, 0), (stat.S_IFDIR, stat.FILE_ATTRIBUTE_REPARSE_POINT)]:
            with self.subTest(mode=mode):
                def inspect(path, *args, **kwargs):
                    if path == target:
                        return SimpleNamespace(st_mode=mode, st_file_attributes=attributes)
                    if target in path.parents:
                        self.fail("Checker descended through a linked source directory")
                    return original(path, *args, **kwargs)

                with patch.object(Path, "lstat", autospec=True, side_effect=inspect):
                    report = layout.check_layout(self.root)
                self.assertEqual(report["status"], "failed")
                self.assertTrue(any("Linked/reparse" in f for f in report["failures"]))


if __name__ == "__main__":
    unittest.main()
