"""Offline protocol fixture, not a Jira connection."""
import json
import sys

for line in sys.stdin:
    request = json.loads(line)
    if 'id' not in request:
        continue
    method = request['method']
    if method == 'initialize':
        result = {'protocolVersion': '2025-06-18', 'capabilities': {'tools': {}}}
    elif method == 'tools/list':
        result = {'tools': [{'name': 'get_issue', 'annotations': {'readOnlyHint': True}}]}
    else:
        key = request['params']['arguments']['key']
        result = {'structuredContent': {'key': key, 'fields': {'summary': 'MCP imported ticket',
                  'issuetype': {'name': 'Story'}, 'description': {'type': 'doc', 'content': [
                      {'type': 'paragraph', 'content': [{'type': 'text', 'text': 'Real fixture description'}]}]},
                  'customfield_1': 'Works offline'}}}
    print(json.dumps({'jsonrpc': '2.0', 'id': request['id'], 'result': result}), flush=True)
