<#
.SYNOPSIS
    Inject shared/core.js into each site's index.html (idempotent), optionally deploy.
.USAGE
    powershell -ExecutionPolicy Bypass -File build-sites.ps1 [-Deploy] [-Root <dir>]
.NOTES
    Pages contain a /*__CORE__*/ placeholder (first run) or
    /*__CORE_START__*/.../*__CORE_END__*/ region (subsequent runs).
    -Root redirects the whole build at an alternate tree (used by tests);
    deployment always uses this script's own tree.
#>
[CmdletBinding()]
param([switch]$Deploy, [string]$Root)
$ErrorActionPreference = "Stop"
if (-not $Root) { $Root = $PSScriptRoot }
$utf8 = [Text.Encoding]::UTF8
$bomless = New-Object Text.UTF8Encoding($false)

# Read a file as bytes and strip any leading UTF-8 BOM. Returns the byte
# content (the decoder that was applied is the caller's choice).
# Uses Array.Copy so a BOM-only file (3 bytes) doesn't trigger PowerShell's
# reverse-range quirk ($raw[3..0] yields a single 0xBF element, not empty).
function Get-Utf8WithoutBom([string]$filePath) {
    $raw = [IO.File]::ReadAllBytes($filePath)
    $offset = 0
    if ($raw.Length -ge 3 -and $raw[0] -eq 0xEF -and $raw[1] -eq 0xBB -and $raw[2] -eq 0xBF) {
        $offset = 3
    }
    $out = New-Object 'byte[]' ($raw.Length - $offset)
    [Array]::Copy($raw, $offset, $out, 0, $out.Length)
    return ,$out
}

# Find the <script> block that contains the core marker.  This guards against a
# page that has a <script src="..."> tag before the inline core block — a naive
# first-<script> regex would capture the wrong tag.
function Get-ScriptBlockContent([string]$text, [string]$marker) {
    $idx = $text.IndexOf($marker)
    if ($idx -lt 0) { return $null }
    $open = $text.LastIndexOf('<script', $idx)
    if ($open -lt 0) { return $null }
    $closeTag = $text.IndexOf('>', $open)
    if ($closeTag -lt 0) { return $null }
    $contentStart = $closeTag + 1
    $endTag = $text.IndexOf('</script>', $contentStart)
    if ($endTag -lt 0) { return $null }
    return $text.Substring($contentStart, $endTag - $contentStart)
}

$corePath = Join-Path $Root "shared\core.js"
if (-not (Test-Path -LiteralPath $corePath -PathType Leaf)) { throw "build-sites.ps1: shared\core.js not found at $corePath" }
$coreText = $utf8.GetString((Get-Utf8WithoutBom $corePath)).TrimEnd()
if ([string]::IsNullOrWhiteSpace($coreText)) { throw "build-sites.ps1: shared\core.js is empty - refusing to inject an empty core" }
$sites = @(
    @{ html = "pages-site\index.html";              repo = "neohiro.github.io";              owner = "neohiro" },
    @{ html = "frenzypenguin-media-site\index.html"; repo = "frenzypenguin-media.github.io"; owner = "frenzypenguin-media" }
)
foreach ($site in $sites) {
    $path = Join-Path $Root $site.html
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "build-sites.ps1: missing target $($site.html) at $path" }
    $text = $utf8.GetString((Get-Utf8WithoutBom $path))
    $block = "/*__CORE_START__*/`r`n" + $coreText + "`r`n/*__CORE_END__*/"
    $sMarker = "/*__CORE_START__*/"
    $eMarker = "/*__CORE_END__*/"
    $pMarker = "/*__CORE__*/"
    $s = $text.IndexOf($sMarker)
    if ($s -ge 0) {
        $e = $text.IndexOf($eMarker, $s)
        if ($e -lt 0) { throw "unbalanced CORE markers in $($site.html)" }
        $text = $text.Remove($s, $e + $eMarker.Length - $s).Insert($s, $block)
    } elseif ($text.Contains($pMarker)) {
        $idx = $text.IndexOf($pMarker)
        $text = $text.Remove($idx, $pMarker.Length).Insert($idx, $block)
    } else {
        throw "no CORE placeholder found in $($site.html)"
    }
    # sanity: script block braces balanced, single core copy
    $js = Get-ScriptBlockContent $text "/*__CORE_START__*/"
    if ($null -eq $js) { throw "could not locate core script block in $($site.html)" }
    $o = ([regex]::Matches($js, '\{')).Count; $c = ([regex]::Matches($js, '\}')).Count
    if ($o -ne $c) { throw "brace mismatch in $($site.html): $o/$c" }
    $copies = ([regex]::Matches($text, [regex]::Escape('/*__CORE_START__*/'))).Count
    if ($copies -ne 1) { throw "expected 1 core copy in $($site.html), found $copies" }
    [IO.File]::WriteAllText($path, $text, $bomless)
    Write-Host "BUILT $($site.html) (script js $o brace pairs)"
}
if ($Deploy) {
    . (Join-Path $PSScriptRoot "deploy-site.ps1")
    foreach ($s in $sites) {
        Deploy-Site -Path (Join-Path $PSScriptRoot $s.html) -Repo $s.repo -Owner $s.owner `
            -Message "Build: inject shared core.js"
    }
}
