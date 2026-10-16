<#
.SYNOPSIS
    Bidirectional daily sync between this workspace and neohiro/opencode-config,
    plus one-command restore, verification and fresh-client drill.
.DESCRIPTION
    Modes:
      Sync     (default) push local changes -> GitHub, pull remote-only files -> local,
               regenerate MANIFEST.md, then run the fresh-client drill. Safe to run daily.
      Restore  GitHub -> workspace (-Root). Writes files that are missing locally or whose
               remote content differs. Never deletes.
      Verify   report-only comparison, exit 3 on drift.
      Drill    download the repo tarball, extract to temp, audit every MANIFEST.md row.
    Policy (stateless, deletion-safe): local content wins; remote-only entries are
    restored; nothing is ever deleted on either side by this script.
    Transport is the GitHub REST API (local MinGit lacks sh.exe/GCM, and API commits
    avoid tokens in git config or process command lines). Uses canonical
    gh-commit.ps1 when present; otherwise a built-in equivalent.
.USAGE
    powershell -ExecutionPolicy Bypass -File sync-opencode-config.ps1 [-Mode Sync|Restore|Verify|Drill] [-Root <path>] [-InstallTask]
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File sync-opencode-config.ps1 -InstallTask   # once per machine
#>
[CmdletBinding()]
param(
    [ValidateSet('Sync','Restore','Verify','Drill')]
    [string]$Mode = 'Sync',
    [string]$Root,
    [switch]$InstallTask,
    [string]$Owner = 'neohiro',
    [ValidatePattern('^[A-Za-z0-9_.-]{1,100}$')][string]$Repo = 'opencode-config',
    [ValidatePattern('^[A-Za-z0-9._-]{1,100}$')][string]$Branch = 'main'
)
$ErrorActionPreference = 'Stop'

if (-not $Root) { $Root = 'C:\Users\skele\Documents\GitHub Manager' }
$logDir = Join-Path $env:LOCALAPPDATA 'opencode-config-sync'
$logFile = Join-Path $logDir 'sync.log'
$tmpDir = Join-Path $env:TEMP 'opencode-sync'
$metaFiles = @('README.md', '.gitattributes')   # repo-only, curated outside this script
$manifestName = 'MANIFEST.md'

function Log([string]$msg) {
    if (-not (Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
    if ((Test-Path -LiteralPath $logFile) -and ((Get-Item -LiteralPath $logFile).Length -gt 1MB)) {
        Move-Item -LiteralPath $logFile -Destination "$logFile.old" -Force -ErrorAction SilentlyContinue
    }
    $line = '{0} [{1}] {2}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Mode, $msg
    Add-Content -LiteralPath $logFile -Value $line -Encoding UTF8
    Write-Output $msg
}

# ---- single-instance guard ---------------------------------------------------------
# per-workspace-root mutex: several workspaces on one machine sync independently
$rootKey = [BitConverter]::ToString(
    ([System.Security.Cryptography.SHA1CryptoServiceProvider]::Create()).ComputeHash(
        [Text.Encoding]::UTF8.GetBytes($Root.ToLower())
    )
).Replace('-', '').Substring(0, 16)
$script:mutex = New-Object System.Threading.Mutex($false, "Local\OpenCodeConfigSync-$rootKey")
if (-not $script:mutex.WaitOne(0)) { Log 'another sync instance holds the mutex; skipping'; exit 0 }

# ---- gh helpers --------------------------------------------------------------------
# Transient GitHub-side errors (replication hiccups, secondary rate limits) were
# observed empirically; retry like canonical gh-commit.ps1 does. Content-addressed
# POSTs (blobs/commits) are safe to replay: identical payloads yield identical SHAs.
function Invoke-Gh([string[]]$GhArgs) {
    $prev = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try {
        $exe = Get-Command -Name gh -CommandType Application -ErrorAction Stop
        $out = $null
        for ($i = 0; ; $i++) {
            $out = & $exe @GhArgs 2>&1
            if ($LASTEXITCODE -eq 0) { break }
            $err = ($out | Out-String)
            if ($i -ge 3 -or ($err -notmatch 'HTTP 5\d\d|rate limit|timed? ?out|connection|Could not resolve|SSL|EOF|empty stream')) { break }
            Start-Sleep -Seconds ([Math]::Pow(2, $i))
        }
    } finally { $ErrorActionPreference = $prev }
    [pscustomobject]@{ rc = $LASTEXITCODE; text = ($out | Out-String).Trim() }
}
function ApiJson([string]$endpoint) {
    $r = Invoke-Gh @('api', $endpoint)
    if ($r.rc -ne 0) { throw "gh api $endpoint failed: $($r.text)" }
    $r.text | ConvertFrom-Json
}

# ---- git blob sha1 of raw bytes ----------------------------------------------------
$sha1 = New-Object System.Security.Cryptography.SHA1CryptoServiceProvider
function Get-BlobSha([byte[]]$b) {
    $h = [Text.Encoding]::ASCII.GetBytes("blob $($b.Length)`0")
    $a = New-Object byte[] ($h.Length + $b.Length)
    [Array]::Copy($h, 0, $a, 0, $h.Length)
    [Array]::Copy($b, 0, $a, $h.Length, $b.Length)
    ($script:sha1.ComputeHash($a) | ForEach-Object { $_.ToString('x2') }) -join ''
}
function Get-LocalBytes([string]$wsRel) { [IO.File]::ReadAllBytes((Join-Path $Root $wsRel)) }

# ---- mapping: workspace <-> repo ---------------------------------------------------
$script:rootFiles = @(
    'gh-commit.ps1','deploy-site.ps1','deploy-all.ps1','build-sites.ps1',
    'publish-workflow.ps1','update-snapshot.ps1','repair_tips.ps1',
    'strip_binaries.ps1','strip_binaries_v2.ps1','strip_binaries_v3.ps1',
    'check_mojibake.py','mojibake_report.txt','gen_previews.py',
    'discussions.py','seed_discussions.py','debug_gql.py','announcements.json',
    'batch_rulesets.py','batch_a.py','batch_a_fix.py','batch_c_gen.py',
    'batch_g_readme.py','batch_h.py','batch_i.py','sync-opencode-config.ps1'
)
$script:rootDirs = @('tests','shared','templates','fp-repo-workflow','scaffold',
    'social-previews','batchA','batchA_fix','batchG_readmes','batchH','batchI')
$script:pairs = @(  # single files: workspace rel -> repo path
    @('analyze_bg.py','BlackGlass/analyze_bg.py'),
    @('deps_bg.py','BlackGlass/deps_bg.py'),
    @('fix_imports_bg.py','BlackGlass/fix_imports_bg.py'),
    @('fix_anchor.py','BlackGlass/fix_anchor.py'),
    @('patch_bg_core.py','BlackGlass/patch_bg_core.py'),
    @('patch_bg_lists.py','BlackGlass/patch_bg_lists.py'),
    @('split_bg.py','BlackGlass/split_bg.py'),
    @('patch_sm1.py','SystemMonitor/patch_sm1.py'),
    @('patch_sm_sensors.py','SystemMonitor/patch_sm_sensors.py'),
    @('patch_sm_tiles.py','SystemMonitor/patch_sm_tiles.py'),
    @('patch_sm_widget.py','SystemMonitor/patch_sm_widget.py'),
    @('fix_ns.py','SystemMonitor/fix_ns.py'),
    @('diag_na.py','NewsAggregator/diag_na.py'),
    @('prep_ep_rename.py','ExploitProtection/prep_ep_rename.py'),
    @('ep_codeql.yml','ExploitProtection/ep_codeql.yml'),
    @('org-profile-readme.md','frenzypenguin-media-org-profile/org-profile-readme.md'),
    @('profile\README.md','neohiro-profile/profile-draft-README.md')
)

function Get-Managed {
    $seen = @{}; $list = @()
    foreach ($f in $script:rootFiles) {
        $rp = $f -replace '\\', '/'
        $list += [pscustomobject]@{ ws = $f; repo = $rp }; $seen[$rp] = $true
    }
    foreach ($d in $script:rootDirs) {
        $base = Join-Path $Root $d
        if (Test-Path -LiteralPath $base) {
            foreach ($fi in (Get-ChildItem -LiteralPath $base -Recurse -File -Force)) {
                $rel = $fi.FullName.Substring($base.Length + 1) -replace '\\', '/'
                $rp = "$d/$rel"
                if (-not $seen.ContainsKey($rp)) { $list += [pscustomobject]@{ ws = "$d\$rel"; repo = $rp }; $seen[$rp] = $true }
            }
        }
    }
    foreach ($p in $script:pairs) {
        if (-not $seen.ContainsKey($p[1])) { $list += [pscustomobject]@{ ws = $p[0]; repo = $p[1] }; $seen[$p[1]] = $true }
    }
    $bf = Join-Path $Root 'batchF'
    if (Test-Path -LiteralPath $bf) {
        foreach ($fi in (Get-ChildItem -LiteralPath $bf -Recurse -File -Force)) {
            $rel = $fi.FullName.Substring($bf.Length + 1) -replace '\\', '/'
            $rp = "ExploitProtection/batchF/$rel"
            if (-not $seen.ContainsKey($rp)) { $list += [pscustomobject]@{ ws = "batchF\$rel"; repo = $rp }; $seen[$rp] = $true }
        }
    }
    , ($list | Sort-Object repo)
}

function ConvertTo-WsPath([string]$repoPath) {
    # inverse of Get-Managed for remote-driven restores; $null = unmanaged/meta
    if (($metaFiles -contains $repoPath) -or ($repoPath -eq $manifestName)) { return $null }
    $asWs = $repoPath -replace '/', '\'
    if ($script:rootFiles -contains $asWs) { return $asWs }
    foreach ($d in $script:rootDirs) { if ($repoPath.StartsWith("$d/")) { return $asWs } }
    foreach ($p in $script:pairs) { if ($p[1] -eq $repoPath) { return $p[0] } }
    if ($repoPath.StartsWith('ExploitProtection/batchF/')) { return ($repoPath -replace '^ExploitProtection/', '') -replace '/', '\' }
    return $null
}

function ConvertTo-Class([string]$repoPath) {
    $top = ($repoPath -split '/')[0]
    switch ($top) {
        'tests' { 'Pipeline (release gate)' }
        'shared' { 'Shared asset' }
        'templates' { 'Shared asset' }
        'fp-repo-workflow' { 'Shared asset' }
        'scaffold' { 'Batch staging (batch C)' }
        { $_ -in @('batchA','batchA_fix','batchG_readmes','batchH','batchI') } { 'Batch staging' }
        'social-previews' { 'Cross-repo artifact' }
        'BlackGlass' { 'Project: BlackGlass' }
        'SystemMonitor' { 'Project: SystemMonitor' }
        'ExploitProtection' { 'Project: ExploitProtection' }
        'NewsAggregator' { 'Project: NewsAggregator' }
        'frenzypenguin-media-org-profile' { 'Draft (unpushed)' }
        'neohiro-profile' { 'Draft (superseded)' }
        default {
            switch -Regex ($repoPath) {
                '^(gh-commit|deploy-site|deploy-all|build-sites|publish-workflow|update-snapshot)\.ps1$' { 'Pipeline (active)' }
                '^sync-opencode-config\.ps1$' { 'Pipeline (automation)' }
                '^README\.md$' { 'Doc' }
                '^\.gitattributes$' { 'Repo metadata' }
                '^batch_rulesets\.py$' { 'Cross-repo op (rulesets)' }
                '^(discussions|seed_discussions)\.py$' { 'Cross-repo op (discussions)' }
                '^debug_gql\.py$|^announcements\.json$' { 'Cross-repo op (discussions)' }
                '^(check_mojibake\.py|mojibake_report\.txt)$' { 'Cross-repo op (audit)' }
                '^gen_previews\.py$' { 'Cross-repo op (previews)' }
                '^strip_binaries.*\.ps1$|^repair_tips\.ps1$' { 'Cross-repo op (history rewrite)' }
                '^(batch_a|batch_a_fix|batch_c_gen|batch_g_readme|batch_h|batch_i)\.py$' { 'Batch generator' }
                default { throw "UNCLASSIFIED: $repoPath" }
            }
        }
    }
}

# ---- remote state ------------------------------------------------------------------
function Get-RemoteShas {
    $head = ApiJson "/repos/$Owner/$Repo/git/ref/heads/$Branch"
    $tree = ApiJson "/repos/$Owner/$Repo/git/trees/$($head.object.sha)?recursive=1"
    if ($tree.truncated) { throw 'remote tree truncated; repo too large for tree-API sync' }
    $map = @{}
    foreach ($e in $tree.tree) { if ($e.type -eq 'blob') { $map[$e.path] = $e.sha } }
    return $map
}

# ---- push: canonical gh-commit.ps1 when present, built-in equivalent otherwise ------
function Invoke-Push([object[]]$Changes) {
    $canonical = Join-Path $Root 'gh-commit.ps1'
    if (Test-Path -LiteralPath $canonical) {
        # canonical Commit-Files writes its payload under %TEMP%\opencode - absent on fresh machines
        if (-not (Test-Path -LiteralPath "$env:TEMP\opencode")) { New-Item -ItemType Directory -Path "$env:TEMP\opencode" -Force | Out-Null }
        . $canonical
        Commit-Files -Repo $Repo -Owner $Owner -Branch $Branch -Message 'Auto-sync: workspace backup [oc]' -Changes $Changes
        return
    }
    if (-not (Test-Path -LiteralPath $tmpDir)) { New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null }
    $tmp = Join-Path $tmpDir 'payload.json'
    function Test-Transient([string]$e) { $e -match 'HTTP 5\d\d|rate limit|timed? ?out|connection|Could not resolve|SSL|EOF|empty stream' }
    function ApiIn([string]$method, [string]$endpoint, [string]$json) {
        [IO.File]::WriteAllText($tmp, $json, (New-Object Text.UTF8Encoding($false)))
        for ($i = 0; ; $i++) {
            $r = Invoke-Gh (@('api', '-X', $method, $endpoint, '--input', $tmp))
            if ($r.rc -eq 0) { return $r.text }
            if ($i -ge 3 -or -not (Test-Transient $r.text)) { throw "gh api $method $endpoint failed: $($r.text)" }
            Start-Sleep -Seconds ([Math]::Pow(2, $i) * 2)
        }
    }
    $ref = ApiJson "/repos/$Owner/$Repo/git/ref/heads/$Branch"
    $commitSha = $ref.object.sha
    $baseTree = (ApiJson "/repos/$Owner/$Repo/git/commits/$commitSha").tree.sha
    $entries = @()
    foreach ($c in $Changes) {
        $b64 = [Convert]::ToBase64String($c.bytes)
        $resp = (ApiIn 'POST' "/repos/$Owner/$Repo/git/blobs" (@{ content = $b64; encoding = 'base64' } | ConvertTo-Json)) | ConvertFrom-Json
        if (-not $resp.sha) { throw "blob creation failed for $($c.path)" }
        $entries += @{ path = $c.path; mode = '100644'; type = 'blob'; sha = $resp.sha }
    }
    $treeResp = (ApiIn 'POST' "/repos/$Owner/$Repo/git/trees" (@{ base_tree = $baseTree; tree = $entries } | ConvertTo-Json -Depth 6)) | ConvertFrom-Json
    $agent = @{ name = 'OpenCode Agent'; email = 'opencode-agent@users.noreply.github.com' }
    $body = @{ message = 'Auto-sync: workspace backup [oc]'; tree = $treeResp.sha; parents = @($commitSha); author = $agent; committer = $agent }
    $newCommit = (ApiIn 'POST' "/repos/$Owner/$Repo/git/commits" ($body | ConvertTo-Json -Depth 5)) | ConvertFrom-Json
    $r = Invoke-Gh @('api', '-X', 'PATCH', "/repos/$Owner/$Repo/git/refs/heads/$Branch", '-f', "sha=$($newCommit.sha)")
    if ($r.rc -ne 0) { throw "ref update failed: $($r.text)" }
    Write-Output "COMMITTED ${Owner}/${Repo} -> $($newCommit.sha) ($($entries.Count) files)"
}

# Multi-device races: two clients pushing concurrently -> the loser gets a
# non-fast-forward rejection from the refs API. Re-read remote, drop entries
# another client already incorporated, retry (blobs are content-addressed;
# orphans are harmless).
function Invoke-SyncPush([object[]]$Pending) {
    $script:lastPushed = $Pending.Count
    for ($attempt = 1; $attempt -le 4; $attempt++) {
        try { Invoke-Push $Pending; return }
        catch {
            $msg = $_.Exception.Message
            if ($attempt -lt 4 -and $msg -match 'fast.?forward|409|422|not a descendant|is not at') {
                Log "push race with another client; re-basing (attempt $attempt/3)"
                Start-Sleep -Seconds 2
                $fresh = Get-RemoteShas
                $Pending = @($Pending | Where-Object { (Get-BlobSha $_.bytes) -ne $fresh[$_.path] })
                $script:lastPushed = $Pending.Count
                if (-not $Pending.Count) { Log 'after re-base nothing left to push (other client won)'; return }
            } else { throw }
        }
    }
}

# Preserve a drifted local copy before Restore overwrites it (recovery insurance;
# stashed outside the managed set so it never re-enters the backup).
function Save-RestoreStash([string]$wsRel) {
    $src = Join-Path $Root $wsRel
    if (-not (Test-Path -LiteralPath $src)) { return }
    $stashDir = Join-Path $logDir ("stash\" + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    $dest = Join-Path $stashDir $wsRel
    $destDir = Split-Path $dest -Parent
    if (-not (Test-Path -LiteralPath $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
    Copy-Item -LiteralPath $src -Destination $dest -Force
}

function Invoke-Pull([string]$repoPath, [string]$blobSha, [switch]$Overwrite) {
    $wsRel = ConvertTo-WsPath $repoPath
    if (-not $wsRel) { return $false }
    $target = Join-Path $Root $wsRel
    if ((Test-Path -LiteralPath $target) -and -not $Overwrite) { return $false }
    $dir = Split-Path $target -Parent
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $r = Invoke-Gh @('api', "/repos/$Owner/$Repo/git/blobs/$blobSha", '--jq', '.content')
    if ($r.rc -ne 0) { throw "blob fetch failed for ${repoPath}: $($r.text)" }
    $bytes = [Convert]::FromBase64String(($r.text -replace '\s', ''))
    [IO.File]::WriteAllBytes($target, $bytes)
    return $true
}

# ---- manifest ----------------------------------------------------------------------
function Update-Manifest([hashtable]$remoteShas) {
    $paths = @( (Get-Managed).repo ) + $metaFiles
    $sb = New-Object Text.StringBuilder
    [void]$sb.AppendLine('# MANIFEST')
    [void]$sb.AppendLine()
    [void]$sb.AppendLine('Every tracked file except this one: size, SHA-256 and classification.')
    [void]$sb.AppendLine('Regenerated automatically by sync-opencode-config.ps1 on each sync.')
    [void]$sb.AppendLine()
    [void]$sb.AppendLine(("Total files: **{0}**" -f ($paths.Count + 1)))
    [void]$sb.AppendLine()
    [void]$sb.AppendLine('| Path | Bytes | SHA-256 | Class |')
    [void]$sb.AppendLine('|---|---:|---|---|')
    foreach ($rp in ($paths | Sort-Object -Unique)) {
        $bytes = $null
        $wsRel = ConvertTo-WsPath $rp
        if ($wsRel -and (Test-Path -LiteralPath (Join-Path $Root $wsRel))) {
            $bytes = Get-LocalBytes $wsRel
        } elseif ($remoteShas.ContainsKey($rp)) {
            $r = Invoke-Gh @('api', "/repos/$Owner/$Repo/git/blobs/$($remoteShas[$rp])", '--jq', '.content')
            if ($r.rc -ne 0) { throw "manifest blob fetch failed for ${rp}: $($r.text)" }
            $bytes = [Convert]::FromBase64String(($r.text -replace '\s', ''))
        } else { throw "manifest: no source for $rp" }
        $sha256 = [BitConverter]::ToString(
            ([System.Security.Cryptography.SHA256CryptoServiceProvider]::Create()).ComputeHash($bytes)
        ).Replace('-', '').ToLower()
        [void]$sb.AppendLine(('| `{0}` | {1} | `{2}` | {3} |' -f $rp, $bytes.Length, $sha256, (ConvertTo-Class $rp)))
    }
    $pending = Join-Path $tmpDir 'MANIFEST.pending.md'
    [IO.File]::WriteAllText($pending, $sb.ToString(), (New-Object Text.UTF8Encoding($false)))
    if ((Get-BlobSha ([IO.File]::ReadAllBytes($pending))) -ne $remoteShas[$manifestName]) {
        Invoke-Push @(@{ path = $manifestName; bytes = [IO.File]::ReadAllBytes($pending) })
        Log 'MANIFEST.md updated on GitHub'
    }
}

# ---- stash retention ----------------------------------------------------------------
# Stashes exist as recovery insurance, not archives: prune after 30 days.
function Remove-StaleStash {
    $stashRoot = Join-Path $logDir 'stash'
    if (-not (Test-Path -LiteralPath $stashRoot)) { return 0 }
    $cutoff = (Get-Date).AddDays(-30)
    $n = 0
    foreach ($d in (Get-ChildItem -LiteralPath $stashRoot -Directory)) {
        if ($d.LastWriteTime -lt $cutoff) { Remove-Item -LiteralPath $d.FullName -Recurse -Force; $n++ }
    }
    return $n
}

# ---- fresh-client drill ------------------------------------------------------------
function Invoke-Drill {
    # isolated subdir: never touch other temp files that share $tmpDir
    $work = Join-Path $tmpDir 'drill'
    if (Test-Path -LiteralPath $work) { Remove-Item -LiteralPath $work -Recurse -Force }
    New-Item -ItemType Directory -Path $work -Force | Out-Null
    if (-not (Test-Path -LiteralPath $tmpDir)) { New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null }
    $tgz = Join-Path $work 'snapshot.tgz'
    # cmd-level redirection keeps gh's binary stdout byte-perfect (PS pipelines would decode it)
    $shim = Join-Path $work 'dl.cmd'
    [IO.File]::WriteAllText($shim, "@echo off`r`ngh api ""/repos/$Owner/$Repo/tarball/$Branch"" > ""$tgz""`r`n", [Text.Encoding]::ASCII)
    & cmd /c $shim 2>&1 | Out-Null
    if (-not (Test-Path -LiteralPath $tgz) -or (Get-Item -LiteralPath $tgz).Length -lt 100) { throw 'drill tarball download failed' }
    $ex = Join-Path $work 'x'
    New-Item -ItemType Directory -Path $ex -Force | Out-Null
    & tar -xzf $tgz -C $ex
    if ($LASTEXITCODE -ne 0) { throw 'drill tar extraction failed' }
    $inner = Get-ChildItem -LiteralPath $ex -Directory | Select-Object -First 1

    # parse manifest rows from the extracted copy itself
    $rows = 0; $fails = @(); $covered = @{}
    foreach ($line in (Get-Content -LiteralPath (Join-Path $inner.FullName $manifestName))) {
        if ($line -notmatch '^\|\s*`(.+?)`\s*\|\s*(\d+)\s*\|\s*`([0-9a-f]{64})`\s*\|') { continue }
        $rows++
        $rel = $Matches[1]; $want = $Matches[3]; $covered[$rel] = $true
        $p = Join-Path $inner.FullName ($rel -replace '/', '\')
        if (-not (Test-Path -LiteralPath $p)) { $fails += "$rel missing"; continue }
        if ((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower() -ne $want) { $fails += "$rel hash mismatch" }
    }
    if ($rows -eq 0) { throw 'drill: no manifest rows parsed' }
    # coverage: every tree file except the manifest itself must be a manifest row
    $all = @(Get-ChildItem -LiteralPath $inner.FullName -Recurse -File | ForEach-Object { $_.FullName.Substring($inner.FullName.Length + 1) -replace '\\', '/' })
    $extra = @($all | Where-Object { ($_ -ne $manifestName) -and (-not $covered.ContainsKey($_)) })
    foreach ($x in $extra) { $fails += "not in manifest: $x" }
    if ($fails.Count) { throw ("drill FAILED ({0}): {1}" -f $fails.Count, ($fails -join '; ')) }
    Log ("DRILL PASS: tarball audit OK - {0} manifest rows verified, {1} tree files, coverage complete" -f $rows, $all.Count)
}

# ---- scheduled task ----------------------------------------------------------------
function Install-SyncTask {
    # Hourly: with multiple workspaces/devices syncing to the same repo, short
    # cadence keeps drift windows small; races resolve via fast-forward rejection.
    $name = 'OpenCodeConfig-Sync'
    try { $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 3650) }
    catch {
        Log "cmdlet trigger unsupported ($($_.Exception.Message)); trying minimal interval form"
        $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Hours 1)
    }
    # space-free launcher: Task Scheduler /TR handling of quoted spaced paths is brittle
    $launcher = Join-Path $logDir 'run-sync.cmd'
    [IO.File]::WriteAllText($launcher, "@echo off`r`npowershell -NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Mode Sync`r`n", [Text.Encoding]::ASCII)
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 30) -MultipleInstances IgnoreNew
    try {
        Register-ScheduledTask -TaskName $name -Action (New-ScheduledTaskAction -Execute $launcher -WorkingDirectory $Root) `
            -Trigger $trigger -Settings $settings `
            -Description 'Hourly two-way sync of OpenCode workspace tooling with neohiro/opencode-config' -Force | Out-Null
        Log "scheduled task '$name' registered (hourly, catch-up on missed runs)"
    } catch {
        Log "Register-ScheduledTask failed ($($_.Exception.Message)); falling back to schtasks"
        schtasks /Create /F /SC HOURLY /MO 1 /TN $name /TR "$launcher" | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'task registration failed via schtasks as well' }
        Log "scheduled task '$name' registered via schtasks"
    }
}

# ====================================================================================
try {
    if ($InstallTask) { Install-SyncTask; exit 0 }

    if ((Invoke-Gh @('auth', 'status')).rc -ne 0) { Log 'gh not authenticated; aborting'; exit 2 }
    if (-not (Test-Path -LiteralPath $Root)) { Log "workspace root not found: $Root"; exit 2 }

    $remote = Get-RemoteShas
    $managed = Get-Managed

    if ($Mode -eq 'Drill') { Invoke-Drill; exit 0 }

    # classify differences
    $toPush = @(); $toPull = @(); $same = 0
    foreach ($m in $managed) {
        $lp = Join-Path $Root $m.ws
        $lExists = Test-Path -LiteralPath $lp
        $rSha = $remote[$m.repo]
        if ($lExists -and -not $rSha) {
            $toPush += @{ path = $m.repo; bytes = Get-LocalBytes $m.ws }
        } elseif ($lExists -and $rSha) {
            if ((Get-BlobSha (Get-LocalBytes $m.ws)) -ne $rSha) { $toPush += @{ path = $m.repo; bytes = Get-LocalBytes $m.ws } } else { $same++ }
        } elseif ((-not $lExists) -and $rSha) {
            $toPull += [pscustomobject]@{ repo = $m.repo; sha = $rSha }
        }
    }
    # remote-driven extras inside managed namespaces (added from another client)
    foreach ($rp in $remote.Keys) {
        if (ConvertTo-WsPath $rp) {
            if ((-not ($managed.repo -contains $rp)) -and (-not (Test-Path -LiteralPath (Join-Path $Root (ConvertTo-WsPath $rp))))) {
                $toPull += [pscustomobject]@{ repo = $rp; sha = $remote[$rp] }
            }
        }
    }

    if ($Mode -eq 'Verify') {
        if ($toPush.Count -or $toPull.Count) {
            foreach ($t in $toPush) { Log "DRIFT push-pending: $($t.path)" }
            foreach ($t in $toPull) { Log "DRIFT restore-pending: $($t.repo)" }
            exit 3
        }
        Log ("VERIFY CLEAN: {0} managed files byte-identical" -f $same)
        exit 0
    }

    if ($Mode -eq 'Restore') {
        $n = 0
        foreach ($m in $managed) {
            if ($remote.ContainsKey($m.repo)) {
                $lp = Join-Path $Root $m.ws
                $lExists = Test-Path -LiteralPath $lp
                $needs = (-not $lExists) -or ((Get-BlobSha (Get-LocalBytes $m.ws)) -ne $remote[$m.repo])
                if ($needs) {
                    if ($lExists) { Save-RestoreStash $m.ws }
                    if (Invoke-Pull $m.repo $remote[$m.repo] -Overwrite) { $n++ }
                }
            }
        }
        foreach ($rp in $remote.Keys) {
            $wsRel = ConvertTo-WsPath $rp
            if ($wsRel -and (-not ($managed.repo -contains $rp))) {
                $lp = Join-Path $Root $wsRel
                if (Test-Path -LiteralPath $lp) { Save-RestoreStash $wsRel }
                if (Invoke-Pull $rp $remote[$rp] -Overwrite) { $n++ }
            }
        }
        Log ("RESTORE complete: {0} file(s) written from GitHub to {1}; drifted locals stashed under {2}\stash" -f $n, $Root, $logDir)
        exit 0
    }

    # Mode = Sync
    $changed = 0
    if ($toPush.Count) {
        $script:lastPushed = $toPush.Count
        Invoke-SyncPush $toPush
        $changed += $script:lastPushed
        Log ("PUSHED {0} file(s) to GitHub" -f $script:lastPushed)
    }
    if ($toPull.Count) {
        $n = 0
        foreach ($t in $toPull) { if (Invoke-Pull $t.repo $t.sha -Overwrite) { $n++ } }
        $changed += $n
        Log ("RESTORED {0} remote-only file(s) to workspace" -f $n)
    }
    $remote = Get-RemoteShas          # reflect any payload push
    Update-Manifest $remote           # regenerates ledger; pushes only when changed
    $remote = Get-RemoteShas          # reflect possible manifest push
    Invoke-Drill                      # fresh-client audit against what GitHub actually serves
    $pruned = Remove-StaleStash
    if ($pruned) { Log ("stash retention: pruned {0} dir(s) older than 30 days" -f $pruned) }

    if ($changed) { Log ("SYNC COMPLETE: {0} change(s) processed" -f $changed) }
    else { Log 'SYNC COMPLETE: already up to date' }
    exit 0
} catch {
    Log ("FATAL [{0}]: {1}" -f $Mode, $_.Exception.Message)
    $frames = ($_ | Select-Object -ExpandProperty ScriptStackTrace -ErrorAction SilentlyContinue)
    if ($frames) { foreach ($ln in (($frames -split "`n") | Select-Object -First 2)) { Log "  at $ln" } }
    exit 1
} finally {
    $script:mutex.ReleaseMutex()
    $script:mutex.Dispose()
}
