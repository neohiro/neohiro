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
    Write-Output ""
    Write-Output "############ $name ############"
    $mirror = "$tmp\$name.git"
    if (Test-Path $mirror) { Remove-Item $mirror -Recurse -Force }
    & git clone --mirror --quiet "https://github.com/neohiro/$name.git" $mirror
    if ($LASTEXITCODE -ne 0) { Write-Output "CLONE FAILED"; continue }
    Set-Location $mirror

    # 1. drop accidental empty tip from earlier run
    $tipMsg = (& git log -1 --format=%s)
    if ($tipMsg -eq "Re-add current release binaries") {
        & git update-ref refs/heads/main "HEAD~1"
        Write-Output "dropped junk tip commit"
    }

    # 2. discover binary paths across history (path extraction via IndexOf)
    $binPaths = New-Object System.Collections.Generic.List[string]
    $sizeMap = @{}
    foreach ($line in (& git rev-list --objects --all)) {
        $i = $line.IndexOf(' ')
        if ($i -lt 0) { continue }
        $sha = $line.Substring(0, $i)
        $path = $line.Substring($i + 1)
        if ($path -match "\.(exe|dll|msi|apk)$") {
            if (-not $binPaths.Contains($path)) { $binPaths.Add($path) }
            continue
        }
        if ($path -notmatch "/" -and $path -notmatch "\.") {
            if (-not $sizeMap.ContainsKey($path)) { $sizeMap[$path] = $sha }
        }
    }
    foreach ($p in $sizeMap.Keys) {
        try {
            $sz = [long](& git cat-file -s $sizeMap[$p])
            if ($sz -gt 500000 -and -not $binPaths.Contains($p)) { $binPaths.Add($p) }
        } catch {}
    }
    Write-Output ("strip list: [" + (($binPaths | Sort-Object) -join "] [") + "]")

    # 3. filter
    $pyArgs = @("-m", "git_filter_repo", "--force", "--invert-paths")
    foreach ($p in ($binPaths | Sort-Object)) { $pyArgs += @("--path", $p) }
    if ($binPaths.Count -gt 0) {
        $out = & python @pyArgs 2>&1 | Select-Object -Last 1
        Write-Output ("filter: " + $out)
    }

    # 4. verify
    $left = 0
    foreach ($line in (& git rev-list --objects --all)) {
        $i = $line.IndexOf(' ')
        if ($i -lt 0) { continue }
        $path = $line.Substring($i + 1)
        if ($binPaths.Contains($path)) { $left++ }
    }
    Write-Output "occurrences left after filter: $left"
    if ($left -gt 0) { Write-Output "!!! FILTER INCOMPLETE - NOT PUSHING !!!"; continue }

    # 5. restore current binaries at tip
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

    # 6. push
    & git push --force "https://github.com/neohiro/$name.git" "refs/heads/main:refs/heads/main" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Write-Output "PUSHED OK" } else { Write-Output "PUSH FAILED" }
}
Write-Output ""
Write-Output "ALL DONE"
