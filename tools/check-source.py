"""Check tracked Harness source syntax without producing bytecode."""
import ast
from pathlib import Path

root = Path(__file__).resolve().parent.parent
required = ["AGENTS.md", ".harness/config.json", "tools/harness.py",
            "tools/run-workflow.py", "tools/jira-intake.py", "tests/test_harness.py",
            ".harness/templates/jira-ticket-plan.md", ".harness/templates/jira-ticket.json"]
required += [".harness/rules/" + name + ".md"
             for name in ("coding", "architecture", "safety", "forbidden")]
required += [".harness/skills/" + name + ".md"
             for name in ("build", "test", "git", "workflow")]
required += [".harness/workflows/" + name + ".md"
             for name in ("feature", "bugfix", "refactor", "jira-intake", "mvp")]
required += [".harness/memory/" + name + ".md"
             for name in ("STATUS", "DECISIONS", "MISTAKES")]
required += ["tools/mcp_client.py", "tools/jira_mcp.py", "tools/editor-workflow.py", ".vscode/tasks.json",
             "tests/test_adapters.py", ".harness/integrations.example.json", "docs/V2.1-Adapters.md"]
missing = [name for name in required if not (root / name).is_file()]
if missing:
    raise SystemExit("Missing Harness files: " + ", ".join(missing))
for folder in ("tools", "tests"):
    for path in (root / folder).rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
print("Python source syntax passed.")
