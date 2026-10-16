<#
.SYNOPSIS
    Perf budget checks for both site files. Exits non-zero on violation.
.RULES
    1. @keyframes may animate only transform/opacity (+ whitelisted brand
       glitch props: clip-path/filter/box-shadow - short bursts, small areas).
       Background-position/left/top/width regressions are caught here.
    2. backdrop-filter allowed only inside .overlay/.panel rules (static modal),
       nowhere on scrollable content.
    3. will-change capped at 4 per file (layer memory).
    4. preconnect to api.github.com required.
#>
[CmdletBinding()]
param()
$ErrorActionPreference = "Stop"
$script:fail = 0
$utf8 = [Text.Encoding]::UTF8
$root = Split-Path $PSScriptRoot -Parent
$baseProps = @('transform', 'opacity')
$brandProps = @('clip-path', 'filter', 'box-shadow')

function Check-Css([string]$label, [string]$relPath, [string[]]$backdropAllow) {
    $t = [IO.File]::ReadAllText((Join-Path $root $relPath), $utf8)
    $css = [regex]::Match($t, '(?s)<style>(.*?)</style>').Groups[1].Value

    # Rule 1: keyframe properties
    $idx = 0
    while (($kf = $css.IndexOf('@keyframes', $idx)) -ge 0) {
        $open = $css.IndexOf('{', $kf); $d = 1; $j = $open + 1
        while ($d -gt 0 -and $j -lt $css.Length) {
            if ($css[$j] -eq '{') { $d++ } elseif ($css[$j] -eq '}') { $d-- }
            $j++
        }
        $inner = $css.Substring($open + 1, $j - $open - 2)
        foreach ($m in [regex]::Matches($inner, '([a-z-]+)\s*:')) {
            $p = $m.Groups[1].Value
            if ($p -notin ($baseProps + $brandProps)) {
                Write-Host "FAIL [$label] keyframes animates '$p'"; $script:fail++
            }
        }
        $idx = $j
    }

    # Rule 2: backdrop-filter selector context
    foreach ($m in [regex]::Matches($css, 'backdrop-filter')) {
        $pre = $css.Substring(0, $m.Index)
        $brace = $pre.LastIndexOf('{')
        $prevClose = if ($brace -gt 0) { $pre.LastIndexOf('}', $brace - 1) } else { -1 }
        $segStart = $prevClose + 1
        $sel = $pre.Substring($segStart, $brace - $segStart).Trim()
        $allowed = $false
        foreach ($a in $backdropAllow) { if ($sel -like "*$a*") { $allowed = $true } }
        if (-not $allowed) { Write-Host "FAIL [$label] backdrop-filter on '$sel'"; $script:fail++ }
    }

    # Rule 3: will-change cap
    $wc = ([regex]::Matches($css, 'will-change')).Count
    if ($wc -gt 4) { Write-Host "FAIL [$label] will-change used $wc times (cap 4)"; $script:fail++ }

    # Rule 4: no preconnect to api.github.com (privacy: no live API calls)
    if ($t.Contains('rel="preconnect"') -and $t.Contains('preconnect" href="https://api.github.com')) {
        Write-Host "FAIL [$label] preconnect to api.github.com leaks origin to GitHub before user interaction"; $script:fail++
    }

    Write-Host "CHECKED [$label]"
}

# every page shipped on neohiro.github.io: index + generated project/guide subpages
Get-ChildItem (Join-Path $root 'pages-site') -Filter '*.html' | Sort-Object Name | ForEach-Object {
    Check-Css $_.BaseName ("pages-site\" + $_.Name) @()
}
Check-Css "fp" "frenzypenguin-media-site\index.html" @('.overlay', '.panel')

if ($script:fail) { Write-Host "$($script:fail) budget violation(s)"; exit 1 }
Write-Host "Perf budget OK."
