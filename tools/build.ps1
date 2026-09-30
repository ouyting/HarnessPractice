[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$required = @(
    'AGENTS.md',
    '.harness/rules/coding.md',
    '.harness/rules/architecture.md',
    '.harness/rules/safety.md',
    '.harness/rules/forbidden.md',
    '.harness/skills/build.md',
    '.harness/skills/test.md',
    '.harness/skills/git.md',
    '.harness/skills/workflow.md',
    '.harness/workflows/feature.md',
    '.harness/workflows/bugfix.md',
    '.harness/workflows/refactor.md',
    '.harness/workflows/mvp.md',
    '.harness/memory/STATUS.md',
    '.harness/memory/DECISIONS.md',
    '.harness/memory/MISTAKES.md',
    'tools/run-workflow.py'
)

$missing = $required | Where-Object { -not (Test-Path -LiteralPath (Join-Path $root $_) -PathType Leaf) }
if ($missing) { throw "Harness layout incomplete: $($missing -join ', ')" }

& python -m py_compile (Join-Path $PSScriptRoot 'run-workflow.py')
if ($LASTEXITCODE -ne 0) { throw 'Python syntax validation failed.' }
Write-Host 'Build verification passed: Harness V1 layout and Python syntax are valid.'
