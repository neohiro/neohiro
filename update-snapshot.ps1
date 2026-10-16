<#
.SYNOPSIS
    Regenerate frenzypenguin-media-site\repos.json (filtered, star-ranked repo
    snapshot). Optionally commit it to the Pages repo (default when run locally).
.USAGE
    powershell -ExecutionPolicy Bypass -File update-snapshot.ps1 [-NoDeploy] [-OutFile <path>]
.NOTES
    CI copy lives at tools/update-snapshot.ps1 in the frenzypenguin-media.github.io
    repo - keep the two in sync (this file is canonical).
#>
[CmdletBinding()]
param(
    [switch]$NoDeploy,
    [string]$OutFile
)
$ErrorActionPreference = "Stop"

# Paginate via gh's native flag so we don't silently cap at 100 repos (any
# account that crosses 100 would otherwise produce an incomplete snapshot).
function Invoke-GhJson([string]$Endpoint) {
    $out = gh api --paginate $Endpoint 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "gh api failed (exit $LASTEXITCODE) for $Endpoint`: $($out -join ' ')"
    }
    return $out | ConvertFrom-Json
}

$org = Invoke-GhJson "/orgs/frenzypenguin-media/repos?per_page=100"
$usr = Invoke-GhJson "/users/neohiro/repos?per_page=100&sort=pushed"

$all = @($org) + @($usr) |
    Where-Object { -not $_.fork -and $_.name -notmatch 'github\.io$' -and $_.name -ne '.github' } |
    # Note: PowerShell's Sort-Object places $null keys at the end (PS 5.1) or start (PS 7+).
    # We only run this on the Windows host where PS 5.1 is the runtime, so the order is
    # stable. If PS version diversity ever matters, pre-filter repos with $null pushed_at.
    Sort-Object @{e = 'stargazers_count'; Descending = $true }, @{e = 'pushed_at'; Descending = $true } |
    ForEach-Object {
        # never-pushed repos return $null for pushed_at; preserve null rather than blowing up
        $pushed = if ($_.pushed_at) { ($_.pushed_at -replace 'T.*$', '') } else { $null }
        [ordered]@{
            name             = $_.name
            html_url         = $_.html_url
            description      = $_.description
            stargazers_count = $_.stargazers_count
            forks_count      = $_.forks_count
            language         = $_.language
            topics           = @($_.topics)
            # date-only: GitHub's pushed_at wobbles across edge caches, which would
            # make CI change-detection noisy; the site only displays the date anyway
            pushed_at        = $pushed
        }
    }

$json = ConvertTo-Json @($all) -Depth 4
if ($all.Count -eq 0 -or [string]::IsNullOrWhiteSpace($json)) {
    throw "no repos matched the snapshot filters - refusing to write an empty snapshot"
}
if (-not $OutFile) { $OutFile = Join-Path $PSScriptRoot "frenzypenguin-media-site\repos.json" }
[IO.File]::WriteAllText($OutFile, $json, (New-Object Text.UTF8Encoding($false)))
Write-Host "SNAPSHOT $($all.Count) repos -> $($OutFile)"

if (-not $NoDeploy) {
    . (Join-Path $PSScriptRoot "deploy-site.ps1")
    Deploy-Site -Path $OutFile -Repo "frenzypenguin-media.github.io" -Owner "frenzypenguin-media" `
        -Message "Refresh repos.json snapshot" -DestPath "repos.json"
}
