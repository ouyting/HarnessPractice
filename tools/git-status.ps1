[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
& git -C $root status --short --branch
if ($LASTEXITCODE -ne 0) { throw 'Git status failed. Is this a Git repository?' }
