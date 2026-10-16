<#
.SYNOPSIS
  Push to a GitHub remote, bypassing Git's credential-helper shell path.

.DESCRIPTION
  STATUS: FALLBACK ONLY. Plain `git push` currently works on this machine with
  the standard configuration:

      git config --global credential.helper "!gh auth git-credential"

  Use that first. Reach for this script only if push starts failing again with
  "could not read Username for 'https://github.com'".

  WHAT WENT WRONG (recorded so the next diagnosis is not repeated)
  --------------------------------------------------------------
  On 2026-10-08 `git push` failed with the error above. The cause was NOT a
  misconfigured helper -- the config really was also wrong at the time, and both
  had to be fixed. But the config alone did not explain it:

    * Git for Windows runs every credential helper through its bundled
      usr/bin/sh.exe.
    * sh.exe started fine, and shell BUILTINS worked. `sh.exe -c "exit 0"`
      returns 0 -- exit is a builtin, so it never forks. Anything that does
      fork failed: the child died with 0xC0000142 (STATUS_DLL_INIT_FAILED) and
      the shell reported "fork: Resource temporarily unavailable".
    * With fork dead, no credential helper could run, so Git fell through to
      an interactive username prompt, which cannot be answered here.

  Ruled out with evidence, not assumption: system resources (9 GB free), stale
  MSYS2 processes (none), Defender process-creation blocks (none in the
  operational log), AppLocker/WDAC (absent), /etc/fstab (normal), ASLR policy
  (Windows defaults), and stdio redirection (fails with and without).

  The failure then stopped on its own. The Defender operational log shows a
  burst of "Antivirus Configuration has changed" events minutes before the
  first failure, so real-time scanning is the likely cause -- but that was NOT
  confirmed, because viewing Defender exclusions requires elevation and this
  session was not elevated. Treat the cause as suspected, not established, and
  re-check Defender if it recurs.

  HOW THIS SCRIPT WORKS
  ---------------------
  Uses GIT_ASKPASS, which Git invokes directly rather than through a shell, so
  it does not depend on fork working. The token is obtained from `gh auth token`
  at call time -- never written to disk, never stored in git config, never
  echoed. Pushing to the *named remote* rather than a raw URL keeps
  remote-tracking refs, so `git status` and `git pull` behave normally.

  A side benefit: because it avoids the shell entirely, it is unaffected by
  whatever breaks fork. That is the reason to keep it around.

  KNOWN LIMITATION: --force-with-lease does NOT work here, verified 2026-10-08.
  These clones have no upstream tracking, so after an amend the lease check
  reports "stale info" and refuses even for a branch you own. -Force therefore
  uses plain --force and refuses main/master outright.

.PARAMETER Remote
  Git remote name (e.g. origin). A named remote is required, not a raw URL:
  pushing to a URL bypasses remote-tracking refs, which breaks `git status`,
  `git pull`, and the branch listings you navigate by.

.PARAMETER Branch
  Branch name to push to (HEAD of the current checkout).

.PARAMETER DryRun
  Report what would happen without writing anything.

.PARAMETER Force
  Use --force. For rewriting your own unmerged PR branch after an amend.

  VERIFIED 2026-10-08: --force-with-lease reports "stale info" and refuses on
  these clones, even with a named remote and a branch that is plainly the
  caller's own. Plain --force is the only option. Verify the branch is yours --
  the script refuses main/master, but nothing can tell you whether someone else
  pushed to a feature branch.

.EXAMPLE
  .\git-push-token.ps1 -Remote origin -Branch fix/foo -DryRun

.EXAMPLE
  .\git-push-token.ps1 -Remote origin -Branch fix/foo -Force

.NOTES
  This is a workaround, not a repair. The real fix is reinstalling or repairing
  Git for Windows so sh.exe works again. Verify with:

      & "C:\Program Files\Git\usr\bin\sh.exe" -c "exit 0"; $LASTEXITCODE

  Expect 0. It currently returns -1073741502.
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$Remote,
  [Parameter(Mandatory)][string]$Branch,
  [switch]$DryRun,
  [switch]$Force
)

$ErrorActionPreference = 'Stop'

Set-Location -LiteralPath (Get-Location).Path

  # Named remote only: a raw URL bypasses tracking refs, which would leave the
  # branch untracked locally and break status/pull. (It also broke --force-with-lease,
  # but that is a separate upstream-tracking limitation, not a URL problem.)
# Capture stderr so a bad remote name produces the message below rather than
# PowerShell terminating on git's own stderr under $ErrorActionPreference='Stop'.
# The temporary 'Continue' is required: 'Stop' turns git's non-zero exit plus
# stderr into a terminating NativeCommandError before $url is ever assigned.
$url = $null
$prevEap = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
try {
  $urlOut = & git remote get-url $Remote 2>&1
  if ($LASTEXITCODE -eq 0) { $url = ($urlOut | Out-String).Trim() }
} finally {
  $ErrorActionPreference = $prevEap
}
if (-not $url) {
  throw "no such remote: '$Remote'. Add it with: git remote add $Remote https://github.com/OWNER/REPO.git"
}
if ($url -notmatch '^https://github\.com/') {
  throw "refusing: $Remote is not a github.com HTTPS remote (got: $url)"
}

# Askpass answers both prompts. Git asks for the username first; GitHub accepts
# any non-empty username when the password is a valid token, so return the
# account name for one prompt and the token for the other.
$account = (& gh api user --jq .login 2>$null | Out-String).Trim()
if (-not $account) { $account = 'x-access-token' }

$askpass = Join-Path $env:TEMP "opencode-git-askpass.cmd"
$askpassBody = @(
  '@echo off',
  "if `"%~1`"==`"`" (echo $account) else (gh auth token)"
) -join "`r`n"
[System.IO.File]::WriteAllText($askpass, $askpassBody + "`r`n")

$pushArgs = @('push')
if ($DryRun) { $pushArgs += '--dry-run' }
if ($Force) {
  # Refuse to force-push the protected default branch; the ruleset blocks
  # non-fast-forward there, and silently clobbering main is never intended.
  $default = (git symbolic-ref --quiet --short refs/remotes/$Remote/HEAD 2>$null)
  if ($Branch -in @('main', 'master')) {
    throw "refusing to force-push $Branch. Changes must go through a pull request."
  }
  $pushArgs += '--force'
}
$pushArgs += @($Remote, "HEAD:refs/heads/$Branch")

$env:GIT_ASKPASS = $askpass
# Fail fast instead of blocking on an interactive prompt that cannot be answered.
$env:GIT_TERMINAL_PROMPT = '0'
try {
  # Empty the helper list: any helper would be spawned via the broken sh.
  & git -c credential.helper= @pushArgs
  $rc = $LASTEXITCODE
} finally {
  Remove-Item Env:\GIT_ASKPASS -ErrorAction SilentlyContinue
  Remove-Item Env:\GIT_TERMINAL_PROMPT -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath $askpass -ErrorAction SilentlyContinue
}

if ($rc -ne 0) { throw "git push failed with exit code $rc" }
Write-Host "pushed HEAD -> $Remote/$Branch" -ForegroundColor Green