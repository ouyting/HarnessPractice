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

Jira is optional in V1. Use the local intake script to record ticket details; connect Jira MCP only when real-time ticket retrieval or a Jira write-back is required.

V1.1 requires a complete plans/<KEY>.json and project build/test commands in .harness/config.json. Passing checks enters awaiting_review; only an explicit review tied to the latest verified snapshot enters done. See docs/V1.1.md. Never represent a printed role name as completed implementation or review.

For VS Code extensions, use tasks in .vscode/tasks.json and tools/editor-workflow.py to prepare stage handoffs. See docs/V2-VSCode.md. Prompt generation is not AI execution. Retain explicit verification and user-recorded review; extension login does not authorize the Harness script to control extension sessions.

V2.1 is VS Code extension collaboration only: generate stage prompts for the user to submit to Codex or Claude Code extensions. No AI CLI adapter or model API calls. Keep opt-in Jira MCP retrieval (`jira-intake.py --from-jira`); read docs/V2.1-Adapters.md. Never auto-approve review or copy extension credentials. Existing plans are never replaced by intake.
