function Commit-Files {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory)][string]$Repo,
        [Parameter(Mandatory)][string]$Message,
        [Parameter(Mandatory)][array]$Changes,
        [string]$Branch = "main",
        [string]$Owner = "neohiro",
        [int]$Retries = 3,
        [switch]$NoOcTag,
        [switch]$NoAgentIdentity
    )

    # Validate gh CLI availability upfront
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
        throw "gh CLI not found in PATH. Install from https://cli.github.com/"
    }

    # Validate Owner/Repo format (GitHub naming rules)
    if ($Owner -notmatch '^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$') {
        throw "Invalid Owner '$Owner': must match GitHub username/org pattern"
    }
    if ($Repo -notmatch '^[a-zA-Z0-9_.-]+$') {
        throw "Invalid Repo '$Repo': must match GitHub repository pattern"
    }
    if ($Branch -notmatch '^[\w/.-]+$') {
        throw "Invalid Branch '$Branch': contains disallowed characters"
    }

    # Validate Changes array structure
    if ($Changes.Count -eq 0) { throw "Changes array cannot be empty" }
    foreach ($c in $Changes) {
        if (-not $c.ContainsKey("path") -or [string]::IsNullOrWhiteSpace($c.path)) {
            throw "Every change entry must have a non-empty 'path' key"
        }
        if (-not $c.delete -and -not $c.ContainsKey("content") -and -not $c.ContainsKey("bytes")) {
            throw "Change entry for '$($c.path)' must have 'content' or 'bytes' (or 'delete'=$true)"
        }
    }

    $tmpDir = Join-Path $env:TEMP "opencode"
    if (-not (Test-Path -LiteralPath $tmpDir)) { New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null }
    $tmp = Join-Path $tmpDir ("ghapi-$PID-" + [guid]::NewGuid().ToString("N") + ".json")

    function Cleanup {
        if ($tmp -and (Test-Path -LiteralPath $tmp)) {
            Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
        }
    }
    try {

    # Validate gh auth before any API calls — capture exit code immediately to avoid
    # stale $LASTEXITCODE pollution from prior commands in the same session.
    $null = & gh auth status 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "gh CLI not authenticated. Run 'gh auth login' first."
    }

    # Transient = worth retrying. Everything else fails fast.
    function Test-Transient([string]$err) {
        $err -match 'HTTP 5\d\d' -or
        $err -match 'rate limit' -or
        $err -match 'timed? ?out|connection|Could not resolve|SSL|EOF|empty stream'
    }

    function Invoke-GhApi {
        param([string[]]$GhArgs)
        for ($i = 0; ; $i++) {
            # EAP=Continue locally so merged stderr (2>&1) never becomes terminating under caller's -ErrorActionPreference Stop
            $prevEap = $ErrorActionPreference; $ErrorActionPreference = "Continue"
            try { $out = & gh api @GhArgs 2>&1 } finally { $ErrorActionPreference = $prevEap }
            if ($LASTEXITCODE -eq 0) { return (($out | Out-String).Trim()) }
            $err = ($out | Out-String)
            if ($i -ge $Retries -or -not (Test-Transient $err)) {
                throw "gh api failed ($($GhArgs -join ' ')): $($err.Trim())"
            }
            $delay = [Math]::Pow(2, $i) * 2 + (Get-Random -Maximum 1.5)
            Write-Warning "transient failure, retry $($i+1)/$Retries in $([int]$delay)s"
            Start-Sleep -Seconds $delay
        }
    }

    function ApiIn([string]$method, [string]$endpoint, [string]$json) {
        # BOM-less UTF-8: preserves non-ASCII messages (Ascii corrupts them, UTF8-PS adds a BOM GitHub may reject)
        [IO.File]::WriteAllText($tmp, $json, (New-Object Text.UTF8Encoding($false)))
        Invoke-GhApi @("-X", $method, "/repos/$Owner/$Repo/$endpoint", "--input", $tmp)
    }

    # Dry-run gate: pure-local plan summary, zero network mutations on -WhatIf / -Confirm
    if (-not $NoOcTag -and $Message -notmatch '\[oc\]') {
        # Agent-session marker: CI runs soft (no failure email) for these pushes
        $Message = "$Message [oc]"
    }
    $plan = foreach ($c in $Changes) {
        if ($c.delete) { "[delete] $($c.path)" }
        elseif ($c.ContainsKey("bytes")) { "[write] $($c.path) ($($c.bytes.Length) bytes)" }
        else { "[write] $($c.path) ($($c.content.Length) chars)" }
    }
    if (-not $PSCmdlet.ShouldProcess("$Owner/$Repo",
        "commit $($Changes.Count) file(s) to branch '$Branch':`n$($plan -join "`n")")) { return }

    # Structural API calls: fetch current branch head + commit to get the base tree.
    # These are unavoidable even for a single-change commit; they must succeed
    # before we can build the new tree.
    $ref = Invoke-GhApi @("/repos/$Owner/$Repo/git/ref/heads/$Branch") | ConvertFrom-Json
    $commitSha = $ref.object.sha
    # Defensive: follow an annotated tag to its underlying commit.
    # This guards against a non-standard default-branch setup or mistaken tag-as-branch use.
    if ($ref.object.type -eq 'tag') {
        $tagObj = Invoke-GhApi @("/repos/$Owner/$Repo/git/tags/$commitSha") | ConvertFrom-Json
        $commitSha = $tagObj.object.sha
    }
    $commitObj = Invoke-GhApi @("/repos/$Owner/$Repo/git/commits/$commitSha") | ConvertFrom-Json
    $baseTree = $commitObj.tree.sha

    # Validate and encode all changes; reject oversized blobs before any blob/tree/commit API calls.
    $entries = @()
    foreach ($c in $Changes) {
        if ($c.delete) {
            $entries += @{ path = $c.path; mode = "100644"; type = "blob"; sha = $null }
            continue
        }
        if ($c.ContainsKey("bytes")) {
            $b64 = [Convert]::ToBase64String($c.bytes)
            $byteCount = $c.bytes.Length
        } else {
            $utf8Bytes = [Text.Encoding]::UTF8.GetBytes($c.content)
            $b64 = [Convert]::ToBase64String($utf8Bytes)
            $byteCount = $utf8Bytes.Length
        }
        # GitHub's blob limit is 50 MB for the stored object (base64-encoded payload).
        # The base64 string length is the on-wire / on-server payload size for the blob POST.
        if ($byteCount -gt 52428800 -or $b64.Length -gt 52428800) {
            throw "File '$($c.path)' is too large: raw=$byteCount bytes, blob=$($b64.Length) bytes (limit 50 MB). Use Git LFS or split the content."
        }
        $resp = ApiIn "POST" "git/blobs" (@{ content = $b64; encoding = "base64" } | ConvertTo-Json)
        $blobSha = ($resp | ConvertFrom-Json).sha
        if (-not $blobSha) { throw "Blob creation failed for $($c.path): $resp" }
        $entries += @{ path = $c.path; mode = "100644"; type = "blob"; sha = $blobSha }
    }
    if (-not $entries) { throw "No changes supplied for ${Owner}/${Repo}" }

    $treeResp = ApiIn "POST" "git/trees" (@{ base_tree = $baseTree; tree = $entries } | ConvertTo-Json -Depth 2)
    $newTree = ($treeResp | ConvertFrom-Json).sha
    if (-not $newTree) { throw "Tree creation failed for ${Repo}: $treeResp" }

    # 3. commit + update ref
    $body = @{ message = $Message; tree = $newTree; parents = @($commitSha) }
    if (-not $NoAgentIdentity) {
        # Git-level agent marker: survives any push transport, lets CI triage
        # distinguish agent commits from human ones without relying on tags.
        $agent = @{ name = "OpenCode Agent"; email = "opencode-agent@users.noreply.github.com" }
        $body.author = $agent
        $body.committer = $agent
    }
    $commitResp = ApiIn "POST" "git/commits" ($body | ConvertTo-Json -Depth 5)
    $newCommit = ($commitResp | ConvertFrom-Json).sha
    if (-not $newCommit) { throw "Commit creation failed for ${Repo}: $commitResp" }

    # Ref update must atomically advance the branch from the parent commit we
    # built the tree on. Two concurrent commits sharing the same parent produce
    # a 422 ("Update is not a fast forward") on the loser. Retry by rebuilding
    # the tree on the new parent (cheap: blobs already uploaded, only tree+commit
    # need re-creation). Loop runs up to $Retries times total (first attempt + retries).
    $parentSha = $commitSha
    for ($refAttempt = 0; $refAttempt -lt $Retries; $refAttempt++) {
        $refUpdateBody = @{ sha = $newCommit; force = $false } | ConvertTo-Json
        [IO.File]::WriteAllText($tmp, $refUpdateBody, (New-Object Text.UTF8Encoding($false)))
        $patchOut = & gh api -X PATCH "/repos/$Owner/$Repo/git/refs/heads/$Branch" --input $tmp 2>&1
        $patchCode = $LASTEXITCODE
        if ($patchCode -eq 0) { break }
        $errMsg = $patchOut.Trim()
        if ($patchCode -ne 422 -and $patchCode -ne 409) {
            throw "gh api failed (-X PATCH /repos/$Owner/$Repo/git/refs/heads/$Branch) [$patchCode]: $errMsg"
        }
        if ($refAttempt -ge $Retries - 1) {
            throw "Ref update lost fast-forward race $Retries times; aborting: $errMsg"
        }
        Write-Warning "ref fast-forward lost (HTTP $patchCode), rebuilding tree on new parent (attempt $($refAttempt+1)/$Retries)"
        $newRef = Invoke-GhApi @("/repos/$Owner/$Repo/git/ref/heads/$Branch") | ConvertFrom-Json
        $newParent = $newRef.object.sha
        if ($newParent -eq $parentSha) { throw "Ref did not advance despite conflict; aborting" }
        $parentSha = $newParent
        $newCommitObj = Invoke-GhApi @("/repos/$Owner/$Repo/git/commits/$newParent") | ConvertFrom-Json
        $rebuiltTree = ApiIn "POST" "git/trees" (@{ base_tree = $newCommitObj.tree.sha; tree = $entries } | ConvertTo-Json -Depth 2) | ConvertFrom-Json
        $rebuildCommit = ApiIn "POST" "git/commits" (@{ message = $Message; tree = $rebuiltTree.sha; parents = @($newParent) } | ConvertTo-Json -Depth 5) | ConvertFrom-Json
        $newCommit = $rebuildCommit.sha
        if (-not $newCommit) { throw "Rebuild commit failed: $rebuildCommit" }
    }
    Write-Output "COMMITTED ${Owner}/${Repo} -> $newCommit ($($entries.Count) files)"
    } finally { Cleanup }
}
