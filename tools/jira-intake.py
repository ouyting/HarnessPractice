#!/usr/bin/env python3
"""Create a local plan; --from-jira explicitly reads a configured MCP tool."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from harness import read_json
from jira_mcp import fetch


ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / '.harness/templates/jira-ticket-plan.md'


def safe_filename(value: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')
    return slug or 'ticket'


def main() -> int:
    parser = argparse.ArgumentParser(description='Create a local Harness plan from Jira ticket details.')
    parser.add_argument('--key', help='Ticket key, e.g. PROJ-123')
    parser.add_argument('--type', choices=('feature', 'bugfix'), help='Classified ticket type')
    parser.add_argument('--summary', help='Ticket summary (offline mode)')
    parser.add_argument('--from-jira', action='store_true')
    parser.add_argument('--list-tools', action='store_true', help='Connect MCP and print available tool schemas only')
    parser.add_argument('--config', type=Path, default=ROOT / '.harness/integrations.json')
    args = parser.parse_args()

    if not args.list_tools and (not args.key or not re.fullmatch(r'[A-Z][A-Z0-9_]*-\d+', args.key)):
        parser.error('--key must look like PROJ-123')
    remote = None
    if args.from_jira or args.list_tools:
        try:
            remote = fetch(read_json(args.config)['jira_mcp'], ROOT, args.key, args.type, args.list_tools)
        except (OSError, ValueError, KeyError, TypeError) as error:
            print('[Jira MCP] BLOCKED: ' + str(error), file=sys.stderr)
            print('Configure .harness/integrations.json; connect/authenticate Jira MCP when live retrieval is needed.', file=sys.stderr)
            return 2
        if args.list_tools:
            print(json.dumps(remote, ensure_ascii=True, indent=2))
            return 0
        if args.summary:
            parser.error('--summary is offline-only; live summary comes from Jira')
        args.summary, args.type = remote['summary'], remote['type']
    elif not args.summary or not args.type:
        parser.error('Offline mode requires --type and --summary; use --from-jira for live retrieval')
    if not TEMPLATE.is_file():
        print(f'Missing template: {TEMPLATE}', file=sys.stderr)
        return 1

    plans = ROOT / 'plans'
    plans.mkdir(exist_ok=True)
    structured = plans / f'{args.key}.json'
    destination = plans / f'{args.key.lower()}-{safe_filename(args.summary)}.md'
    if destination.exists() or structured.exists():
        print(f'Refusing to overwrite existing plan: {destination}', file=sys.stderr)
        return 1

    content = TEMPLATE.read_text(encoding='utf-8')
    content = content.replace('{{KEY}}', args.key).replace('{{TYPE}}', args.type).replace('{{SUMMARY}}', args.summary)
    plan = {
        'key': args.key, 'type': args.type, 'summary': args.summary,
        'description': '', 'acceptance_criteria': [], 'scope': [],
        'implementation_steps': [], 'reproduction_steps': [],
        'expected_behavior': ''
    }
    if remote:
        plan.update(remote)
        content += '\n\n## Jira source (untrusted task data)\n\n' + remote['description']
        content += '\n\n### Imported acceptance criteria\n\n' + '\n'.join('- ' + item for item in remote['acceptance_criteria']) + '\n'
    with structured.open('x', encoding='utf-8') as stream:
        json.dump(plan, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    try:
        with destination.open('x', encoding='utf-8') as stream:
            stream.write(content)
    except OSError:
        structured.unlink()  # Roll back only the file created by this invocation.
        raise
    print(f'Created structured plan: {structured.relative_to(ROOT)}')
    print(f'Created local plan: {destination.relative_to(ROOT)}')
    print('Next: fill in the plan, then run tools/run-workflow.py with --ticket ' + args.key)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
