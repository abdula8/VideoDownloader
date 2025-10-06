<#
PowerShell helper: commit-and-pr.ps1
- Stages all changes, commits with a message, creates a timestamped branch, pushes branch to origin.
- If GitHub CLI (`gh`) is installed and authenticated, opens a PR in the browser.
- Otherwise prints the PR URL for manual creation.

Usage:
.
# Example: .\scripts\commit-and-pr.ps1 -Message "ci: update workflow" -OpenPR
#
Param(
    [Parameter(Mandatory=$false)]
    [string]$Message = "Update from local changes",

    [switch]$OpenPR
)

function Run-Git([string]$args) {
    Write-Host "> git $args"
    $proc = Start-Process git -ArgumentList $args -NoNewWindow -PassThru -Wait -RedirectStandardOutput stdout.txt -RedirectStandardError stderr.txt
n    $out = Get-Content -Path stdout.txt -Raw -ErrorAction SilentlyContinue
    $err = Get-Content -Path stderr.txt -Raw -ErrorAction SilentlyContinue
    if ($out) { Write-Host $out }
    if ($err) { Write-Host $err }
}

# Ensure we're in repo root
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $PSScriptRoot

# Stage all changes
git add .

# Create branch name
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$branch = "ci/auto-$ts"

# Commit
$commitMsg = $Message
$commitOk = $false
try {
    git commit -m "$commitMsg"
    $commitOk = $true
} catch {
    Write-Host "No changes to commit or commit failed: $_"
}

if ($commitOk) {
    git checkout -b $branch
    git push -u origin $branch

    $owner = "abdula8"
    $repo = "VideoDownloader"
    $prUrl = "https://github.com/$owner/$repo/compare/main...$branch?expand=1"

    Write-Host "Branch pushed: $branch"
    Write-Host "Open this URL to create a PR:"
    Write-Host $prUrl

    if ($OpenPR) {
        # Try to open via gh if available
        $gh = Get-Command gh -ErrorAction SilentlyContinue
        if ($gh) {
            gh pr create --base main --head $branch --title "$commitMsg" --body "Auto-created PR by commit-and-pr.ps1" --web
        } else {
            Start-Process $prUrl
        }
    }
} else {
    Write-Host "Nothing to push"
}
