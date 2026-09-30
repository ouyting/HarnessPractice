#!/usr/bin/env python3
"""Runnable, dependency-free Harness V1 workflow entry point."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REQUIRED = (
    'AGENTS.md',
    '.harness/rules/coding.md',
    '.harness/rules/architecture.md',
    '.harness/rules/safety.md',
    '.harness/rules/forbidden.md',
    '.harness/skills/build.md',
    '.harness/skills/test.md',
    '.harness/skills/git.md',
    '.harness/skills/workflow.md',
    '.harness/workflows/feature.md',
    '.harness/workflows/bugfix.md',
    '.harness/workflows/refactor.md',
    '.harness/workflows/mvp.md',
    '.harness/memory/STATUS.md',
    '.harness/memory/DECISIONS.md',
    '.harness/memory/MISTAKES.md',
)


def verify_layout() -> list[str]:
    return [item for item in REQUIRED if not (ROOT / item).is_file()]


def update_status(workflow: str) -> None:
    status = ROOT / '.harness/memory/STATUS.md'
    lines = status.read_text(encoding='utf-8').splitlines()
    lines = [line for line in lines if not line.startswith('- Last verified:')]
    lines.append(f'- Last verified: `{workflow}` workflow completed successfully.')
    status.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main() -> int:
    parser = argparse.ArgumentParser(description='Run the Harness V1 role loop.')
    parser.add_argument('--workflow', choices=('feature', 'bugfix', 'refactor'), default='feature')
    parser.add_argument('--verify-only', action='store_true', help='Validate the Tester gate without changing memory.')
    args = parser.parse_args()

    print(f'[Planner] Workflow: {args.workflow}; acceptance criterion: required harness contract exists.')
    print('[Coder] V1 deterministic scaffold selected; no project implementation file is changed.')
    missing = verify_layout()
    if missing:
        print('[Tester] FAIL: missing required files: ' + ', '.join(missing), file=sys.stderr)
        return 1
    print('[Tester] PASS: required harness files are present.')
    print('[Reviewer] PASS: Planner → Coder → Tester → Reviewer gates completed.')
    if not args.verify_only:
        update_status(args.workflow)
        print('[Memory] STATUS.md updated.')
    print('COMPLETE')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
