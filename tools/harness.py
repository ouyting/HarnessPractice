"""Harness V1.1: evidence-based local verification and explicit review."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

KEY = re.compile(r"[A-Z][A-Z0-9_]*-\d+")
WORKFLOWS = ("feature", "bugfix", "refactor")


def stamp():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def text(value):
    return isinstance(value, str) and bool(value.strip()) and value.strip().lower() not in ("todo", "tbd")


def strings(value):
    return isinstance(value, list) and bool(value) and all(text(item) for item in value)


def load_plan(root, ticket, workflow=None):
    if not KEY.fullmatch(ticket):
        raise ValueError("Ticket key must look like PROJ-123.")
    path = root / "plans" / (ticket + ".json")
    plan = read_json(path)
    if not isinstance(plan, dict):
        raise ValueError("Plan must be a JSON object.")
    if plan.get("key") != ticket or plan.get("type") not in WORKFLOWS:
        raise ValueError("Plan key/type is invalid.")
    if workflow and plan["type"] != workflow:
        raise ValueError("Ticket type does not match --workflow.")
    for field in ("summary", "description"):
        if not text(plan.get(field)):
            raise ValueError("Plan requires " + field)
    for field in ("acceptance_criteria", "scope", "implementation_steps"):
        if not strings(plan.get(field)):
            raise ValueError("Plan requires nonempty " + field)
    if plan["type"] == "bugfix":
        if not strings(plan.get("reproduction_steps")) or not text(plan.get("expected_behavior")):
            raise ValueError("Bugfix requires reproduction_steps and expected_behavior.")
    return plan


def load_config(root):
    config = read_json(root / ".harness/config.json")
    if not isinstance(config, dict) or config.get("version", "1.1") != "1.1":
        raise ValueError("Expected a Harness 1.1 config object.")
    for stage in ("build", "test"):
        spec = config.get(stage, {})
        if not isinstance(spec, dict):
            raise ValueError("Command configuration must be an object: " + stage)
        if not strings(spec.get("command")):
            raise ValueError("Configure a nonempty command argument list for " + stage)
        timeout = spec.get("timeout_seconds")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("Configure a positive timeout for " + stage)
    return config


def snapshot(root):
    """Hash source/config/plan files; ignore only runtime output and metadata."""
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if ".git" in rel.parts or "__pycache__" in rel.parts or path.suffix == ".pyc":
            continue
        if rel.as_posix().startswith((".harness/runs/", ".harness/memory/")):
            continue
        digest.update(rel.as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def execute(root, spec):
    command = [sys.executable if arg == "{python}" else arg for arg in spec["command"]]
    start = stamp()
    try:
        result = subprocess.run(command, cwd=root, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=spec["timeout_seconds"],
                                shell=False)
        return {"command": command, "started_at": start, "finished_at": stamp(),
                "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.TimeoutExpired as error:
        def decode(value):
            return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else (value or "")
        return {"command": command, "started_at": start, "finished_at": stamp(),
                "exit_code": None, "error": "timeout",
                "stdout": decode(error.stdout), "stderr": decode(error.stderr)}
    except OSError as error:
        return {"command": command, "started_at": start, "finished_at": stamp(),
                "exit_code": None, "error": str(error), "stdout": "", "stderr": ""}


def run(root, ticket, workflow=None, persist=True):
    plan = load_plan(root, ticket, workflow)
    config = load_config(root)
    before = snapshot(root)
    record = {"version": "1.1", "ticket": ticket, "workflow": plan["type"],
              "run_id": uuid.uuid4().hex, "started_at": stamp(), "snapshot": before,
              "state": "testing", "checks": []}
    print("[Planner] Validated local plan for " + ticket)
    print("[Coder] Implementation is supplied by developer/agent; this command verifies it.")
    for stage in ("build", "test"):
        evidence = execute(root, config[stage])
        evidence["stage"] = stage
        record["checks"].append(evidence)
        print("[" + stage + "] " + ("PASS" if evidence["exit_code"] == 0 else "FAIL"))
        if evidence["stdout"]:
            print(evidence["stdout"], end="")
        if evidence["stderr"]:
            print(evidence["stderr"], end="", file=sys.stderr)
        if evidence["exit_code"] != 0:
            record["state"] = "blocked"
            break
    else:
        record["state"] = "awaiting_review"
    if snapshot(root) != before:
        record["state"] = "blocked"
        record["error"] = "Source/config/plan changed during verification. Run again."
    record["finished_at"] = stamp()
    if persist:
        folder = root / ".harness/runs" / ticket
        write_json(folder / (record["run_id"] + ".json"), record)
        write_json(folder / "latest.json", record)
    print("[Workflow] " + record["state"] + "; run_id=" + record["run_id"])
    return record


def review(root, ticket, run_id, reviewer, decision, notes, diff_checked, criteria_checked):
    load_plan(root, ticket)
    folder = root / ".harness/runs" / ticket
    record = read_json(folder / "latest.json")
    if record.get("run_id") != run_id or record.get("state") != "awaiting_review":
        raise ValueError("Review must target the latest awaiting_review run.")
    if record["snapshot"] != snapshot(root):
        raise ValueError("Files changed after verification. Run verification again before review.")
    if not text(reviewer) or not text(notes):
        raise ValueError("Reviewer identity and review notes are required.")
    if decision == "approve" and not (diff_checked and criteria_checked):
        raise ValueError("Approval requires --diff-checked and --criteria-checked.")
    record["review"] = {"reviewer": reviewer, "decision": decision, "notes": notes,
                        "diff_checked": diff_checked, "criteria_checked": criteria_checked,
                        "at": stamp(), "run_id": run_id, "snapshot": record["snapshot"]}
    record["state"] = "done" if decision == "approve" else "blocked"
    write_json(folder / (run_id + ".json"), record)
    write_json(folder / "latest.json", record)
    print("[Reviewer] " + record["state"])
    return record


def main(root=None):
    root = root or Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Harness V1.1 verification and review")
    parser.add_argument("--ticket", required=True)
    parser.add_argument("--workflow", choices=WORKFLOWS)
    parser.add_argument("--verify-only", action="store_true", help="Run checks without saving results; cannot be reviewed.")
    parser.add_argument("--review", choices=("approve", "reject"))
    parser.add_argument("--run-id")
    parser.add_argument("--reviewer")
    parser.add_argument("--notes")
    parser.add_argument("--diff-checked", action="store_true")
    parser.add_argument("--criteria-checked", action="store_true")
    args = parser.parse_args()
    try:
        if args.review:
            if args.verify_only or not args.run_id:
                raise ValueError("Review requires --run-id and cannot use --verify-only.")
            record = review(root, args.ticket, args.run_id, args.reviewer, args.review,
                            args.notes, args.diff_checked, args.criteria_checked)
        else:
            record = run(root, args.ticket, args.workflow, not args.verify_only)
        return 1 if record["state"] == "blocked" else 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print("[Harness] BLOCKED: " + str(error), file=sys.stderr)
        return 2
