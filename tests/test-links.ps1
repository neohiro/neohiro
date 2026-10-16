<#
.SYNOPSIS
    Link-integrity gate for neohiro.github.io. Exits non-zero on violation.
.RULES
    1. Every index card/guide fill link resolves to a shipped subpage.
    2. Every data-repo on the index has a matching <repo>.html page.
    3. Every subpage links exactly its own repository (github.com/neohiro/<name>)
       and no foreign repository.
    4. No orphan pages: every subpage is referenced from the index.
#>
[CmdletBinding()]
param()
$ErrorActionPreference = "Stop"
$script:fail = 0
$utf8 = [Text.Encoding]::UTF8
$root = Split-Path $PSScriptRoot -Parent
$dir = Join-Path $root "pages-site"

if (-not (Test-Path (Join-Path $dir "index.html"))) { Write-Host "FAIL pages-site\index.html missing"; exit 1 }
$index = [IO.File]::ReadAllText((Join-Path $dir "index.html"), $utf8)
$pages = Get-ChildItem $dir -Filter "*.html" | Where-Object { $_.Name -ne "index.html" }

# Rule 1: fill links must resolve to shipped pages
foreach ($m in [regex]::Matches($index, '<a class="fill" href="([^"]+\.html)"')) {
    $target = $m.Groups[1].Value
    if (-not (Test-Path -LiteralPath (Join-Path $dir $target) -PathType Leaf)) {
        Write-Host "FAIL [index] links to missing page: $target"; $script:fail++
    }
}

# Rule 2: data-repo attributes must have a detail page
foreach ($m in [regex]::Matches($index, 'data-repo="([^"]+)"')) {
    $repo = $m.Groups[1].Value
    if (-not (Test-Path -LiteralPath (Join-Path $dir "$repo.html") -PathType Leaf)) {
        Write-Host "FAIL [index] data-repo '$repo' has no $repo.html"; $script:fail++
    }
}

# Rule 3: each subpage links its own repo, and nothing else
foreach ($p in $pages) {
    $t = [IO.File]::ReadAllText($p.FullName, $utf8)
    $expected = 'href="https://github.com/neohiro/' + $p.BaseName + '"'
    if (-not $t.Contains($expected)) {
        Write-Host "FAIL [$($p.Name)] missing own repo link: $expected"; $script:fail++
    }
    foreach ($m in [regex]::Matches($t, 'github\.com/neohiro/([A-Za-z0-9._-]+)"')) {
        if ($m.Groups[1].Value -ne $p.BaseName) {
            Write-Host "FAIL [$($p.Name)] links foreign repo: $($m.Groups[1].Value)"; $script:fail++
        }
    }
}

# Rule 4: no orphans - every subpage is linked from the index
foreach ($p in $pages) {
    if (-not $index.Contains('"' + $p.Name + '"')) {
        Write-Host "FAIL [$($p.Name)] orphan page (not linked from index)"; $script:fail++
    }
}

Write-Host "LINKED $($pages.Count) subpage(s) against index"
if ($script:fail) { Write-Host "$($script:fail) link-integrity violation(s)"; exit 1 }
Write-Host "Link integrity OK."
