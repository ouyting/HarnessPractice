# Harness V2.1 — Agent Guide

This repository is a small, local-first agent harness. Work in short, verified loops:

1. Start with `.harness/workflows/jira-intake.md` when work originates from Jira.
2. Read `.harness/rules/` and the relevant feature, bugfix, or refactor workflow.
3. Record the plan before changing implementation files.
4. Run `tools/test.ps1` after changes.
5. Review the diff and update `.harness/memory/STATUS.md`.

Use the entry point below to demonstrate or verify the V1 loop:

```powershell
python tools/run-workflow.py --ticket PROJ-123
```

Never bypass the safety and forbidden rules. This MVP intentionally uses only Python's standard library and PowerShell.

Jira is optional. Use the intake handoff to request read-only retrieval through the selected extension's existing MCP. No Jira write-back is authorized by intake.

V1.1 requires a complete plans/<KEY>.json and project build/test commands in .harness/config.json. Passing checks enters awaiting_review; only an explicit review tied to the latest verified snapshot enters done. See docs/V1.1.md. Never represent a printed role name as completed implementation or review.

For VS Code extensions, use tasks in .vscode/tasks.json and tools/editor-workflow.py to prepare stage handoffs. See docs/V2-VSCode.md. Prompt generation is not AI execution. Retain explicit verification and user-recorded review; extension login does not authorize the Harness script to control extension sessions.

V2.1 uses extension-only handoffs for Jira Intake and AI stages. jira-intake.py --key KEY --agent codex/claude creates a prompt, not a network request or plan update. The extension uses its existing MCP, previews both plan files and waits for user confirmation before updating them. No independent MCP client or integrations.json; no AI CLI/API. Never copy credentials or modify Jira. See docs/V2.1-Adapters.md.

Jira Intake must collect Description, Purpose / Core Requirements, Design, and directly associated Confluence content via the extension's existing read-only MCP tools. Resolve field IDs by site metadata, retain original bodies and provenance, and report missing/blocked/partial reads rather than inventing completeness. See the intake workflow for bounded link traversal and source_materials records.
