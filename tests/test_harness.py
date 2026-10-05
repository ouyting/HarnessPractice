"""Behavioral regression tests for real gates and stale review prevention."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("harness", Path(__file__).resolve().parents[1] / "tools/harness.py")
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plan = {"key": "DEMO-1", "type": "feature", "summary": "Example",
                     "description": "Verify an implementation", "acceptance_criteria": ["Works"],
                     "scope": ["One function"], "implementation_steps": ["Implement and test"]}
        harness.write_json(self.root / "plans/DEMO-1.json", self.plan)
        self.config = {"build": {"command": ["{python}", "-c", "print('build')"], "timeout_seconds": 10},
                       "test": {"command": ["{python}", "-c", "print('test')"], "timeout_seconds": 10}}
        harness.write_json(self.root / ".harness/config.json", self.config)

    def save_config(self):
        harness.write_json(self.root / ".harness/config.json", self.config)

    def test_success_waits_for_review(self):
        record = harness.run(self.root, "DEMO-1")
        self.assertEqual(record["state"], "awaiting_review")
        self.assertEqual(len(record["checks"]), 2)
        done = harness.review(self.root, "DEMO-1", record["run_id"], "reviewer", "approve",
                              "Diff and acceptance criteria verified", True, True)
        self.assertEqual(done["state"], "done")

    def test_failed_build_stops_before_test(self):
        self.config["build"]["command"] = ["{python}", "-c", "raise SystemExit(7)"]
        self.save_config()
        record = harness.run(self.root, "DEMO-1")
        self.assertEqual(record["state"], "blocked")
        self.assertEqual(len(record["checks"]), 1)
        self.assertEqual(record["checks"][0]["exit_code"], 7)

    def test_failed_test_then_fixed_can_run_again(self):
        self.config["test"]["command"] = ["{python}", "-c", "raise SystemExit(3)"]
        self.save_config()
        failed = harness.run(self.root, "DEMO-1")
        self.assertEqual(failed["state"], "blocked")
        with self.assertRaises(ValueError):
            harness.review(self.root, "DEMO-1", failed["run_id"], "reviewer", "approve", "Checked", True, True)
        self.config["test"]["command"] = ["{python}", "-c", "print('fixed')"]
        self.save_config()
        self.assertEqual(harness.run(self.root, "DEMO-1")["state"], "awaiting_review")

    def test_missing_acceptance_blocks(self):
        self.plan["acceptance_criteria"] = []
        harness.write_json(self.root / "plans/DEMO-1.json", self.plan)
        with self.assertRaises(ValueError):
            harness.run(self.root, "DEMO-1")

    def test_wrong_workflow_blocks(self):
        with self.assertRaises(ValueError):
            harness.run(self.root, "DEMO-1", "bugfix")

    def test_bug_requires_reproduction(self):
        self.plan["type"] = "bugfix"
        harness.write_json(self.root / "plans/DEMO-1.json", self.plan)
        with self.assertRaises(ValueError):
            harness.run(self.root, "DEMO-1")
        self.plan.update(reproduction_steps=["Run the failing case"], expected_behavior="Pass")
        harness.write_json(self.root / "plans/DEMO-1.json", self.plan)
        self.assertEqual(harness.run(self.root, "DEMO-1")["state"], "awaiting_review")

    def test_stale_code_cannot_be_approved(self):
        record = harness.run(self.root, "DEMO-1")
        (self.root / "code.py").write_text("changed = True")
        with self.assertRaises(ValueError):
            harness.review(self.root, "DEMO-1", record["run_id"], "reviewer", "approve", "Checked", True, True)

    def test_approval_requires_checklist(self):
        record = harness.run(self.root, "DEMO-1")
        with self.assertRaises(ValueError):
            harness.review(self.root, "DEMO-1", record["run_id"], "reviewer", "approve", "Checked", False, True)

    def test_review_rejection_blocks(self):
        record = harness.run(self.root, "DEMO-1")
        self.assertEqual(harness.review(self.root, "DEMO-1", record["run_id"], "reviewer",
                                        "reject", "Missing edge case", False, False)["state"], "blocked")

    def test_old_run_cannot_be_reviewed(self):
        first = harness.run(self.root, "DEMO-1")
        harness.run(self.root, "DEMO-1")
        with self.assertRaises(ValueError):
            harness.review(self.root, "DEMO-1", first["run_id"], "reviewer", "approve", "Checked", True, True)

    def test_timeout_is_blocked(self):
        self.config["test"].update(command=["{python}", "-c", "import time; time.sleep(2)"],
                                   timeout_seconds=0.05)
        self.save_config()
        record = harness.run(self.root, "DEMO-1")
        self.assertEqual(record["state"], "blocked")
        self.assertEqual(record["checks"][-1]["error"], "timeout")

    def test_verify_only_saves_nothing(self):
        harness.run(self.root, "DEMO-1", persist=False)
        self.assertFalse((self.root / ".harness/runs").exists())

    def test_missing_executable_is_blocked(self):
        self.config["build"]["command"] = ["nonexistent-harness-command-12345"]
        self.save_config()
        record = harness.run(self.root, "DEMO-1")
        self.assertEqual(record["state"], "blocked")
        self.assertIn("error", record["checks"][0])

    def test_changes_during_verification_block_review(self):
        self.config["test"]["command"] = [
            "{python}", "-c", "from pathlib import Path; Path('changed.py').write_text('x=1')"
        ]
        self.save_config()
        self.assertEqual(harness.run(self.root, "DEMO-1")["state"], "blocked")

    def test_intake_creates_structured_plan_and_refuses_overwrite(self):
        intake_spec = importlib.util.spec_from_file_location(
            "intake", Path(__file__).resolve().parents[1] / "tools/jira-intake.py")
        intake = importlib.util.module_from_spec(intake_spec)
        intake_spec.loader.exec_module(intake)
        intake.ROOT = self.root
        intake.TEMPLATE = self.root / "template.md"
        intake.TEMPLATE.write_text("# {{KEY}}: {{SUMMARY}} ({{TYPE}})", encoding="utf-8")
        from unittest.mock import patch
        with patch.object(sys, "argv", ["jira-intake", "--key", "DEMO-2", "--type",
                                       "feature", "--summary", "Test intake"]):
            self.assertEqual(intake.main(), 0)
            path = self.root / "plans/DEMO-2.json"
            original = path.read_bytes()
            self.assertEqual(json.loads(original)["key"], "DEMO-2")
            self.assertEqual(intake.main(), 1)
            self.assertEqual(path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
