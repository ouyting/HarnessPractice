# Feature Workflow

0. **Intake:** if the source is Jira, complete `jira-intake.md` and create a local ticket plan.
1. **Planner:** translate the ticket plan into scope, acceptance criteria, and a minimal change list.
2. **Coder:** implement only the approved plan.
3. **Tester:** run build and targeted tests; report exact commands and outcomes.
4. **Reviewer:** inspect diff, rules compliance, and user-visible impact.

Exit only when Tester and Reviewer pass; otherwise return the failure to Coder with evidence.

V1.1 completion: build/test evidence must pass, then reviewer records notes with the latest run_id, --diff-checked and --criteria-checked. Only an unchanged verified snapshot can enter done.
