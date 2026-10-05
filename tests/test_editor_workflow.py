"""Extension handoff gates; no external account or model required."""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
spec = importlib.util.spec_from_file_location("editor_workflow", TOOLS / "editor-workflow.py")
editor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(editor)
import harness


class EditorWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plan = {"key": "EDIT-1", "type": "feature", "summary": "A feature",
                     "description": "Task", "acceptance_criteria": ["Works"],
                     "scope": ["Small"], "implementation_steps": ["Implement"]}
        harness.write_json(self.root / "plans/EDIT-1.json", self.plan)
        harness.write_json(self.root / ".harness/config.json", {
            stage: {"command": ["{python}", "-c", "print('ok')"], "timeout_seconds": 10}
            for stage in ("build", "test")
        })

    def test_planner_can_fill_incomplete_plan(self):
        self.plan["acceptance_criteria"] = []
        harness.write_json(self.root / "plans/EDIT-1.json", self.plan)
        self.assertTrue(editor.prepare(self.root, "EDIT-1", "planner").is_file())
        with self.assertRaises(ValueError):
            editor.prepare(self.root, "EDIT-1", "coder")

    def test_handoff_does_not_claim_execution(self):
        prompt = editor.prepare(self.root, "EDIT-1", "coder", "claude")
        self.assertIn("Implement the validated plan", prompt.read_text(encoding="utf-8"))
        self.assertFalse((self.root / ".harness/runs/EDIT-1/latest.json").exists())

    def test_reviewer_requires_passing_unchanged_run(self):
        run = harness.run(self.root, "EDIT-1")
        self.assertTrue(editor.prepare(self.root, "EDIT-1", "reviewer").is_file())
        self.assertEqual(harness.read_json(self.root / ".harness/runs/EDIT-1/latest.json")["run_id"], run["run_id"])
        (self.root / "code.py").write_text("changed=True")
        with self.assertRaises(ValueError):
            editor.prepare(self.root, "EDIT-1", "reviewer")

    def test_failed_checks_do_not_get_reviewer_prompt(self):
        config = harness.read_json(self.root / ".harness/config.json")
        config["test"]["command"] = ["{python}", "-c", "raise SystemExit(1)"]
        harness.write_json(self.root / ".harness/config.json", config)
        harness.run(self.root, "EDIT-1")
        with self.assertRaises(ValueError):
            editor.prepare(self.root, "EDIT-1", "reviewer")

    def test_repair_limit_and_evidence(self):
        config = harness.read_json(self.root / ".harness/config.json")
        config["test"]["command"] = ["{python}", "-c", "raise SystemExit(1)"]
        harness.write_json(self.root / ".harness/config.json", config)
        harness.run(self.root, "EDIT-1")
        for _ in range(2):
            prompt = editor.prepare(self.root, "EDIT-1", "repair")
            self.assertIn('"exit_code": 1', prompt.read_text(encoding="utf-8"))
        with self.assertRaises(ValueError):
            editor.prepare(self.root, "EDIT-1", "repair")

    def test_recorded_approval_uses_v11_gate(self):
        harness.run(self.root, "EDIT-1")
        editor.prepare(self.root, "EDIT-1", "reviewer")
        with self.assertRaises(ValueError):
            editor.record_review(self.root, "EDIT-1", "approve", "Human", "Read findings", False, True)
        done = editor.record_review(self.root, "EDIT-1", "approve", "Human", "Reviewed diff and criteria", True, True)
        self.assertEqual(done["state"], "done")

    def test_old_reviewer_prompt_cannot_approve_new_run(self):
        harness.run(self.root, "EDIT-1")
        editor.prepare(self.root, "EDIT-1", "reviewer")
        harness.run(self.root, "EDIT-1")
        with self.assertRaises(ValueError):
            editor.record_review(self.root, "EDIT-1", "approve", "Human", "Checked", True, True)


if __name__ == "__main__":
    unittest.main()
