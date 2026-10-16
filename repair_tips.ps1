$env:PATH = "$env:TEMP\opencode\mingit\cmd;" + $env:PATH
$tmp = "$env:TEMP\opencode\rewrite"
$local = "C:\Users\skele\Documents\GitHub Manager\repos"

$targets = [ordered]@{
    "Calculator"     = @("Calculator.exe")
    "LANScan"        = @("LANScan", "LANScan.exe")
    "HoneyScan"      = @("HoneyScan", "HoneyScan.exe")
    "DNSLookup"      = @("DNSLookup", "DNSLookup.exe")
    "SystemMonitor"  = @("SystemMonitor.exe", "SystemMonitor-SpoofExample.exe")
    "Godmode"        = @("Godmode.exe")
    "NewsAgreggator" = @("News.exe")
    "GoogleCommand"  = @("GCom.exe")
}

$failures = @()
foreach ($name in $targets.Keys) {
    Write-Output ""
    Write-Output "############ REPAIR $name ############"
    $mirror = "$tmp\$name.git"
    if (-not (Test-Path $mirror)) { Write-Output "mirror missing, re-cloning"; & git clone --mirror --quiet "https://github.com/neohiro/$name.git" $mirror }
    Set-Location $mirror

    # sanity: parent must have a real tree (more than just binaries)
    $parentFiles = (& git ls-tree -r "HEAD~1" --name-only)
    if ($parentFiles.Count -lt 5) { Write-Output "!!! parent tree looks wrong ($($parentFiles.Count) files) - SKIPPING !!!"; $failures += $name; continue }

    # rebuild tip from good parent + binaries
    & git read-tree "HEAD~1"
    foreach ($p in $targets[$name]) {
        $src = Join-Path $local "$name\$p"
        if (-not (Test-Path $src)) { Write-Output "!!! missing snapshot $src"; $failures += $name; continue }
        $blob = & git hash-object -w $src
        & git update-index --add --cacheinfo "100644,$blob,$p"
    }
    $tree = & git write-tree
    $commit = & git commit-tree $tree -p "HEAD~1" -m "Restore repository contents and current release binaries

The history cleanup commit accidentally replaced the full tree with only the
binary artifacts. This restores all sources, docs and workflows while keeping
the current release binaries at the tip."

    # PRE-PUSH VERIFICATION: inspect the new tree completely
    & git update-ref refs/heads/main $commit
    $newFiles = (& git ls-tree -r main --name-only)
    $expected = $parentFiles.Count + $targets[$name].Count
    Write-Output ("new tree: {0} files (expected ~{1})" -f $newFiles.Count, $expected)
    if ($newFiles.Count -lt $expected) { Write-Output "!!! TREE STILL INCOMPLETE - NOT PUSHING !!!"; $failures += $name; continue }

    & git push --force "https://github.com/neohiro/$name.git" "refs/heads/main:refs/heads/main" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Write-Output "PUSHED OK" } else { Write-Output "PUSH FAILED"; $failures += $name }
}

Write-Output ""
if ($failures) { Write-Output ("FAILURES: " + ($failures -join ", ")) } else { Write-Output "ALL REPAIRS SUCCEEDED" }
