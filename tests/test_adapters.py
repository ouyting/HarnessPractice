"""Adapters tested against actual local subprocesses and a loopback HTTP server."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1] / 'tools'
sys.path.insert(0, str(TOOLS))
from harness import read_json, write_json
from jira_mcp import fetch, normalize, render
from mcp_client import MCPClient


class AdapterTests(unittest.TestCase):
    def test_extension_only_repository_contract(self):
        root = TOOLS.parent
        self.assertFalse((TOOLS / 'ai-execute.py').exists())
        self.assertFalse((TOOLS / 'ai_adapter.py').exists())
        tasks = read_json(root / '.vscode/tasks.json')
        serialized = json.dumps(tasks)
        self.assertNotIn('ai-execute.py', serialized)
        self.assertNotIn('AI CLI', serialized)
        self.assertNotIn('ai', read_json(root / '.harness/integrations.example.json'))
        inputs = {item['id'] for item in tasks['inputs']}
        import re
        for task in tasks['tasks']:
            for name in re.findall(r'\$\{input:([^}]+)\}', json.dumps(task)):
                self.assertIn(name, inputs)
            self.assertTrue((root / task['args'][0]).is_file())

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plan = {'key': 'DEMO-1', 'type': 'feature', 'summary': 'Test', 'description': 'Test behavior',
                     'acceptance_criteria': ['Works'], 'scope': ['One file'], 'implementation_steps': ['Implement']}
        write_json(self.root / 'plans/DEMO-1.json', self.plan)
        write_json(self.root / '.harness/config.json', {
            'build': {'command': ['{python}', '-c', 'pass'], 'timeout_seconds': 10},
            'test': {'command': ['{python}', '-c', 'pass'], 'timeout_seconds': 10}})
        self.mcp = {'transport': 'stdio', 'command': [sys.executable, str(Path(__file__).parent / 'fixtures/mcp_server.py')],
                    'ticket_tool': 'get_issue', 'ticket_arguments': {'key': '{key}'}, 'acceptance_fields': ['customfield_1']}

    def test_stdio_real_roundtrip(self):
        plan = fetch(self.mcp, self.root, 'DEMO-2')
        self.assertEqual(plan['description'], 'Real fixture description')
        self.assertEqual(plan['acceptance_criteria'], ['Works offline'])
        self.assertEqual(plan['type'], 'feature')

    def test_tool_discovery_and_unknown_tool(self):
        self.assertEqual(fetch(self.mcp, self.root, None, list_only=True)[0]['name'], 'get_issue')
        with self.assertRaises(ValueError):
            fetch(dict(self.mcp, ticket_tool='delete_issue'), self.root, 'DEMO-2')

    def test_wrong_key_and_error_rejected(self):
        with self.assertRaises(ValueError):
            normalize({'structuredContent': {'key': 'OTHER-1'}}, 'DEMO-1', {})
        with self.assertRaises(ValueError):
            normalize({'isError': True}, 'DEMO-1', {})

    def test_text_json_and_unknown_type(self):
        issue = {'key': 'DEMO-1', 'fields': {'summary': 'S', 'issuetype': {'name': 'Custom'}}}
        result = {'content': [{'type': 'text', 'text': json.dumps(issue)}]}
        with self.assertRaises(ValueError):
            normalize(result, 'DEMO-1', {})
        self.assertEqual(normalize(result, 'DEMO-1', {}, 'bugfix')['type'], 'bugfix')

    def test_adf_multiple_paragraphs(self):
        value = {'type': 'doc', 'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': s}]} for s in ('a', 'b')]}
        self.assertEqual(render(value), 'a\nb')

    def test_http_json_and_sse_session(self):
        requests = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                requests.append((body, dict(self.headers)))
                if body['method'].startswith('notifications/'):
                    self.send_response(202)
                    self.end_headers()
                    return
                result = {'protocolVersion': '2025-06-18'} if body['method'] == 'initialize' else {'tools': []}
                data = json.dumps({'jsonrpc': '2.0', 'id': body['id'], 'result': result})
                self.send_response(200)
                self.send_header('Mcp-Session-Id', 'fixture-session')
                self.send_header('Content-Type', 'application/json' if body['method'] == 'initialize' else 'text/event-stream')
                self.end_headers()
                self.wfile.write((data if body['method'] == 'initialize' else 'data: ' + data + '\n\n').encode())
        server = HTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with MCPClient({'transport': 'http', 'url': 'http://127.0.0.1:' + str(server.server_port)}, self.root) as client:
                self.assertEqual(client.list_tools(), [])
            self.assertEqual(requests[-1][1]['Mcp-Session-Id'], 'fixture-session')
            headers = {k.lower(): v for k, v in requests[-1][1].items()}
            self.assertEqual(headers['mcp-protocol-version'], '2025-06-18')
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_insecure_endpoint_and_missing_token(self):
        with self.assertRaises(ValueError):
            with MCPClient({'transport': 'http', 'url': 'http://example.com/mcp'}, self.root):
                pass
        with patch.dict('os.environ', {}, clear=True), self.assertRaises(ValueError):
            with MCPClient({'transport': 'http', 'url': 'http://localhost:1', 'token_env': 'MISSING'}, self.root):
                pass

    def test_intake_live_saves_description_and_preserves_existing(self):
        spec = importlib.util.spec_from_file_location('intake_adapter', TOOLS / 'jira-intake.py')
        intake = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(intake)
        intake.ROOT, intake.TEMPLATE = self.root, self.root / 'template.md'
        intake.TEMPLATE.write_text('# {{KEY}} {{SUMMARY}}', encoding='utf-8')
        config = self.root / 'integrations.json'
        write_json(config, {'jira_mcp': self.mcp})
        with patch.object(sys, 'argv', ['intake', '--key', 'DEMO-2', '--from-jira', '--config', str(config)]):
            self.assertEqual(intake.main(), 0)
            self.assertEqual(read_json(self.root / 'plans/DEMO-2.json')['description'], 'Real fixture description')
            md = next((self.root / 'plans').glob('demo-2*.md'))
            self.assertIn('Real fixture description', md.read_text())
            original = md.read_bytes()
            self.assertEqual(intake.main(), 1)
            self.assertEqual(md.read_bytes(), original)


    def test_mcp_timeout_and_malformed_output(self):
        for code in ('import time; time.sleep(2)', 'print("not-json", flush=True)'):
            with self.assertRaises(ValueError):
                with MCPClient({'transport': 'stdio', 'command': [sys.executable, '-c', code], 'timeout_seconds': .1}, self.root):
                    pass

    def test_http_auth_failure_does_not_echo_secret(self):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b'sensitive-server-error')
        server = HTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with self.assertRaises(ValueError) as caught:
                with MCPClient({'transport': 'http', 'url': 'http://127.0.0.1:' + str(server.server_port)}, self.root):
                    pass
            self.assertIn('401', str(caught.exception))
            self.assertNotIn('sensitive', str(caught.exception))
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
