"""Batch: CHANGELOG.md for flagships lacking one + CodeQL badges."""
import subprocess, json, os

TOKEN = None

def gh_raw(repo, path, ref=None):
    url = f"https://api.github.com/repos/neohiro/{repo}/contents/{path}"
    if ref:
        url += f"?ref={ref}"
    r = subprocess.run(["curl.exe", "-sL", "-H", f"Authorization: Bearer {TOKEN}",
                        "-H", "Accept: application/vnd.github.raw", url],
                       capture_output=True)
    return r.stdout.decode("utf-8", errors="replace")

def token():
    global TOKEN
    TOKEN = subprocess.run(["gh", "auth", "token"], capture_output=True,
                           text=True).stdout.strip()

CHANGELOGS = {}

CHANGELOGS["SystemMonitor"] = """# Changelog

## v1.0.2 - 2026-08-22

### Added
- **Desktop widget mode**: pin the monitor onto the desktop layer itself -
  behind every window, yet persistent across Show Desktop (Win+D), Win+M and
  virtual-desktop switches (Windows WorkerW embedding, Linux desktop-type
  windows, macOS best-effort). Right-click the title to toggle; persisted in
  config.json.
- Rounded glass tile design with soft accent glow, theme-aware palette.
- Manufacturer sensor backends: LibreHardwareMonitor / OpenHardwareMonitor
  WMI namespaces for true CPU/GPU temperatures, loads and fan RPMs.
- GPU usage & temperature tiles via auto-detected nvidia-smi.
- Fan RPM tiles (hardware monitor or psutil on Linux).
- Disk read/write throughput tiles.
- Battery percentage tile (laptops).
- Inferred CPU temperature from sustained load when no hardware source is
  available, honestly labelled `~Temperature`.

### Fixed
- Disk metrics now target the real system drive instead of `/` on Windows.
- Windows temperature detection no longer silently missing.

## v1.0.1 - 2026-08-22

### Added
- SECURITY.md with private vulnerability reporting.
- MIT license, `.gitignore`, `requirements.txt`.

## v1.0.0 - 2026-07-23

Initial release: cross-platform CPU/RAM/disk/network/ping monitoring with
theme selector, dynamic reordering and standalone builds for Windows, Linux
and macOS.
"""

CHANGELOGS["BlackGlass"] = """# Changelog

All notable changes are documented here. The README keeps a short highlights
list only.

## 1.6 - 2026-08-22

### Added
- **In-session teleporting** (pymetaverse-style): minimap double-clicks, the
  Teleport button, parcel modals and clickable `[Teleport to: ...]` chat links
  move you without relogging. The quick logout-login method remains as
  automatic failover.
- Region name resolution via MapNameRequest/MapItemReply.
- Per-user **Lists tab**: contacts with distance, discovered groups and open
  chat sessions.
- SECURITY.md, CONTRIBUTING.md, structured issue forms, CodeQL scanning.

### Changed
- `blackglass` package split (protocol / network / agent / credentials / ui).

### Hardening
- Bounded caches, stale-avatar pruning and deterministic packet pruning fix
  long-session memory growth.
- Windows credential files sealed whole-file with DPAPI; POSIX files chmod
  600.

## 1.5 - 2026-07-23

Multi-client login tabbed interface; minimap radar with live map tiles;
double-click hard teleport; GridSurvey fallback; nearby-avatar list with
teleport/profile actions.

## 1.4 - earlier

URI namespace resolution; groups, parcels and profiles accessible in-viewer.

## 1.3

Nearby avatars list with per-avatar Teleport To / Profile options.

## 1.2

Minimap renders dots for yourself and others correctly.
"""

CHANGELOGS["ExploitProtection"] = """# Changelog

## Unreleased - 2026-08-22

### Infrastructure
- CodeQL security analysis enabled (weekly + on push); repository code moved
  to standard lowercase `ExploitProtection.py` so the scanner extracts it.
- SECURITY.md with private vulnerability reporting.
- CONTRIBUTING.md plus structured bug/feature issue forms.
- Branch protection ruleset: default branch cannot be deleted or force-pushed.
- Funding configuration (GitHub Sponsors + Patreon) and support buttons.
- README images switched to branch-relative paths; hashtag block removed;
  license clarified.

## 1.1 / 1.0

See [Releases](../../releases) for bundled GUI builds and the growing
`XploitProtection.xml` mitigation catalog.
"""

CODEQL_BADGE = {
    "Cripple-NetStrip": "[![CodeQL](https://github.com/neohiro/Cripple-NetStrip/actions/workflows/codeql.yml/badge.svg)](https://github.com/neohiro/Cripple-NetStrip/actions/workflows/codeql.yml)",
    "BlackGlass": "[![CodeQL](https://github.com/neohiro/BlackGlass/actions/workflows/codeql.yml/badge.svg)](https://github.com/neohiro/BlackGlass/actions/workflows/codeql.yml)",
    "ExploitProtection": "[![CodeQL](https://github.com/neohiro/ExploitProtection/actions/workflows/codeql.yml/badge.svg?branch=M3T4P0D.3XPL01T)](https://github.com/neohiro/ExploitProtection/actions/workflows/codeql.yml)",
}

token()
os.makedirs("batchH", exist_ok=True)
manifest = []

for repo, content in CHANGELOGS.items():
    fp = os.path.join("batchH", f"{repo}__CHANGELOG.md")
    open(fp, "w", encoding="utf-8", newline="").write(content)
    manifest.append({"repo": repo, "branch": "M3T4P0D.3XPL01T" if repo == "ExploitProtection" else "main",
                     "path": "CHANGELOG.md", "file": fp})

# CodeQL badges into existing badge rows
for repo in CODEQL_BADGE:
    ref = "M3T4P0D.3XPL01T" if repo == "ExploitProtection" else "main"
    src = gh_raw(repo, "README.md", ref)
    if not src or "workflows/codeql.yml" in src:
        print(f"badge skip {repo}")
        continue
    lines = src.split("\n")
    for i, l in enumerate(lines[:12]):
        if "Build Status" in l or "release.yml/badge" in l:
            lines.insert(i + 1, CODEQL_BADGE[repo])
            break
    out = "\n".join(lines)
    if out != src:
        fp = os.path.join("batchH", f"{repo}__README.md")
        open(fp, "w", encoding="utf-8", newline="").write(out)
        manifest.append({"repo": repo, "branch": ref, "path": "README.md", "file": fp})
        print(f"badge staged {repo}")

open(os.path.join("batchH", "manifest.json"), "w").write(
    json.dumps(manifest))
print(f"staged {len(manifest)} commits")
