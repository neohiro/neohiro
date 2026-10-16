<#
.SYNOPSIS
    One-command release path: security sweep -> perf budget -> commit suite ->
    build -> deploy both sites -> live verification.
.USAGE
    powershell -ExecutionPolicy Bypass -File deploy-all.ps1 [-SkipLiveVerify]
#>
[CmdletBinding()]
param([switch]$SkipLiveVerify)
$ErrorActionPreference = "Stop"
$utf8 = [Text.Encoding]::UTF8
$root = $PSScriptRoot

function Invoke-Step([string]$name, [scriptblock]$step) {
    Write-Host "`n=== $name ==="
    & $step
    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { throw "$name failed (exit $LASTEXITCODE)" }
}

# 1. test gates (child processes so exit codes are trustworthy)
Invoke-Step "1/4 test gates" {
    powershell -ExecutionPolicy Bypass -File "$root\tests\test-security.ps1"
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
    powershell -ExecutionPolicy Bypass -File "$root\tests\test-perf-budget.ps1"
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
    powershell -ExecutionPolicy Bypass -File "$root\tests\test-links.ps1"
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
    powershell -ExecutionPolicy Bypass -File "$root\tests\test-gh-commit.ps1"
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
}

# 2. build
Invoke-Step "2/4 build" {
    powershell -ExecutionPolicy Bypass -File "$root\build-sites.ps1"
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
}

# 3. deploy
$script:deployed = @()
Invoke-Step "3/4 deploy" {
    . (Join-Path $root "deploy-site.ps1")
    # every page on neohiro.github.io: index plus the generated project/guide
    # subpages - shipped as ONE atomic commit (see Deploy-SiteFiles)
    $neoPages = Get-ChildItem (Join-Path $root "pages-site") -Filter "*.html" |
        Sort-Object Name | ForEach-Object { $_.Name }
    if (-not $neoPages) { throw "no pages found under pages-site" }
    $script:deployed += @{ label = "neohiro"; ownerRepo = "neohiro/neohiro.github.io"; files = $neoPages;
        out = Deploy-SiteFiles -Dir (Join-Path $root "pages-site") -Repo "neohiro.github.io" `
            -Files $neoPages -Message "Release: validated build" }
    $script:deployed += @{ label = "fp"; ownerRepo = "frenzypenguin-media/frenzypenguin-media.github.io";
        out = Deploy-Site -Path (Join-Path $root "frenzypenguin-media-site\index.html") -Repo "frenzypenguin-media.github.io" -Owner "frenzypenguin-media" `
            -Message "Release: validated build" }
}

# 4. live verify
if (-not $SkipLiveVerify) {
    if (@($script:deployed).Count -eq 0) { throw "4/4 live verify: no deploys recorded - cannot verify an empty set" }
    Invoke-Step "4/4 live verify" {
        Start-Sleep -Seconds 45
        function Has-Seq([byte[]]$hay, [byte[]]$needle) {
            if (-not $hay) { return $false }
            for ($i = 0; $i -le $hay.Length - $needle.Length; $i++) {
                $ok = $true
                for ($j = 0; $j -lt $needle.Length; $j++) { if ($hay[$i + $j] -ne $needle[$j]) { $ok = $false; break } }
                if ($ok) { return $true }
            }
            return $false
        }
        foreach ($d in $script:deployed) {
            if ($d.out -match '-> ([0-9a-f]{40})') { $wantSha = $Matches[1] } else { $wantSha = $null }
            $headSha = gh api "/repos/$($d.ownerRepo)/commits/main" --jq ".sha"
            if ($null -eq $headSha -or $headSha -eq '') { throw "$($d.label): gh api returned empty SHA - cannot verify" }
            if ($wantSha -and -not ($headSha.StartsWith($wantSha))) { throw "$($d.label): HEAD $($headSha.Substring(0,8)) != deployed $($wantSha.Substring(0,8))" }
            # poll: rebuild may lag the push; accept 'built' whenever it settles
            $st = $null
            $deadline = (Get-Date).AddSeconds(180)
            do {
                $st = gh api "/repos/$($d.ownerRepo)/pages" --jq ".status"
                if ($st -eq "built") { break }
                Start-Sleep -Seconds 10
            } while ((Get-Date) -lt $deadline)
            if ($st -ne "built") { throw "$($d.label): Pages still '$st' after 180s" }
            # verify every deployed page at its live URL (index gets core+glyph
            # checks; subpages get their repo-link marker)
            $files = if ($d.files) { @($d.files) } else { @("index.html") }
            foreach ($f in $files) {
                $path = if ($f -eq "index.html") { "/" } else { "/$f" }
                $repoName = $d.ownerRepo.Split('/')
                if ($repoName.Count -ne 2) { throw "$($d.label): bad ownerRepo '$($d.ownerRepo)' - expected owner/repo" }
                $url = "https://$($repoName[1])$path`?v=$wantSha"
                # CDN can briefly lag the 'built' flip - retry, then fail loudly
                $bytes = $null
                foreach ($attempt in 1..3) {
                    $resp = $null
                    try { $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 30 } catch {}
                    if ($resp) {
                        # Prefer RawContentStream (byte-fidelity), fall back to .Content
                        # which is a string and must be re-encoded to bytes.
                        if ($resp.RawContentStream) { $bytes = $resp.RawContentStream.ToArray() }
                        if (-not $bytes -and $resp.Content) { $bytes = $utf8.GetBytes($resp.Content) }
                    }
                    if ($bytes) { break }
                    if ($attempt -lt 3) { Start-Sleep -Seconds 5 }
                }
                if (-not $bytes) { throw "$($d.label)/${f}: live fetch returned nothing at $url" }
                $pageText = $utf8.GetString($bytes)
                if ($f -eq "index.html") {
                    $checks = @(
                        @{ ok = $pageText.Contains("startTypewriter"); what = "core injected" },
                        @{ ok = (Has-Seq $bytes @(0xE2, 0x98, 0x85)); what = "star glyph utf-8" }
                    )
                } else {
                    $checks = @(
                        @{ ok = $pageText.Contains("View on GitHub"); what = "repo link present" },
                        @{ ok = $pageText.Contains("data-repo="); what = "live-star hook present" }
                    )
                }
                foreach ($c in $checks) { if (-not $c.ok) { throw "$($d.label)/${f}: live check failed - $($c.what)" } }
                Write-Host "LIVE OK [$($d.label)/$f] head=$($headSha.Substring(0,8))"
            }
        }
    }
}

Write-Host "`nDEPLOY-ALL COMPLETE."
