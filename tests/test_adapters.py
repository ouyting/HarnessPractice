"""Extension Jira handoffs are local-only and never overwrite plans."""
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('extension_intake', ROOT / 'tools/jira-intake.py')
intake = importlib.util.module_from_spec(spec)
spec.loader.exec_module(intake)


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'plans').mkdir()

    def test_existing_plans_preserved(self):
        a = self.root / 'plans/UP-1525.json'
        b = self.root / 'plans/up-1525-user-title.md'
        a.write_text('{"key":"UP-1525","user_notes":"keep"}', encoding='utf-8')
        b.write_text('User authored notes', encoding='utf-8')
        before = [a.read_bytes(), b.read_bytes()]
        prompt = intake.prepare(self.root, 'UP-1525', 'codex')
        self.assertEqual(before, [a.read_bytes(), b.read_bytes()])
        text = prompt.read_text(encoding='utf-8')
        self.assertIn('explicit user confirmation', text)
        self.assertIn('re-read both files', text)
        manifest = json.loads(prompt.with_name('manifest.json').read_text())
        self.assertEqual(len(manifest['existing_plan_hashes']), 2)
        self.assertEqual(manifest['state'], 'handoff_prepared')

    def test_missing_plan_is_not_created(self):
        prompt = intake.prepare(self.root, 'DEMO-9', 'claude')
        self.assertTrue(prompt.exists())
        self.assertEqual(list((self.root / 'plans').iterdir()), [])
        self.assertIn('THIS VS Code extension', prompt.read_text())
        self.assertFalse((self.root / '.harness/integrations.json').exists())

    def test_unique_prompts_do_not_overwrite(self):
        self.assertNotEqual(intake.prepare(self.root, 'DEMO-1'), intake.prepare(self.root, 'DEMO-1'))

    def test_invalid_key_or_agent(self):
        for key, agent in [('../escape', 'codex'), ('DEMO-1', 'unknown')]:
            with self.assertRaises(ValueError):
                intake.prepare(self.root, key, agent)

    def test_multiple_markdown_blocks(self):
        for name in ('demo-1-a.md', 'demo-1-b.md'):
            (self.root / 'plans' / name).write_text('notes')
        with self.assertRaises(ValueError):
            intake.prepare(self.root, 'DEMO-1')

    def test_legacy_flag_only_prepares_handoff(self):
        with patch.object(intake, 'ROOT', self.root), patch.object(sys, 'argv', ['intake','--key','DEMO-1','--from-jira']):
            self.assertEqual(intake.main(), 0)
        self.assertEqual(list((self.root / 'plans').iterdir()), [])

    def test_default_agent_and_explicit_claude(self):
        for agent in ([], ['--agent','claude']):
            with patch.object(intake, 'ROOT', self.root), patch.object(sys, 'argv', ['intake','--key','DEMO-1']+agent):
                self.assertEqual(intake.main(), 0)

    def test_old_config_argument_rejected(self):
        with patch.object(sys, 'argv', ['intake','--key','DEMO-1','--config','secret.json']):
            with self.assertRaises(SystemExit):
                intake.main()

    def test_repository_contract(self):
        for retired in ('jira_mcp.py','mcp_client.py','ai-execute.py','ai_adapter.py'):
            self.assertFalse((ROOT/'tools'/retired).exists())
        tasks = json.loads((ROOT/'.vscode/tasks.json').read_text())
        inputs = {i['id'] for i in tasks['inputs']}
        for task in tasks['tasks']:
            for name in re.findall(r'\$\{input:([^}]+)\}', json.dumps(task)):
                self.assertIn(name, inputs)
            arg = task['args'][0]
            self.assertTrue((ROOT/(arg['value'] if isinstance(arg,dict) else arg)).is_file())
        jira = next(t for t in tasks['tasks'] if t['label']=='Harness V2.1: Jira Intake (Extension MCP)')
        args = [a['value'] if isinstance(a,dict) else a for a in jira['args']]
        self.assertIn('--agent', args)
        self.assertNotIn('--from-jira', args)
        self.assertNotIn('input:python', json.dumps(tasks))
        source = (ROOT/'tools/jira-intake.py').read_text()
        self.assertNotIn('from jira_mcp', source)
        self.assertNotIn('subprocess', source)


if __name__ == '__main__':
    unittest.main()
