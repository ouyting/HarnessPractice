# Harness V1 — Agent Guide

This repository is a small, local-first agent harness. Work in short, verified loops:

1. Read `.harness/rules/` and the relevant workflow.
2. Record the plan before changing implementation files.
3. Run `tools/test.ps1` after changes.
4. Review the diff and update `.harness/memory/STATUS.md`.

Use the entry point below to demonstrate or verify the V1 loop:

```powershell
python tools/run-workflow.py
```

Never bypass the safety and forbidden rules. This MVP intentionally uses only Python's standard library and PowerShell.
