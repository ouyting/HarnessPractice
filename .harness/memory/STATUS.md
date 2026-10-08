# Status

- Harness V1 initialized.
- Current focus: adapt V1.1 command configuration to the first real business project.
- Last verified: 2026-10-05 HARN-11 build and 15 regression tests passed.
- Review: Codex self-review recorded for run 7a870bc3631e4a938e53d77ae183fcc0; state done. This is not an independent team review.
- Evidence: .harness/runs/HARN-11/latest.json.

## V2.1 adapters (2026-10-05)

- Added Jira MCP intake; AI now uses manual VS Code extension handoffs only.
- Earlier 43-test result covers the retired CLI implementation, not this revised scope.
- AI CLI source/tasks/config removed on user request; recoverable source backups in .harness/runs/migration-v21-extension-only.
- Actual extension development cycle and real Jira authentication not yet tested.
- Previous HARN-11 review is historical and does not cover V2.1 changes.
- HARN-21 requires explicit human review after the new verification run; no automatic approval.
- Scope: HarnessPractice only; HarnessDemo and uro-pro not updated in this iteration.
- Extension-only revision: Python syntax and 33 regression checks; see HARN-21/latest.json for final verification evidence. Approval remains pending.
- PowerShell wrappers: AST syntax checked; direct execution blocked by local execution policy. Use documented Python entry points.


## Jira Intake extension-only migration

- Intake now prepares a prompt for Codex/Claude existing MCP. No direct Jira requests, independent MCP config or automatic plan updates.
- Existing plans preserved; extension must preview JSON/Markdown changes and obtain confirmation.
- Earlier standalone MCP tests/config notes are historical. Local regression rerun required for this revised workflow.

- Final extension-intake validation: HarnessPractice 31 tests / HarnessDemo 34 tests passed, source checks passed, and all pre-migration plan hashes matched. Current agent shell was denied writing Demo runtime prompts (WinError 5); prompt generation logic passed in temporary-directory tests. Use VS Code under your own account; sandbox write failure is not an MCP connection failure.

## Jira and Confluence source collection (2026-10-08)

- Scope: HarnessPractice only. Existing plans, HarnessDemo and uro-pro were not modified.
- Intake handoffs now require Description, Purpose / Core Requirements, Design and associated Confluence bodies through existing extension MCP tools; no standalone connection added.
- Templates record original content, provenance and incomplete-read status. Field IDs are resolved by site metadata; linked-page traversal is bounded and deduplicated. Plan writes still require preview and explicit confirmation.
- Verification: Python source syntax and git diff whitespace checks passed; all 34 local regression tests passed, including source handoffs for both agents and offline no-overwrite coverage.
- Initial sandbox test run could not write temporary fixtures (WinError 5); rerun outside the sandbox exposed one outdated JSON-template fixture, which was updated before the final passing run.
- Live Jira/Confluence retrieval was not executed in this iteration. Generated handoffs are instructions, not an enforced MCP retrieval engine or proof of business acceptance. Human review remains pending.
