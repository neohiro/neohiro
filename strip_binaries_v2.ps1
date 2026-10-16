$ErrorActionPreference = "Stop"
$env:PATH = "$env:TEMP\opencode\mingit\cmd;" + $env:PATH
$tmp = "$env:TEMP\opencode\rewrite"
$local = "C:\Users\skele\Documents\GitHub Manager\repos"

$targets = [ordered]@{
    "LANScan"        = @("LANScan", "LANScan.exe")
    "HoneyScan"      = @("HoneyScan", "HoneyScan.exe")
    "DNSLookup"      = @("DNSLookup", "DNSLookup.exe")
    "SystemMonitor"  = @("SystemMonitor.exe", "SystemMonitor-SpoofExample.exe")
    "Godmode"        = @("Godmode.exe")
    "NewsAgreggator" = @("News.exe")
    "GoogleCommand"  = @("GCom.exe")
}

foreach ($name in $targets.Keys) {
    Write-Output "############ $name ############"
    $mirror = "$tmp\$name.git"
    if (Test-Path $mirror) { Remove-Item $mirror -Recurse -Force }
    & git clone --mirror --quiet "https://github.com/neohiro/$name.git" $mirror
    Set-Location $mirror

    # 1. drop the accidental empty "Re-add" tip from the earlier failed run
    $tipMsg = (& git log -1 --format=%s)
    if ($tipMsg -eq "Re-add current release binaries") {
        & git update-ref refs/heads/main "HEAD~1"
        Write-Output "dropped junk tip commit"
    }

    # 2. discover binary paths across ALL history
    $pairs = & git rev-list --objects --all | ForEach-Object { ($_ -split ' ', 2) }
    $binPaths = New-Object System.Collections.Generic.List[string]
    function Add-Bin([string]$p) {
        if ($p -and -not $binPaths.Contains($p)) { $binPaths.Add($p) }
    }
    foreach ($pair in $pairs) {
        if ($pair.Count -lt 2) { continue }
        $sha = $pair[0]; $path = $pair[1]
        if ($path -match "\.(exe|dll|msi|apk)$") { Add-Bin $path; continue }
        if ($path -notmatch "/" -and $path -notmatch "\.") {
            try {
                $sz = [long](& git cat-file -s $sha 2>$null)
                if ($sz -gt 500000) { Add-Bin $path }
            } catch {}
        }
    }
    Write-Output ("strip list: " + (($binPaths | Sort-Object) -join " | "))

    # 3. filter with explicit per-path args
    $pyArgs = @("-m", "git_filter_repo", "--force", "--invert-paths")
    foreach ($p in ($binPaths | Sort-Object)) { $pyArgs += @("--path", $p) }
    & python @pyArgs 2>&1 | Select-Object -Last 1

    # 4. verify zero occurrences left
    $left = 0
    foreach ($pair in (& git rev-list --objects --all | ForEach-Object { ($_ -split ' ', 2) })) {
        if ($pair.Count -ge 2 -and ($binPaths -contains $pair[1])) { $left++ }
    }
    Write-Output "occurrences left after filter: $left"
    if ($left -gt 0) { Write-Output "!!! FILTER INCOMPLETE - SKIPPING PUSH !!!"; continue }

    # 5. restore current binaries as new tip
    foreach ($p in $targets[$name]) {
        $src = Join-Path $local "$name\$p"
        if (Test-Path $src) {
            $blob = & git hash-object -w $src
            & git update-index --add --cacheinfo "100644,$blob,$p"
        } else { Write-Output "WARN missing snapshot: $src" }
    }
    $tree = & git write-tree
    $commit = & git commit-tree $tree -p HEAD -m "Re-add current release binaries"
    & git update-ref refs/heads/main $commit

    # 6. push once, forced
    & git push --force "https://github.com/neohiro/$name.git" "refs/heads/main:refs/heads/main" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Write-Output "PUSHED OK" } else { Write-Output "PUSH FAILED" }
}
Write-Output "ALL DONE"
