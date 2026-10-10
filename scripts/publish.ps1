# Refresh package from parent project and publish to GitHub.
# Usage:
#   .\scripts\publish.ps1
#   .\scripts\publish.ps1 -Repo papi-dti-merger -Public
#   .\scripts\publish.ps1 -CommitOnly

param(
  [string]$Repo = "papi-dti-merger",
  [switch]$Public,
  [switch]$Private,
  [switch]$CommitOnly,
  [string]$Remote = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "==> Assembling package from parent project"
python .\build_public_package.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$args = @(".\scripts\init_and_push_github.py", "--repo", $Repo)
if ($Public) { $args += "--public" }
if ($Private) { $args += "--private" }
if ($CommitOnly) { $args += "--commit-only" }
if ($Remote) { $args += @("--remote", $Remote) }

Write-Host "==> Git / GitHub"
python @args
exit $LASTEXITCODE
