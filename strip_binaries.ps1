$ErrorActionPreference = "Continue"
$env:PATH = "$env:TEMP\opencode\mingit\cmd;" + $env:PATH
$tmp = "$env:TEMP\opencode\rewrite"
$local = "C:\Users\skele\Documents\GitHub Manager\repos"

# repo -> candidate binary paths currently at HEAD (extensionless ELF + exes)
$targets = [ordered]@{
    "LANScan"       = @("LANScan", "LANScan.exe")
    "HoneyScan"     = @("HoneyScan", "HoneyScan.exe")
    "DNSLookup"     = @("DNSLookup", "DNSLookup.exe")
    "SystemMonitor" = @("SystemMonitor.exe", "SystemMonitor-SpoofExample.exe")
    "Godmode"       = @("Godmode.exe")
    "NewsAgreggator"= @("News.exe")
    "GoogleCommand" = @("GCom.exe")
}

foreach ($name in $targets.Keys) {
    Write-Output "############ $name ############"
    $mirror = "$tmp\$name.git"
    if (Test-Path $mirror) { Remove-Item $mirror -Recurse -Force }
    & git clone --mirror --quiet "https://github.com/neohiro/$name.git" $mirror
    if ($LASTEXITCODE -ne 0) { Write-Output "CLONE FAILED"; continue }
    Set-Location $mirror

    # discover every exe-like or large extensionless path across ALL history
    $candidates = & git rev-list --objects --all | ForEach-Object { ($_ -split ' ',2)[1] } |
        Where-Object { $_ -and ($_ -match "\.(exe|dll|msi|apk)$") } | Sort-Object -Unique
    # extensionless top-level entries that are blobs >1MB (catch renamed builds)
    $extless = & git rev-list --objects --all | ForEach-Object { ($_ -split ' ',2)[1] } |
        Where-Object { $_ -and ($_ -notmatch "/" -and $_ -notmatch "\.") } | Sort-Object -Unique
    foreach ($p in $extless) {
        $sz = (& git cat-file -s (& git rev-parse "$($name):$p" 2>$null) 2>$null)
        if (-not $sz) {
            # resolve blob sha directly from rev-list pairs instead
        }
    }
    $binPaths = @($candidates + $targets[$name] | Sort-Object -Unique)
    Write-Output ("binary paths to strip: " + ($binPaths -join ", "))
    Write-Output ("branches: " + ((& git for-each-ref refs/heads --format "%(refname:short)") -join ", "))

    python -m git_filter_repo --force --invert-paths @binPaths 2>&1 | Select-Object -Last 2

    $left = (& git rev-list --objects --all | ForEach-Object { ($_ -split ' ',2)[1] } | Where-Object { $_ -in $binPaths } | Measure-Object).Count
    Write-Output "remaining occurrences in history: $left"

    # restore current binaries from local snapshot as tip commit
    foreach ($p in $targets[$name]) {
        $src = Join-Path $local "$name\$p"
        if (Test-Path $src) {
            $blob = & git hash-object -w $src
            & git update-index --add --cacheinfo "100644,$blob,$p"
        } else { Write-Output "WARN: local snapshot missing $src" }
    }
    $tree = & git write-tree
    $commit = & git commit-tree $tree -p HEAD -m "Re-add current release binaries"
    & git update-ref refs/heads/main $commit

    & git push --force "https://github.com/neohiro/$name.git" "refs/heads/main:refs/heads/main" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Write-Output "PUSHED OK" } else { Write-Output "PUSH FAILED" }
}
Write-Output "ALL DONE"
