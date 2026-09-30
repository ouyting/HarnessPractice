# Harness V1 Entry Workflow

Run locally:

```powershell
python tools/run-workflow.py --workflow feature
```

The entry point models the controlled loop below. In V1, each role produces a deterministic artifact and the Tester validates required harness files; it is intentionally a runnable scaffold rather than an autonomous coding system.

```text
Planner → Coder → Tester ──fail──> stop with evidence
                       │
                      pass
                       ↓
                    Reviewer → complete
```
