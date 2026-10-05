#!/usr/bin/env python3
"""Create a local, versionable plan from Jira ticket metadata without any network access."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / '.harness/templates/jira-ticket-plan.md'


def safe_filename(value: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')
    return slug or 'ticket'


def main() -> int:
    parser = argparse.ArgumentParser(description='Create a local Harness plan from Jira ticket details.')
    parser.add_argument('--key', required=True, help='Ticket key, e.g. PROJ-123')
    parser.add_argument('--type', required=True, choices=('feature', 'bugfix'), help='Classified ticket type')
    parser.add_argument('--summary', required=True, help='Ticket summary')
    args = parser.parse_args()

    if not re.fullmatch(r'[A-Z][A-Z0-9_]*-\d+', args.key):
        parser.error('--key must look like PROJ-123')
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
    destination.write_text(content, encoding='utf-8')
    plan = {
        'key': args.key, 'type': args.type, 'summary': args.summary,
        'description': '', 'acceptance_criteria': [], 'scope': [],
        'implementation_steps': [], 'reproduction_steps': [],
        'expected_behavior': ''
    }
    with structured.open('x', encoding='utf-8') as stream:
        json.dump(plan, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(f'Created structured plan: {structured.relative_to(ROOT)}')
    print(f'Created local plan: {destination.relative_to(ROOT)}')
    print('Next: fill in the plan, then run tools/run-workflow.py with --ticket ' + args.key)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
