# batch_privacy.py - Privacy audit fixes for neohiro & frenzypenguin-media
# Single-pass: safe to re-run; idempotent; skips already-fixed files.
# Run:  python batch_privacy.py [--dry-run]
"""Orchestrator for the privacy audit fix batch.

All string transformations live in privacy_transforms.py so they can be
unit-tested in isolation. This module wires them to files, runs the live
verification toolchain, and deploys staged artifacts.

Re-running is safe — every transform is idempotent. Use --dry-run to
preview changes without writing.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

import privacy_transforms as pt

ROOT = os.path.dirname(os.path.abspath(__file__))
UTF8 = "utf-8"

# Parse CLI args before anything else so dry_run is available in the body.
_parser = argparse.ArgumentParser(description="Privacy audit fix batch.")
_parser.add_argument(
    "--dry-run", action="store_true",
    help="preview changes without writing any files",
)
_args = _parser.parse_args()
DRY_RUN = _args.dry_run


# ---------------------------------------------------------------------------
# Filesystem helpers
# ---------------------------------------------------------------------------

def rewrite(path: str, fn, *, encoding: str = UTF8) -> bool:
    """Apply fn to the file at path. No-op if fn returns the same content.

    Returns True if a write actually happened (or would have under --dry-run)."""
    if not os.path.isfile(path):
        print(f"  SKIP {path} (not found or not a file)")
        return False
    try:
        with open(path, "r", encoding=encoding, newline="") as f:
            old = f.read()
    except UnicodeDecodeError:
        print(f"  SKIP {os.path.relpath(path, ROOT)} (encoding error)")
        return False
    new = fn(old)
    if new == old:
        print(f"  OK   {os.path.relpath(path, ROOT)} (no change)")
        return False
    if DRY_RUN:
        print(f"  DRY  {os.path.relpath(path, ROOT)} (would update)")
        return True
    with open(path, "w", encoding=encoding, newline="") as f:
        f.write(new)
    print(f"  FIX  {os.path.relpath(path, ROOT)}")
    return True


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

print("=" * 60)
print("batch_privacy.py  -  privacy audit fixes")
print("=" * 60)


def section(title: str) -> None:
    print("\n" + title)
    print("-" * 60)


changes: list[str] = []


# ---------------------------------------------------------------------------
# #1 - drop the agent-commits row from stats
# ---------------------------------------------------------------------------
section("[#1] Drop agent-commit row from update_stats.py and stats.svg")

STATS_PY = os.path.join(ROOT, "profile-repo", "update_stats.py")
STATS_SVG = os.path.join(ROOT, "profile-repo", "stats.svg")

rewrite(STATS_PY, pt.fix_stats_py)
rewrite(STATS_SVG, pt.fix_stats_svg)
changes.append("#1 stats.svg + update_stats.py: agent-commit row removed")

# ---------------------------------------------------------------------------
# #2 - remove vercel.app third-party stats card from profile README
# ---------------------------------------------------------------------------
section("[#2] Vercel stats card from profile/README.md")

PROFILE_README = os.path.join(ROOT, "profile", "README.md")
rewrite(PROFILE_README, pt.fix_profile_readme)
changes.append("#2 vercel.app card removed from profile/README.md")

# ---------------------------------------------------------------------------
# #3 - harden outbound sponsor links
# ---------------------------------------------------------------------------
section("[#3] Outbound link hardening (rel attributes)")

for path in (
    PROFILE_README,
    os.path.join(ROOT, "profile-repo", "README.md"),
    os.path.join(ROOT, "org-profile-readme.md"),
    os.path.join(ROOT, "pages-site", "index.html"),
    os.path.join(ROOT, "frenzypenguin-media-site", "index.html"),
):
    rewrite(path, pt.harden_links)
changes.append(f"#3 sponsor/patreon/linktree links hardened with rel={pt.REL_NEEDED}")

# ---------------------------------------------------------------------------
# #4 - replace shields.io star-count badges with inline text
# ---------------------------------------------------------------------------
section("[#4] Replace shields.io star badges with inline text")

for path in (
    PROFILE_README,
    os.path.join(ROOT, "profile-repo", "README.md"),
    os.path.join(ROOT, "org-profile-readme.md"),
):
    rewrite(path, pt.strip_shields)
changes.append("#4 img.shields.io star badges replaced with inline text")

# ---------------------------------------------------------------------------
# #5 - remove api.github.com preconnect from all site HTML
# ---------------------------------------------------------------------------
section("[#5] Remove api.github.com preconnect from all site HTML")

for site in ("pages-site", "frenzypenguin-media-site"):
    site_dir = os.path.join(ROOT, site)
    if not os.path.isdir(site_dir):
        continue
    for f in os.listdir(site_dir):
        full = os.path.join(site_dir, f)
        if f.endswith(".html") and os.path.isfile(full):
            rewrite(full, pt.fix_preconnect)
changes.append("#5 api.github.com preconnect removed from all site HTML files")

# ---------------------------------------------------------------------------
# #6 - remove live GitHub API fetch (main.js, index.html, per-repo HTML)
# ---------------------------------------------------------------------------
section("[#6] Remove live GitHub API fetch (main.js, index.html, per-repo HTML)")

PAGES_MAIN = os.path.join(ROOT, "pages-site", "main.js")
rewrite(PAGES_MAIN, pt.fix_pages_main)

pages_dir = os.path.join(ROOT, "pages-site")
if os.path.isdir(pages_dir):
    for f in os.listdir(pages_dir):
        full = os.path.join(pages_dir, f)
        if f.endswith(".html") and f != "index.html" and os.path.isfile(full):
            rewrite(full, pt.fix_per_repo_html)

rewrite(os.path.join(ROOT, "pages-site", "index.html"), pt.fix_index_html)
rewrite(os.path.join(ROOT, "frenzypenguin-media-site", "index.html"), pt.fix_fp_index_html)
changes.append("#6 live GitHub API fetch removed from main.js, index.html, per-repo HTML, fp-media index")

# ---------------------------------------------------------------------------
# #7 - strip sensitive fields from repos.json
# ---------------------------------------------------------------------------
section("[#7] Strip stargazers_count/forks_count/pushed_at from repos.json")

FP_REPOS = os.path.join(ROOT, "frenzypenguin-media-site", "repos.json")
rewrite(FP_REPOS, pt.fix_repos_json)
changes.append("#7 repos.json: stargazers/forks/pushed_at removed")

# ---------------------------------------------------------------------------
# #8 - remove sessionStorage cache from shared core.js
# ---------------------------------------------------------------------------
section("[#8] Remove sessionStorage cache from shared core.js")

CORE_JS = os.path.join(ROOT, "shared", "core.js")
rewrite(CORE_JS, pt.fix_core_js)
changes.append("#8 sessionStorage cache removed from shared core.js")

# ---------------------------------------------------------------------------
# #9 - remove auto-resume entry from repos.json
# ---------------------------------------------------------------------------
section("[#9] Remove auto-resume entry from repos.json")

rewrite(FP_REPOS, pt.fix_repos_no_autorename)
changes.append("#9 auto-resume entry removed from repos.json")

# ---------------------------------------------------------------------------
# #11 - pin ExploitProtection XML/asset download to release tag
# ---------------------------------------------------------------------------
section(f"[#11] Pin ExploitProtection download URLs to {pt.XP_RELEASE_TAG}")

XP_PY = os.path.join(ROOT, "repos", "ExploitProtection", "ExploitProtection.PY")
rewrite(XP_PY, pt.fix_xp_py)
changes.append(f"#11 ExploitProtection download URLs pinned to {pt.XP_RELEASE_TAG} release tag")

# ---------------------------------------------------------------------------
# #15 - split ExploitProtection LICENSE into MIT (code) + CC-BY-SA (data)
# ---------------------------------------------------------------------------
section("[#15] Split ExploitProtection LICENSE into MIT (code) + CC BY-SA (data)")

XP_LICENSE = os.path.join(ROOT, "repos", "ExploitProtection", "LICENSE")
STAGED = os.path.join(ROOT, "batch_privacy_staged")
os.makedirs(STAGED, exist_ok=True)

for fname, content in (
    ("LICENSE-CODE", pt.MIT_LICENSE),
    ("LICENSE-DATA", pt.CC_DATA_LICENSE),
):
    staged_path = os.path.join(STAGED, fname)
    if os.path.exists(staged_path):
        print(f"  OK   {os.path.relpath(staged_path, ROOT)} (already staged)")
        continue
    if DRY_RUN:
        print(f"  DRY  {os.path.relpath(staged_path, ROOT)} (would stage)")
        continue
    with open(staged_path, "w", encoding=UTF8, newline="") as f:
        f.write(content)
    print(f"  STAGED {os.path.relpath(staged_path, ROOT)}")

rewrite(XP_LICENSE, pt.fix_xp_license)
changes.append("#15 ExploitProtection LICENSE: split into MIT (code) + CC BY-SA (data)")

# ---------------------------------------------------------------------------
# #16 - expand extension warnings in windows README
# ---------------------------------------------------------------------------
section("[#16] Expand extension warning in windows README")

WIN_README = os.path.join(ROOT, "repos", "windows", "README.md")
rewrite(WIN_README, pt.fix_win_readme)
changes.append("#16 windows README: extension warning expanded to all modified types")

# ---------------------------------------------------------------------------
# #18 - remove MAPSReporting/SubmitSamplesConsent from windows_hardening.cmd
# ---------------------------------------------------------------------------
section("[#18] Remove MAPSReporting telemetry from windows_hardening.cmd")

WIN_CMD = os.path.join(ROOT, "repos", "windows", "windows_hardening.cmd")
rewrite(WIN_CMD, pt.fix_win_cmd)
changes.append("#18 windows_hardening.cmd: MAPSReporting telemetry removed")

# ---------------------------------------------------------------------------
# #20 - remove sudo passwd root from ubuntu README
# ---------------------------------------------------------------------------
section("[#20] Remove sudo passwd root from ubuntu README")

UBUNTU_README = os.path.join(ROOT, "repos", "ubuntu", "README.md")
rewrite(UBUNTU_README, pt.fix_ubuntu_readme)
changes.append("#20 ubuntu README: 'sudo passwd root' removed")

# ---------------------------------------------------------------------------
# #22 - fix ubuntusocks.sh
# ---------------------------------------------------------------------------
section("[#22] Fix ubuntusocks.sh (drop fast_open, drop password echo)")

UBUNTUSOCKS = os.path.join(ROOT, "repos", "ubuntu", "ubuntusocks.sh")
rewrite(UBUNTUSOCKS, pt.fix_socks)
changes.append("#22 ubuntusocks.sh: fast_open + password echo removed")

# ---------------------------------------------------------------------------
# #23 - gate disable_ipv6 behind --disable-ipv6 flag
# ---------------------------------------------------------------------------
section("[#23] Gate disable_ipv6 behind --disable-ipv6 flag")

for script in ("ubuntuinstall.sh", "ubuntuinstallserver.sh"):
    path = os.path.join(ROOT, "repos", "ubuntu", script)
    if os.path.exists(path):
        rewrite(path, pt.fix_ubuntu_install_script)
changes.append("#23 ubuntu scripts: disable_ipv6 gated behind --disable-ipv6 flag")

# ---------------------------------------------------------------------------
# #24 - replace placeholder password in SHADOWSOCKS-LIBEV.md
# ---------------------------------------------------------------------------
section("[#24] Replace placeholder password in SHADOWSOCKS-LIBEV.md")

SS_MD = os.path.join(ROOT, "repos", "ubuntu", "SHADOWSOCKS-LIBEV.md")
rewrite(SS_MD, pt.fix_ss_md)
changes.append("#24 SHADOWSOCKS-LIBEV.md: placeholder password replaced")

# ---------------------------------------------------------------------------
# #36 - remove SystemMonitor-SpoofExample.exe
# ---------------------------------------------------------------------------
section("[#36] Remove SystemMonitor-SpoofExample.exe")

SM_EXE = os.path.join(ROOT, "repos", "SystemMonitor", "SystemMonitor-SpoofExample.exe")
if os.path.exists(SM_EXE):
    bak = SM_EXE + ".bak"
    if not os.path.exists(bak):
        if not DRY_RUN:
            shutil.move(SM_EXE, bak)
        print(f"  MOVED {os.path.relpath(SM_EXE, ROOT)} -> .bak")
    else:
        print(f"  OK   {os.path.relpath(SM_EXE, ROOT)} (already moved)")
else:
    print(f"  SKIP {os.path.relpath(SM_EXE, ROOT)} (not found)")
changes.append("#36 SystemMonitor-SpoofExample.exe moved to .bak")

# ---------------------------------------------------------------------------
# #37 - rename SystemMonitor config.json -> config.example.json
# ---------------------------------------------------------------------------
section("[#37] Stage SystemMonitor config.json rename")

SM_CFG = os.path.join(ROOT, "repos", "SystemMonitor", "config.json")
if os.path.exists(SM_CFG):
    bak = SM_CFG + ".staged"
    if not os.path.exists(bak):
        if not DRY_RUN:
            shutil.copy(SM_CFG, bak)
        print(f"  COPIED {os.path.relpath(SM_CFG, ROOT)} -> .staged")
    print("  NOTE: rename config.json -> config.example.json in repo and add config.json to .gitignore")
changes.append("#37 SystemMonitor config.json staged; .gitignore update needed")

# ---------------------------------------------------------------------------
# #41+42 - org-level SECURITY.md, CODE_OF_CONDUCT.md, CONTRIBUTING.md
# ---------------------------------------------------------------------------
section("[#41+42] Stage org-level governance docs")

STAGED_ORG = os.path.join(STAGED, "org-github")
os.makedirs(STAGED_ORG, exist_ok=True)
for fname, content in (
    ("SECURITY.md", pt.SECURITY_MD),
    ("CODE_OF_CONDUCT.md", pt.COC_MD),
    ("CONTRIBUTING.md", pt.CONTRIBUTING_MD),
):
    path = os.path.join(STAGED_ORG, fname)
    if DRY_RUN:
        print(f"  DRY  {os.path.relpath(path, ROOT)} (would stage)")
    else:
        with open(path, "w", encoding=UTF8, newline="") as f:
            f.write(content)
        print(f"  STAGED {os.path.relpath(path, ROOT)}")
changes.append("#41+42 org-level SECURITY.md + CODE_OF_CONDUCT.md + CONTRIBUTING.md staged")

# ---------------------------------------------------------------------------
# #43 - remove 404 release.yml Build Status badges
# ---------------------------------------------------------------------------
section("[#43] Remove 404 release.yml Build Status badges")

REPOS_WITH_BADGE = (
    "BlackGlass", "Calculator", "ClockWidget", "Cripple-NetStrip",
    "dnscrypt-proxy-gui", "DNSLookup", "ExploitProtection",
    "FileManager", "GhostMaze", "Godmode", "GoogleCommand",
    "HoneyScan", "htmlinfo", "LANScan", "metapod", "MoodTracker",
    "MusicPlay", "NetMatrix", "NewsAggregator", "SecondLife",
    "ShadowSocks", "SystemMonitor", "Tetris", "TristarMania",
    "ubuntu", "windows", "ZombieShoot",
)
for repo in REPOS_WITH_BADGE:
    readme = os.path.join(ROOT, "repos", repo, "README.md")
    if os.path.exists(readme):
        rewrite(readme, pt.remove_badges)
changes.append("#43 404 release.yml Build Status badges removed from all repo READMEs")

# ---------------------------------------------------------------------------
# regenerate stats.svg + rebuild sites (live toolchain verification)
# ---------------------------------------------------------------------------
section("[verify] Regenerate stats.svg and rebuild sites")

verify_failures: list[str] = []

def _decode(b: bytes) -> str:
    """Decode a subprocess output buffer using the system locale, with a
    fallback to utf-8 then latin-1.  Avoids UnicodeDecodeError on Windows
    where the subprocess may use cp1252/cp437 while Python expects utf-8."""
    for enc in (UTF8, "cp1252", "latin-1"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            continue
    return b.decode(UTF8, errors="replace")


try:
    r = subprocess.run(
        [sys.executable, "update_stats.py"],
        capture_output=True, timeout=60,
        cwd=os.path.join(ROOT, "profile-repo"),
    )
    if r.returncode == 0:
        print(f"  stats.svg regenerated (stdout: {_decode(r.stdout).strip()})")
    else:
        msg = f"update_stats.py exit {r.returncode}: {_decode(r.stderr).strip()}"
        print(f"  FAIL {msg}")
        verify_failures.append(msg)
except subprocess.TimeoutExpired as e:
    msg = f"update_stats.py: timed out after {e.timeout}s"
    print(f"  FAIL {msg}")
    verify_failures.append(msg)
except OSError as e:
    msg = f"update_stats.py: {e}"
    print(f"  FAIL {msg}")
    verify_failures.append(msg)

try:
    r = subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", "build-sites.ps1"],
        capture_output=True, timeout=60, cwd=ROOT,
    )
    if r.returncode == 0:
        print(f"  Sites rebuilt (stdout: {_decode(r.stdout).strip()})")
    else:
        msg = f"build-sites.ps1 exit {r.returncode}: {_decode(r.stderr).strip()}"
        print(f"  FAIL {msg}")
        verify_failures.append(msg)
except subprocess.TimeoutExpired as e:
    msg = f"build-sites.ps1: timed out after {e.timeout}s"
    print(f"  FAIL {msg}")
    verify_failures.append(msg)
except OSError as e:
    msg = f"build-sites.ps1: {e}"
    print(f"  FAIL {msg}")
    verify_failures.append(msg)

# ---------------------------------------------------------------------------
# DEPLOY staged artifacts -> real target locations
# ---------------------------------------------------------------------------
section("[deploy] Copy staged artifacts to target paths")

deploy_log: list[str] = []


def deploy_file(src_rel: str, dst_abs: str) -> bool:
    src = os.path.join(ROOT, src_rel)
    if not os.path.isfile(src):
        return False
    if DRY_RUN:
        print(f"  DRY  deploy {src_rel} -> {os.path.relpath(dst_abs, ROOT)}")
        return True
    os.makedirs(os.path.dirname(dst_abs), exist_ok=True)
    try:
        with open(src, "r", encoding=UTF8, newline="") as f:
            body = f.read()
    except UnicodeDecodeError:
        print(f"  SKIP {src_rel} (encoding error)")
        return False
    with open(dst_abs, "w", encoding=UTF8, newline="") as f:
        f.write(body)
    deploy_log.append(f"{src_rel} -> {os.path.relpath(dst_abs, ROOT)}")
    print(f"  DEPLOY {src_rel} -> {os.path.relpath(dst_abs, ROOT)}")
    return True


# 1. ExploitProtection LICENSE-CODE and LICENSE-DATA go alongside LICENSE
for fname in ("LICENSE-CODE", "LICENSE-DATA"):
    deploy_file(
        os.path.join("batch_privacy_staged", fname),
        os.path.join(ROOT, "repos", "ExploitProtection", fname),
    )

# 2. Org-level governance docs -> .github/ in both orgs and every repo
ORG_DOCS = ("SECURITY.md", "CODE_OF_CONDUCT.md", "CONTRIBUTING.md")
ORG_DESTINATIONS: list[str] = [
    os.path.join(ROOT, "fp-repo-workflow", ".github"),
    os.path.join(ROOT, "profile-repo", ".github"),
]
repos_root = os.path.join(ROOT, "repos")
if os.path.isdir(repos_root):
    for repo in sorted(os.listdir(repos_root)):
        gh = os.path.join(repos_root, repo, ".github")
        if os.path.isdir(gh):
            ORG_DESTINATIONS.append(gh)
for d in ORG_DESTINATIONS:
    for fname in ORG_DOCS:
        deploy_file(
            os.path.join("batch_privacy_staged", "org-github", fname),
            os.path.join(d, fname),
        )

# 3. SystemMonitor config.json -> config.example.json
SM_CFG_EX = os.path.join(ROOT, "repos", "SystemMonitor", "config.example.json")
SM_GI = os.path.join(ROOT, "repos", "SystemMonitor", ".gitignore")
if os.path.exists(SM_CFG) and not os.path.exists(SM_CFG_EX):
    if DRY_RUN:
        print(f"  DRY  rename config.json -> config.example.json")
    else:
        shutil.copy(SM_CFG, SM_CFG_EX)
        print(f"  RENAME config.json -> config.example.json")
        deploy_log.append("repos/SystemMonitor/config.json -> config.example.json")

# 4. Add config.json to SystemMonitor .gitignore
if os.path.exists(os.path.dirname(SM_GI)):
    if os.path.exists(SM_GI):
        with open(SM_GI, "r", encoding=UTF8, newline="") as f:
            gi = f.read()
    else:
        gi = ""
    if "config.json" not in gi:
        if DRY_RUN:
            print(f"  DRY  +config.json in {os.path.relpath(SM_GI, ROOT)}")
        else:
            with open(SM_GI, "a", encoding=UTF8, newline="") as f:
                if gi and not gi.endswith(("\n", "\r\n", "\r")):
                    f.write("\n")
                f.write("# Local config (use config.example.json as a template)\n")
                f.write("config.json\n")
            print(f"  GITIGNORE +config.json in {os.path.relpath(SM_GI, ROOT)}")
            deploy_log.append("repos/SystemMonitor/.gitignore: +config.json")

# 5. Promote the staged .bak into the actual SpoofExample.exe.bak location
SM_SPOOF_BAK = os.path.join(ROOT, "repos", "SystemMonitor", "SystemMonitor-SpoofExample.exe.bak")
if os.path.exists(SM_EXE) and not os.path.exists(SM_SPOOF_BAK):
    if DRY_RUN:
        print(f"  DRY  rename SpoofExample.exe -> .exe.bak")
    else:
        shutil.move(SM_EXE, SM_SPOOF_BAK)
        print(f"  RENAME SpoofExample.exe -> .exe.bak")
        deploy_log.append("SpoofExample.exe -> SpoofExample.exe.bak")

if deploy_log:
    changes.append(f"deployed {len(deploy_log)} staged artifacts")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
if verify_failures:
    print(f"DONE with {len(verify_failures)} VERIFY FAILURE(S) - {len(changes)} fixes applied")
    for f in verify_failures:
        print(f"  ! {f}")
else:
    print(f"DONE - {len(changes)} fixes applied")
print("=" * 60)
for c in changes:
    print(f"  - {c}")

if verify_failures:
    sys.exit(2)
