[CmdletBinding()]
param(
    [ValidateSet('feature', 'bugfix', 'refactor')]
    [string]$Workflow = 'feature'
)

$ErrorActionPreference = 'Stop'
& python (Join-Path $PSScriptRoot 'run-workflow.py') --workflow $Workflow --verify-only
if ($LASTEXITCODE -ne 0) { throw 'Workflow test failed.' }
