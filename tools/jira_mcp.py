"""Read a single configured Jira ticket tool and normalize its result."""
import json
from mcp_client import MCPClient


def render(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(render(item) for item in value)
    if isinstance(value, dict):
        if value.get("type") == "text":
            return value.get("text", "")
        if value.get("type") == "hardBreak":
            return "\n"
        separator = "\n" if value.get("type") in ("doc", "bulletList", "orderedList", "listItem") else ""
        content = separator.join(render(item) for item in value.get("content", []))
        return content
    raise ValueError("Unsupported Jira rich text value.")


def normalize(result, key, config, kind=None):
    if result.get("isError"):
        raise ValueError("Jira tool reported an error; no plan was written.")
    issue = result.get("structuredContent")
    if issue is None:
        for block in result.get("content", []):
            if block.get("type") == "text":
                try:
                    issue = json.loads(block["text"])
                    break
                except ValueError:
                    continue
    if isinstance(issue, dict) and "issue" in issue:
        issue = issue["issue"]
    if not isinstance(issue, dict) or issue.get("key") != key:
        raise ValueError("Jira response must contain the exact requested issue key.")
    fields = issue.get("fields", issue)
    summary = fields.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError("Jira response missing summary.")
    issue_type = fields.get("issuetype", {})
    name = issue_type.get("name", "") if isinstance(issue_type, dict) else str(issue_type)
    kind = kind or {"bug": "bugfix", "feature": "feature", "story": "feature", "task": "feature"}.get(name.lower())
    if kind not in ("feature", "bugfix"):
        raise ValueError("Unknown Jira issue type; specify --type feature or bugfix.")
    criteria = []
    for field in config.get("acceptance_fields", []):
        content = render(fields.get(field)).strip()
        if content:
            criteria.append(content)
    return {"key": key, "type": kind, "summary": summary, "description": render(fields.get("description")).strip(),
            "acceptance_criteria": criteria, "scope": [], "implementation_steps": [],
            "reproduction_steps": [], "expected_behavior": ""}


def fetch(config, root, key, kind=None, list_only=False):
    with MCPClient(config, root) as client:
        tools = client.list_tools()
        if list_only:
            return tools
        name = config.get("ticket_tool")
        selected = next((t for t in tools if t.get("name") == name), None)
        if not selected:
            raise ValueError("Configure exact read-only ticket_tool from --list-tools output.")
        if selected.get("annotations", {}).get("destructiveHint") is True:
            raise ValueError("Refusing a destructive Jira tool.")
        def substitute(value):
            if isinstance(value, str):
                return value.replace("{key}", key)
            if isinstance(value, dict):
                return {k: substitute(v) for k, v in value.items()}
            if isinstance(value, list):
                return [substitute(v) for v in value]
            return value
        arguments = substitute(config.get("ticket_arguments", {}))
        if key not in json.dumps(arguments):
            raise ValueError("ticket_arguments must include {key}.")
        result = client.call("tools/call", {"name": name, "arguments": arguments})
        return normalize(result, key, config, kind)
