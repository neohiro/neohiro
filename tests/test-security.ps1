<#
.SYNOPSIS
    Security sweep over both site HTML files. Exits non-zero on violation.
.RULES
    1. innerHTML only ever assigned the empty string (no dynamic HTML injection).
    2. No eval / new Function / document.write.
    3. No inline event handlers (onclick= etc.) - addEventListener only.
    4. Every target="_blank" link carries rel containing noopener.
    5. Self-contained pages: no <script src>, no <iframe>.
    6. No plaintext http:// references except W3C namespace URIs.
#>
[CmdletBinding()]
param()
$ErrorActionPreference = "Stop"
$script:fail = 0
$utf8 = [Text.Encoding]::UTF8
$root = Split-Path $PSScriptRoot -Parent

# --- meta-level: prove the detection rules still catch known-bad samples ---
$negFail = 0
$cases = @(
    @{ pat = 'innerHTML\s*=\s*([^;\r\n]+)'; bad = 'el.innerHTML = userText;' },
    @{ pat = '\beval\s*\(';                bad = 'eval(input);' },
    @{ pat = 'new\s+Function';             bad = 'new Function(x);' },
    @{ pat = '(?i)\son[a-z]+\s*=\s*"';     bad = '<div onclick="go()">' },
    @{ pat = '<script\s+src=';             bad = '<script src=//evil.js>' },
    @{ pat = 'http://[^"''\s<>]+';         bad = 'http://cdn.example.com/x' }
)
foreach ($c in $cases) {
    if (-not [regex]::IsMatch($c.bad, $c.pat)) { Write-Host "FAIL [selftest] rule no longer detects: $($c.pat)"; $negFail++ }
}
$tagVal = [regex]::Match('<a target="_blank" href="https://x">', '<a\b[^>]*>').Value
if (-not ($tagVal -match 'target\s*=\s*"_blank"' -and $tagVal -notmatch 'rel\s*=\s*"[^"]*noopener')) {
    Write-Host "FAIL [selftest] noopener rule no longer detects missing rel"; $negFail++
}
if ($negFail) { Write-Host "$negFail sweep self-test(s) failed"; exit 1 }
Write-Host "SELFTEST OK (detection rules verified)"

function Sweep([string]$label, [string]$relPath) {
    $t = [IO.File]::ReadAllText((Join-Path $root $relPath), $utf8)

    # Rule 1: innerHTML must be cleared, never assigned content
    foreach ($m in [regex]::Matches($t, 'innerHTML\s*=\s*([^;\r\n]+)')) {
        $rhs = $m.Groups[1].Value.Trim()
        if ($rhs -ne "''") { Write-Host "FAIL [$label] innerHTML assigned non-empty value: $($rhs.Substring(0, [Math]::Min(40, $rhs.Length)))"; $script:fail++ }
    }

    # Rule 2: forbidden dynamic-execution APIs
    foreach ($pat in @('\beval\s*\(', 'new\s+Function', 'document\.write')) {
        if ([regex]::IsMatch($t, $pat)) { Write-Host "FAIL [$label] forbidden pattern: $pat"; $script:fail++ }
    }

    # Rule 3: inline event handlers in markup
    foreach ($m in [regex]::Matches($t, '(?i)\son[a-z]+\s*=\s*"')) {
        Write-Host "FAIL [$label] inline event handler near index $($m.Index): $($m.Value)"; $script:fail++
    }

    # Rule 4: target=_blank requires rel with noopener
    foreach ($m in [regex]::Matches($t, '<a\b[^>]*>')) {
        $tag = $m.Value
        if ($tag -match 'target\s*=\s*"_blank"' -and $tag -notmatch 'rel\s*=\s*"[^"]*noopener') {
            Write-Host "FAIL [$label] _blank link without noopener: $($tag.Substring(0, [Math]::Min(60, $tag.Length)))"; $script:fail++
        }
    }

    # Rule 5: self-contained - no external scripts or frames
    foreach ($pat in @('<script\s+src=', '<iframe')) {
        if ($t -match $pat) { Write-Host "FAIL [$label] external/frame resource: $pat"; $script:fail++ }
    }

    # Rule 6: no plaintext http:// (allow W3C namespaces)
    foreach ($m in [regex]::Matches($t, 'http://[^"''\s<>]+')) {
        if ($m.Value -notmatch '^http://www\.w3\.org/') {
            Write-Host "FAIL [$label] insecure http reference: $($m.Value)"; $script:fail++
        }
    }

    Write-Host "SWEPT [$label]"
}

# every page shipped on neohiro.github.io: index + generated project/guide subpages
Get-ChildItem (Join-Path $root 'pages-site') -Filter '*.html' | Sort-Object Name | ForEach-Object {
    Sweep $_.BaseName ("pages-site\" + $_.Name)
}
Sweep "fp" "frenzypenguin-media-site\index.html"

if ($script:fail) { Write-Host "$($script:fail) security violation(s)"; exit 1 }
Write-Host "Security sweep OK."
