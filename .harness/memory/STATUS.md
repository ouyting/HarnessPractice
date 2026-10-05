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
