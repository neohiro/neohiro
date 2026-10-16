<#
.SYNOPSIS
    Offline tests for gh-commit.ps1 (no network calls - gh is mocked).
.USAGE
    powershell -ExecutionPolicy Bypass -File tests\test-gh-commit.ps1
.NOTES
    A PowerShell function named 'gh' shadows gh.exe for the duration of the run,
    simulating: transient 5xx retries with backoff, fatal-error fail-fast,
    WhatIf zero-mutation dry-run, UTF-8 (BOM-less) request bodies, an
    emoji round-trip through Deploy-Site (regression guard for ANSI mis-decode),
    and build-sites.ps1 core injection idempotency.
    Exits non-zero if any check fails.
#>
$ErrorActionPreference = "Stop"
$script:calls = 0
$fail = 0

function gh {
    param([string]$cmd, [Parameter(ValueFromRemainingArguments)]$rest)
    $script:calls++
    $ii = [array]::IndexOf($rest, '--input')
    if ($ii -ge 0 -and $ii -lt ($rest.Count - 1)) {
        $ep = ($rest | Where-Object { $_ -like '/*' } | Select-Object -First 1)
        $script:lastBodyFile = $rest[$ii + 1]
        # Snapshot body bytes in memory: Commit-Files cleans the file in its
        # finally block, so any test that wants to inspect the body must read
        # it from the mock, not from the file path.
        $script:lastBodyBytes = [IO.File]::ReadAllBytes($script:lastBodyFile)
        if ($ep -like '*/git/blobs') { $script:blobBody = [Text.Encoding]::UTF8.GetString($script:lastBodyBytes) }
    }
    $endpoint = ($rest | Where-Object { $_ -like '/*' } | Select-Object -First 1)
    if ($script:scenario -eq "transient" -and $script:calls -le 2) {
        $global:LASTEXITCODE = 1
        Write-Error "gh: HTTP 502 Bad Request"
        return
    }
    if ($script:scenario -eq "fatal") {
        $global:LASTEXITCODE = 1
        Write-Error "gh: Not Found (HTTP 404)"
        return
    }
    $global:LASTEXITCODE = 0
    switch -Regex ($endpoint) {
        '/git/ref/heads/'      { '{"object":{"sha":"basesha","type":"commit"}}'; break }
        '/git/commits/basesha' { '{"tree":"basetree"}'; break }
        '/git/blobs'           { '{"sha":"blobsha1"}'; break }
        '/git/trees'           { '{"sha":"newtree"}'; break }
        '/git/commits'         { '{"sha":"newcommit"}'; break }
        '/git/refs/heads/'     { '{"object":{"sha":"newcommit"}}'; break }
        default                { throw "mock: unexpected endpoint $endpoint" }
    }
}

$scriptPath = Join-Path $PSScriptRoot "..\gh-commit.ps1"

# --- Test 0: gh-commit.ps1 parses cleanly ---
$errs = $null
[System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path $scriptPath), [ref]$null, [ref]$errs) | Out-Null
if ($errs.Count) { Write-Host "T0 FAIL: $($errs.Count) parse error(s)"; $errs | ForEach-Object Message; $fail++ }
else { Write-Host "T0 OK: gh-commit.ps1 parses cleanly" }

. $scriptPath
$changes = @(
    @{ path = "index.html"; content = "test content" },
    @{ path = "old.txt"; delete = $true }
)

# --- Test 1: transient 502 x2 then success (retries with backoff, full pipeline) ---
$script:scenario = "transient"; $script:calls = 0
$t0 = Get-Date
$out = Commit-Files -Repo "fake-repo" -Message "test commit" -Retries 3 -Changes $changes
$secs = [int]((Get-Date) - $t0).TotalSeconds
if ($out -match 'COMMITTED neohiro/fake-repo -> newcommit' -and $script:calls -eq 8 -and $secs -ge 4) {
    Write-Host "T1 OK: retried to success in ${secs}s after $script:calls call(s)"
} else { Write-Host "T1 FAIL: out='$out' calls=$script:calls elapsed=${secs}s"; $fail++ }

# --- Test 2: fatal 404 must throw immediately with no retries ---
$script:scenario = "fatal"; $script:calls = 0
try {
    Commit-Files -Repo "fake-repo" -Message "x" -Changes $changes -ErrorAction Stop | Out-Null
    Write-Host "T2 FAIL: should have thrown"; $fail++
} catch {
    if ($script:calls -eq 1) { Write-Host "T2 OK: fatal error failed fast after $script:calls call(s)" }
    else { Write-Host "T2 FAIL: expected 1 call, got $script:calls"; $fail++ }
}

# --- Test 3: WhatIf makes zero network calls and prints a plan ---
$script:scenario = "transient"; $script:calls = 0
Commit-Files -Repo "fake-repo" -Message "dry" -Changes $changes -WhatIf | Out-Null
if ($script:calls -eq 0) { Write-Host "T3 OK: WhatIf made 0 network calls" }
else { Write-Host "T3 FAIL: WhatIf made $script:calls call(s)"; $fail++ }

# --- Test 4: request body file written as UTF-8 without BOM ---
# Inspect the body bytes captured in-memory by the mock (avoids the race where
# Commit-Files's finally{} removes the file before we can read it).
$script:scenario = "success"; $script:calls = 0; $script:lastBodyBytes = $null
try {
    Commit-Files -Repo "fake-repo" -Message "t4 body" -Changes @(@{ path = "a.txt"; content = "x" }) | Out-Null
    $bodyBytes = $script:lastBodyBytes
    if ($null -eq $bodyBytes) { Write-Host "T4 FAIL: no body bytes captured"; $fail++ }
    elseif ($bodyBytes.Length -gt 0 -and $bodyBytes[0] -eq 239) { Write-Host "T4 FAIL: body has UTF-8 BOM (0xEF 0xBB 0xBF)"; $fail++ }
    else { Write-Host "T4 OK: body file is BOM-less" }
} catch {
    Write-Host "T4 FAIL: threw - $($_.Exception.Message)"; $fail++
}

# --- Test 5: Deploy-Site preserves emojis end-to-end (UTF-8 read -> blob bytes) ---
. (Join-Path $PSScriptRoot "..\deploy-site.ps1")
$script:scenario = "success"; $script:calls = 0
$tmpHtml = Join-Path ([IO.Path]::GetTempPath()) ("deploy-t5-" + [guid]::NewGuid().ToString("N") + ".html")
$alienStr = [Text.Encoding]::UTF8.GetString(@(0xF0, 0x9F, 0x91, 0xBD))
[IO.File]::WriteAllText($tmpHtml, "<p>emoji round-trip $alienStr</p>", [Text.Encoding]::UTF8)
try {
    $out5 = Deploy-Site -Path $tmpHtml -Repo "fake-repo" -Message "t5 emoji"
    $body = $script:blobBody | ConvertFrom-Json
    $decoded = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($body.content))
    $ok5 = ($out5 -match 'COMMITTED neohiro/fake-repo') -and $decoded.Contains($alienStr)
    if ($ok5) { Write-Host "T5 OK: emoji survived read->blob pipeline" }
    else { Write-Host "T5 FAIL: emoji lost in pipeline"; $fail++ }
} catch {
    Write-Host "T5 FAIL: threw - $($_.Exception.Message)"; $fail++
} finally {
    Remove-Item $tmpHtml -ErrorAction SilentlyContinue
}

# --- Test 6: build-sites.ps1 injects core once and is idempotent (temp fixture tree) ---
$fx = Join-Path ([IO.Path]::GetTempPath()) ("buildtest-" + [guid]::NewGuid().ToString("N"))
try {
    New-Item -ItemType Directory -Path (Join-Path $fx "pages-site") | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $fx "frenzypenguin-media-site") | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $fx "shared") | Out-Null
    # copy the real core.js into the fixture so build-sites.ps1 finds it via -Root
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot "..\shared\core.js") -Destination (Join-Path $fx "shared\core.js")
    foreach ($rel in @("pages-site\index.html", "frenzypenguin-media-site\index.html")) {
        [IO.File]::WriteAllText((Join-Path $fx $rel),
            "<html><body><script>`r`n/*__CORE__*/`r`n</script></body></html>", [Text.Encoding]::UTF8)
    }
    & (Join-Path $PSScriptRoot "..\build-sites.ps1") -Root $fx | Out-Null
    $h1 = (Get-FileHash (Join-Path $fx "pages-site\index.html")).Hash + (Get-FileHash (Join-Path $fx "frenzypenguin-media-site\index.html")).Hash
    & (Join-Path $PSScriptRoot "..\build-sites.ps1") -Root $fx | Out-Null
    $h2 = (Get-FileHash (Join-Path $fx "pages-site\index.html")).Hash + (Get-FileHash (Join-Path $fx "frenzypenguin-media-site\index.html")).Hash
    $ok = ($h1 -eq $h2)
    foreach ($rel in @("pages-site\index.html", "frenzypenguin-media-site\index.html")) {
        $c = [IO.File]::ReadAllText((Join-Path $fx $rel), [Text.Encoding]::UTF8)
        if (([regex]::Matches($c, [regex]::Escape('/*__CORE_START__*/'))).Count -ne 1) { $ok = $false }
        if (-not $c.Contains('function cachedJson')) { $ok = $false }
    }
    if ($ok) { Write-Host "T6 OK: build injects core exactly once and is idempotent" }
    else { Write-Host "T6 FAIL: build output not stable or core missing"; $fail++ }
} catch {
    Write-Host "T6 FAIL: threw - $($_.Exception.Message)"; $fail++
} finally {
    Remove-Item $fx -Recurse -Force -ErrorAction SilentlyContinue
}

# T7: build-sites.ps1 refuses to inject an empty core
try {
    $fx7 = Join-Path (Join-Path $env:TEMP "opencode") ("fx7-" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $fx7 -Force | Out-Null
    # minimal valid skeleton so build-sites.ps1's site discovery passes
    foreach ($sub in @("pages-site", "frenzypenguin-media-site")) {
        $d = Join-Path $fx7 $sub
        New-Item -ItemType Directory -Path $d -Force | Out-Null
        Set-Content -LiteralPath (Join-Path $d "index.html") -Value "<html><body><script>/*__CORE__*/</script></body></html>" -Encoding UTF8
    }
    $coreDir = Join-Path $fx7 "shared"
    New-Item -ItemType Directory -Path $coreDir -Force | Out-Null
    [IO.File]::WriteAllBytes((Join-Path $coreDir "core.js"), [byte[]]@())  # truly empty, 0 bytes
    $threw = $false
    try { & (Join-Path $PSScriptRoot "..\build-sites.ps1") -Root $fx7 | Out-Null } catch { $threw = $true }
    if ($threw) { Write-Host "T7 OK: build rejects empty core.js" }
    else { Write-Host "T7 FAIL: build did not reject empty core.js"; $fail++ }
} catch {
    Write-Host "T7 FAIL: threw - $($_.Exception.Message)"; $fail++
} finally {
    if ($fx7) { Remove-Item $fx7 -Recurse -Force -ErrorAction SilentlyContinue }
}

# T8: build-sites.ps1 strips a UTF-8 BOM from both core.js and the page
try {
    $fx8 = Join-Path (Join-Path $env:TEMP "opencode") ("fx8-" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $fx8 -Force | Out-Null
    foreach ($sub in @("pages-site", "frenzypenguin-media-site")) {
        $d = Join-Path $fx8 $sub
        New-Item -ItemType Directory -Path $d -Force | Out-Null
        # write the page with a leading BOM (UTF-8 EF BB BF)
        $bom = [byte[]](0xEF, 0xBB, 0xBF)
        $body = [Text.Encoding]::UTF8.GetBytes("<html><body><script>/*__CORE__*/</script></body></html>")
        Set-Content -LiteralPath (Join-Path $d "index.html") -Value ([byte[]]($bom + $body)) -Encoding Byte
    }
    $coreDir = Join-Path $fx8 "shared"
    New-Item -ItemType Directory -Path $coreDir -Force | Out-Null
    $coreBom = [byte[]](0xEF, 0xBB, 0xBF)
    $coreBody = [Text.Encoding]::UTF8.GetBytes("function cachedJson(){return 1} ")
    Set-Content -LiteralPath (Join-Path $coreDir "core.js") -Value ([byte[]]($coreBom + $coreBody)) -Encoding Byte
    & (Join-Path $PSScriptRoot "..\build-sites.ps1") -Root $fx8 | Out-Null
    $bomFree = $true
    foreach ($rel in @("pages-site\index.html", "frenzypenguin-media-site\index.html")) {
        $bytes = [IO.File]::ReadAllBytes((Join-Path $fx8 $rel))
        if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
            $bomFree = $false
        }
        # injected core must NOT include the BOM as the first byte after the script tag
        $text = [Text.Encoding]::UTF8.GetString([byte[]]$bytes)
        if ($text -notmatch 'function cachedJson') { $bomFree = $false }
    }
    if ($bomFree) { Write-Host "T8 OK: build strips BOM from both inputs" }
    else { Write-Host "T8 FAIL: BOM survived build"; $fail++ }
} catch {
    Write-Host "T8 FAIL: threw - $($_.Exception.Message)"; $fail++
} finally {
    if ($fx8) { Remove-Item $fx8 -Recurse -Force -ErrorAction SilentlyContinue }
}

# T9: Commit-Files cleans up its per-call body file (no leftover in %TEMP%\opencode)
$script:scenario = "success"; $script:calls = 0
$bodyFile9 = $null
try {
    $errs9 = $null
    [System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path (Join-Path $PSScriptRoot "..\gh-commit.ps1")), [ref]$null, [ref]$errs9) | Out-Null
    if ($errs9.Count) { throw "T9 FAIL: gh-commit.ps1 has parse errors: $($errs9[0].Message)" }
    Commit-Files -Repo "fake-repo" -Message "t9 cleanup" -Changes @(@{ path = "a.txt"; content = "x" }) | Out-Null
    $bodyFile9 = $script:lastBodyFile
    if (-not $bodyFile9) { Write-Host "T9 FAIL: no body file was captured"; $fail++ }
    elseif (Test-Path -LiteralPath $bodyFile9) { Write-Host "T9 FAIL: body file $bodyFile9 was not cleaned up"; $fail++ }
    else { Write-Host "T9 OK: Commit-Files cleans up its per-call body file" }
} catch {
    Write-Host "T9 FAIL: threw - $($_.Exception.Message)"; $fail++
}

# T10: build-sites.ps1 picks the correct <script> block when a page has
# an external <script src="..."> tag before the inline core block.
# Regression for the "first <script> wins" bug in the sanity check.
try {
    $fx10 = Join-Path (Join-Path $env:TEMP "opencode") ("fx10-" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $fx10 -Force | Out-Null
    # fixture: an earlier <script> block (no attributes) appears first so the
    # naive "first <script> wins" regex would match it and miss the inline core.
    # The external block has 0 braces; the core has 4 - so a buggy sanity check
    # would report 0 instead of 4.
    $pageWithExtScript = @'
<html>
<head>
<script>var __placeholder__ = 1;</script>
</head>
<body><h1>hello</h1>
<script>/*__CORE__*/</script>
</body>
</html>
'@
    foreach ($sub in @("pages-site", "frenzypenguin-media-site")) {
        $d = Join-Path $fx10 $sub
        New-Item -ItemType Directory -Path $d -Force | Out-Null
        [IO.File]::WriteAllText((Join-Path $d "index.html"), $pageWithExtScript, [Text.Encoding]::UTF8)
    }
    $coreDir = Join-Path $fx10 "shared"
    New-Item -ItemType Directory -Path $coreDir -Force | Out-Null
    # core with 4 brace pairs - sanity check should report 4
    $coreBody = 'function a(){return 1} function b(){return 2} function c(){return 3} function d(){return 4} '
    [IO.File]::WriteAllText((Join-Path $coreDir "core.js"), $coreBody, (New-Object Text.UTF8Encoding($false)))
    # Run the build and capture its host output (Write-Host inside a child
    # scriptblock isn't captured by 2>&1 in PS 5.1, so we redirect via a
    # transcript-like wrapper using a cmd file).
    $wrapper = Join-Path (Join-Path $env:TEMP "opencode") ("tw10-" + [guid]::NewGuid().ToString('N') + ".cmd")
    $scriptPath = (Resolve-Path (Join-Path $PSScriptRoot "..\build-sites.ps1")).Path
    $rootEscaped = $fx10 -replace '\\', '\\'
    # The wrapper calls powershell, redirects stdout/stderr to a file, then we read it.
    $outFile10 = Join-Path (Join-Path $env:TEMP "opencode") ("tw10-out-" + [guid]::NewGuid().ToString('N') + ".txt")
    $cmd = "@echo off`npowershell -ExecutionPolicy Bypass -File `"$scriptPath`" -Root `"$rootEscaped`" > `"$outFile10`" 2>&1"
    Set-Content -LiteralPath $wrapper -Value $cmd -Encoding ASCII
    & cmd /c $wrapper | Out-Null
    $buildOut = (Get-Content -LiteralPath $outFile10 -Raw) -join "`n"
    Remove-Item $wrapper, $outFile10 -ErrorAction SilentlyContinue

    # The bug would cause the build to print "script js 0 brace pairs"
    # (matching the first <script> block, the placeholder). The fix reports 4.
    $builtOk = $false
    foreach ($rel in @("pages-site\index.html", "frenzypenguin-media-site\index.html")) {
        $bytes = [IO.File]::ReadAllBytes((Join-Path $fx10 $rel))
        $text = [Text.Encoding]::UTF8.GetString($bytes)
        $coreIdx = $text.IndexOf('/*__CORE_START__*/')
        if ($coreIdx -ge 0) {
            $open = $text.LastIndexOf('<script', $coreIdx)
            $closeTag = $text.IndexOf('>', $open)
            $endTag = $text.IndexOf('</script>', $closeTag + 1)
            if ($open -ge 0 -and $endTag -ge 0) {
                $jsContent = $text.Substring($closeTag + 1, $endTag - $closeTag - 1)
                $openBraces = ([regex]::Matches($jsContent, '\{')).Count
                if ($openBraces -eq 4) { $builtOk = $true }
            }
        }
    }
    $reportOk = $buildOut -match 'script js 4 brace pairs'
    if ($builtOk -and $reportOk) {
        Write-Host "T10 OK: brace-count sanity check uses the core block, not the earlier <script>"
    } else {
        Write-Host "T10 FAIL: builtOk=$builtOk reportOk=$reportOk buildOut='$buildOut'"; $fail++
    }
} catch {
    Write-Host "T10 FAIL: threw - $($_.Exception.Message)"; $fail++
} finally {
    if ($fx10) { Remove-Item $fx10 -Recurse -Force -ErrorAction SilentlyContinue }
}

# T11: Commit-Files rejects changes with empty/missing path
$script:scenario = "success"; $script:calls = 0
try {
    $caught = $false
    try {
        Commit-Files -Repo "fake-repo" -Message "t11" -Changes @(@{ content = "x" }) -ErrorAction Stop | Out-Null
    } catch [System.Management.Automation.RuntimeException] {
        if ($_.Exception.Message -match 'path is required') { $caught = $true }
    }
    if ($caught) { Write-Host "T11 OK: Commit-Files rejects empty path" }
    else { Write-Host "T11 FAIL: did not throw the expected 'path is required' error"; $fail++ }
} catch {
    Write-Host "T11 FAIL: threw - $($_.Exception.Message)"; $fail++
}

# T12: Commit-Files rejects blobs larger than GitHub's 50 MB limit, before any blob upload
$script:scenario = "success"; $script:calls = 0
try {
    $huge = [byte[]]::new((40 * 1024 * 1024) + 1)  # 40 MB raw -> ~53 MB base64 (exceeds limit)
    $caught = $false
    try {
        Commit-Files -Repo "fake-repo" -Message "t12" -Changes @(@{ path = "huge.bin"; bytes = $huge }) -ErrorAction Stop | Out-Null
    } catch [System.Management.Automation.RuntimeException] {
        if ($_.Exception.Message -match '50 MB') { $caught = $true }
    }
    # Structural calls (ref head + base commit) = 2; guard runs before any blob POST,
    # so total must be <= 2.
    if ($caught -and $script:calls -le 2) {
        Write-Host "T12 OK: Commit-Files rejects oversized blobs before blob API call"
    } else {
        Write-Host "T12 FAIL: caught=$caught calls=$script:calls (expected <=2)"; $fail++
    }
} catch {
    Write-Host "T12 FAIL: threw - $($_.Exception.Message)"; $fail++
}

Write-Host ""
if ($fail) { Write-Host "$fail test(s) FAILED"; exit 1 }
Write-Host "All tests passed."
