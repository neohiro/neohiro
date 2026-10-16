<#
.SYNOPSIS
    Publish the snapshot-refresh workflow and its tooling to the
    frenzypenguin-media.github.io repo (single multi-file commit).
.DESCRIPTION
    The FP repo is not cloned locally, so this script bridges canonical local
    sources (gh-commit.ps1, update-snapshot.ps1, fp-repo-workflow\.github\...)
    into that repo. Re-run it after editing ANY of those files.
.USAGE
    powershell -ExecutionPolicy Bypass -File publish-workflow.ps1
#>
[CmdletBinding()]
param()
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

$files = @(
    @{ src = "$root\gh-commit.ps1";                                           dest = "tools/gh-commit.ps1" },
    @{ src = "$root\update-snapshot.ps1";                                     dest = "tools/update-snapshot.ps1" },
    @{ src = "$root\fp-repo-workflow\.github\workflows\refresh-snapshot.yml"; dest = ".github/workflows/refresh-snapshot.yml" }
)

# Pre-validate: surface a clear error before opening any GitHub connection
foreach ($f in $files) {
    if (-not (Test-Path -LiteralPath $f.src -PathType Leaf)) {
        throw "publish-workflow.ps1: source file missing: $($f.src)"
    }
}

. (Join-Path $root "gh-commit.ps1")

# Read source files as BOM-less UTF-8: the BOM-detecting UTF8 encoding
# preserves any leading BOM bytes it sees, which would land in the committed
# file and render the deployed page with phantom whitespace at the start.
$bomlessReader = New-Object Text.UTF8Encoding($false)
$changes = foreach ($f in $files) {
    $content = [IO.File]::ReadAllText($f.src, $bomlessReader)
    if ($f.dest -like '*.ps1') {
        # parse-check via Parser API - never on the file directly so we can isolate errors
        $errs = $null
        [System.Management.Automation.Language.Parser]::ParseInput($content, [ref]$null, [ref]$errs) | Out-Null
        if ($errs.Count) { throw "parse errors in $($f.src): $($errs[0].Message)" }
    }
    @{ path = $f.dest; content = $content }
}
Commit-Files -Repo "frenzypenguin-media.github.io" -Owner "frenzypenguin-media" `
    -Message "CI: sync refresh-snapshot workflow + tooling from canonical sources" `
    -Changes @($changes)
