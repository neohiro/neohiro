"""Batch A-fix v2: repair cache indentation + paths-ignore placement."""
import re, subprocess

def gh_raw(repo, wf):
    r = subprocess.run(["gh", "api", f"repos/neohiro/{repo}/contents/.github/workflows/{wf}",
                        "-H", "Accept: application/vnd.github.raw"],
                       capture_output=True, text=True, encoding="utf-8")
    return r.stdout if r.returncode == 0 else None

CACHE_LINE = re.compile(r"(?m)^[ ]+cache: 'pip'[ ]*$")

def fix_cache(text):
    """Remove misplaced cache lines, then nest cache inside the with: block."""
    cleaned = CACHE_LINE.sub("", text)
    if cleaned == text:
        return None
    pattern = re.compile(
        r"(?m)^(?P<u>[ ]+)uses: actions/setup-python@\S+\n"
        r"(?P=u)with:\n"
        r"(?P<p>[ ]+)python-version:[^\n]*\n")
    out, k = pattern.subn(lambda m: m.group(0) + m.group("p") + "cache: 'pip'\n",
                          cleaned)
    assert k >= 1, "setup-python block not found"
    return out

IGNORE = ("    paths-ignore:\n"
          "      - '**.md'\n"
          "      - '**.txt'\n"
          "      - '.gitignore'\n"
          "      - 'docs/**'\n")

def fix_paths_ignore(text):
    changed = False
    # drop misplaced blocks wherever they are
    cleaned, n = CACHE_IGNORE_ANY.subn("", text)
    if n:
        text, changed = cleaned, True
    # insert under push:
    m = re.search(r"(?m)^  push:\n", text)
    if m and "paths-ignore" not in text[m.end():m.end() + 400]:
        text = text[:m.end()] + IGNORE + text[m.end():]
        changed = True
    return text, changed

CACHE_IGNORE_ANY = re.compile(
    r"[ ]+paths-ignore:\n(?:[ ]+- '[^']*'\n)+")

REPOS = ["Cripple-NetStrip", "BlackGlass", "ClockWidget", "GhostMaze", "GoogleCommand",
         "LANScan", "MoodTracker", "MusicPlay", "NetMatrix", "NewsAgreggator",
         "ShadowSocks", "SystemMonitor", "Tetris", "TristarMania", "ZombieShoot",
         "dnscrypt-proxy-gui"]

import os
os.makedirs("batchA_fix", exist_ok=True)
manifest = []
for repo in REPOS:
    for wf in ("release.yml", "ci.yml"):
        src = gh_raw(repo, wf)
        if not src:
            continue
        out = src
        notes = []
        c1 = fix_cache(out)
        if c1 is not None:
            out = c1
            notes.append("cache-fixed")
        if repo == "Cripple-NetStrip":
            c2, ch = fix_paths_ignore(out)
            if ch:
                out = c2
                notes.append("ignore-moved")
        if out != src:
            # verify every cache line sits exactly two spaces deeper than its uses-line
            lines = out.split("\n")
            for i, l in enumerate(lines):
                if "setup-python" in l and "uses:" in l:
                    u_ind = len(l) - len(l.lstrip())
                    for j in range(i, min(i + 6, len(lines))):
                        if "cache: 'pip'" in lines[j]:
                            c_ind = len(lines[j]) - len(lines[j].lstrip())
                            assert c_ind == u_ind + 2, f"{repo}/{wf} line {j}"
            fp = rf"batchA_fix\{repo}__{wf}"
            open(fp, "w", encoding="utf-8", newline="").write(out)
            manifest.append(f"{repo}|{wf}")
            print(f"{repo}/{wf}: {', '.join(notes) if notes else 'verify-only'}")
open("batchA_fix\\manifest.txt", "w").write("\n".join(manifest))
print(f"\nstaged {len(manifest)} corrections")
