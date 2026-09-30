# Bugfix Workflow

0. **Intake:** if the source is Jira, complete `jira-intake.md` and create a local ticket plan.
1. **Planner:** capture the ticket's reproduction, expected behavior, and suspected boundary.
2. **Coder:** make the smallest corrective change.
3. **Tester:** prove the reproduction is fixed and run regression checks.
4. **Reviewer:** check cause, regression coverage, and scope.

Stop if reproduction is unavailable; record the blocker instead of guessing.
