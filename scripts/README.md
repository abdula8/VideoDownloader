commit-and-pr.ps1

Usage

From the repository root in PowerShell:

```powershell
# Stage, commit, create branch and push
.\scripts\commit-and-pr.ps1 -Message "ci: update workflow" -OpenPR
```

If `gh` (GitHub CLI) is installed and authenticated, the script will open a PR in your browser. Otherwise it prints the PR URL for manual creation.

Notes

- The script creates a timestamped branch named `ci/auto-YYYYMMDD-HHMMSS` and pushes it to `origin`.
- It does not modify or merge any branches automatically.