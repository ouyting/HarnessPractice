# Workflow Skill

For Jira-originated work, first use `.harness/workflows/jira-intake.md`. Create a local plan from the ticket details with:

```powershell
python tools/jira-intake.py --key PROJ-123 --type feature --summary "Short summary"
```

Then select the closest workflow in `.harness/workflows/` and run `python tools/run-workflow.py --workflow <name> --ticket PROJ-123`. A workflow moves through Planner → Coder → Tester → Reviewer and stops on a failed gate.

This V1 script does not connect to Jira. When the ticket must be read live or its status/comment must be updated, prompt the user to connect Jira MCP first.
