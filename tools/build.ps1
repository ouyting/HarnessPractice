[CmdletBinding()]
param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
& $Python (Join-Path $PSScriptRoot 'check-source.py')
if ($LASTEXITCODE -ne 0) { throw 'Python source validation failed.' }
