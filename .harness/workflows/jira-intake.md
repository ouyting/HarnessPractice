# Jira Intake Workflow (Local-First)

Use this workflow whenever a feature or bug starts from a Jira ticket.

1. Capture the ticket key, title, issue type, description, acceptance criteria, priority, links, and reproduction details (for bugs).
2. Classify it as `feature` or `bugfix`. If ambiguous, record the uncertainty and stop before implementation.
3. Generate a local plan from the template:

```powershell
python tools/jira-intake.py --key PROJ-123 --type feature --summary "Short summary"
```

4. Review the generated plan, fill in acceptance criteria and the verification command.
5. Continue with `feature.md` or `bugfix.md`:

```powershell
python tools/run-workflow.py --workflow feature --ticket PROJ-123
```

## Connection boundary

This workflow does **not** read Jira itself. Ask the user to connect Jira MCP only if a live ticket must be retrieved, searched, transitioned, commented on, or otherwise updated. Treat Jira write-back as a separate, user-authorized action.

V1.1: Intake also generates `plans/<KEY>.json`. Fill description, acceptance_criteria, scope and implementation_steps; bugs also need reproduction_steps and expected_behavior. Markdown alone cannot pass the readiness gate.
