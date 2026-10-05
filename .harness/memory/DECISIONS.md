# Decisions

| Date | Decision | Rationale |
|---|---|---|
| 2026-09-30 | Use Python standard library + PowerShell | Runs on Windows without framework setup or network dependencies. |
| 2026-09-30 | Make verification layout-based in V1 | The harness has no target application yet; it can still verify its own contract. |
| 2026-09-30 | Make Jira Intake local-first | Ticket metadata becomes a versioned local plan; live Jira access and write-back remain opt-in through MCP. |

| 2026-10-05 | V1.1 uses explicit plans, command evidence and snapshot-bound review | Remove unconditional role PASS; separate successful verification from completed review. |
| 2026-10-05 | V2.1 uses VS Code extension collaboration only; remove AI CLI adapters | User requests existing extension accounts, manual handoffs and local verification. Jira MCP stays opt-in. |


| 2026-10-05 | Retire standalone Jira MCP intake; use extension's existing MCP via confirmed handoffs | User requests no second MCP configuration; preserve source plans and require diff preview before updates. |
