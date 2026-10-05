# Test Skill

Run `powershell -ExecutionPolicy Bypass -File tools/test.ps1`. The test executes the workflow's validation path with the Python standard library.

V1.1: `tools/test.ps1` runs the Harness regression suite directly, with no workflow recursion. Project ticket verification uses the configured test command via `run-workflow.py --ticket <KEY>`.
