# Feature Workflow

1. **Planner:** translate request into scope, acceptance criteria, and a minimal change list.
2. **Coder:** implement only the approved plan.
3. **Tester:** run build and targeted tests; report exact commands and outcomes.
4. **Reviewer:** inspect diff, rules compliance, and user-visible impact.

Exit only when Tester and Reviewer pass; otherwise return the failure to Coder with evidence.
