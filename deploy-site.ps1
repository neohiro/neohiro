<#
.SYNOPSIS
    Deploy site files to a GitHub Pages repo via Commit-Files.
.DESCRIPTION
    Reads source files as explicit UTF-8 ([IO.File]::ReadAllText) - never
    Get-Content, which mis-decodes BOM-less UTF-8 as ANSI on PS 5.1 and
    destroys emojis. Deploy-Site commits one file; Deploy-SiteFiles commits a
    whole directory of pages as a single atomic commit (multi-page sites must
    ship in one commit so deploy-all's HEAD==deployed verify stays valid).
.USAGE
    . .\deploy-site.ps1
    Deploy-Site -Path .\pages-site\index.html -Repo neohiro.github.io [-Owner x] [-Message "..."]
    Deploy-SiteFiles -Dir .\pages-site -Repo neohiro.github.io -Files @("index.html","HoneyScan.html")
#>
$ghCommit = Join-Path $PSScriptRoot "gh-commit.ps1"
if (-not (Test-Path -LiteralPath $ghCommit -PathType Leaf)) {
    throw "deploy-site.ps1: required dependency 'gh-commit.ps1' not found in $PSScriptRoot"
}
. $ghCommit
# BOM-less reader: the BOM-detecting UTF8 encoding would preserve any leading
# BOM bytes it sees, which would land in the committed file and render the
# deployed page with phantom whitespace at the start.
$bomlessReader = New-Object Text.UTF8Encoding($false)

function Deploy-Site {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Repo,
        [string]$Owner = "neohiro",
        [string]$Message = "Update site",
        [string]$DestPath = "index.html"
    )
    $content = [IO.File]::ReadAllText((Resolve-Path $Path), $bomlessReader)
    Commit-Files -Repo $Repo -Owner $Owner -Message $Message -Changes @(@{ path = $DestPath; content = $content })
}

function Deploy-SiteFiles {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Dir,
        [Parameter(Mandatory)][string[]]$Files,
        [Parameter(Mandatory)][string]$Repo,
        [string]$Owner = "neohiro",
        [string]$Message = "Update site"
    )
    $dirFull = (Resolve-Path $Dir).Path
    if (@($Files).Count -eq 0) { throw "Deploy-SiteFiles: no files specified" }
    $missing = @($Files | Where-Object { -not (Test-Path -LiteralPath (Join-Path $dirFull $_) -PathType Leaf) })
    if ($missing) { throw "Deploy-SiteFiles: missing file(s): $($missing -join ', ')" }
    $changes = foreach ($f in $Files) {
        @{ path = $f; content = [IO.File]::ReadAllText((Join-Path $dirFull $f), $bomlessReader) }
    }
    Commit-Files -Repo $Repo -Owner $Owner -Message $Message -Changes @($changes)
}
