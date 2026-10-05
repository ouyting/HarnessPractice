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

Offline intake does **not** read Jira. V2.1 supports explicit live retrieval with
`python tools/jira-intake.py --key PROJ-123 --from-jira` after configuring `.harness/integrations.json`.
See `docs/V2.1-Adapters.md`; missing configuration/authentication prompts for connection.
Live intake is read-only and refuses to overwrite existing local plans. Jira write-back is not implemented.

V1.1: Intake also generates `plans/<KEY>.json`. Fill description, acceptance_criteria, scope and implementation_steps; bugs also need reproduction_steps and expected_behavior. Markdown alone cannot pass the readiness gate.
