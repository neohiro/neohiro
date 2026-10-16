"""Batch A: paths-ignore (push triggers) + pip cache (setup-python) across workflows."""
import re, sys
import subprocess, json

def gh(*args):
    return subprocess.run(["gh"] + list(args), capture_output=True, text=True)

def get_wf(repo, name):
    r = gh("api", f"repos/neohiro/{repo}/contents/.github/workflows/{name}",
           "-H", "Accept: application/vnd.github.raw")
    return r.stdout if r.returncode == 0 else None

def yaml_ok(text):
    try:
        import yaml
        yaml.safe_load(text)
        return True
    except Exception as e:
        print(f"    YAML FAIL: {e}")
        return False

IGNORE_BLOCK = ("    paths-ignore:\n"
                "      - '**.md'\n"
                "      - '**.txt'\n"
                "      - '.gitignore'\n"
                "      - 'docs/**'\n")

def add_paths_ignore(text):
    """Insert paths-ignore right after a push block's branches line(s)."""
    pattern = re.compile(r"^([ ]+)push:\n((?:[ ]{4,}[^\n]*\n|\n)*?)", re.M)
    m = re.search(r"(?m)^([ ]+)push:\n((?:[ ]+[^\n]*\n)+)", text)
    if not m:
        return None
    # find insertion point: after consecutive more-indented lines following 'push:'
    indent = m.group(1)
    start = m.end()
    lines = text[start:].split("\n")
    consumed = 0
    for ln in lines:
        if ln.strip() == "" or ln.startswith(indent + "  "):
            consumed += len(ln) + 1
        else:
            break
    insert_at = start + consumed
    return text[:insert_at] + IGNORE_BLOCK + text[insert_at:]

def add_pip_cache(text):
    def repl(m):
        block = m.group(0)
        if "cache:" in block:
            return block
        return block + m.group("ind") + "cache: 'pip'\n"
    pattern = re.compile(
        r"(?P<ind>[ ]+)uses: actions/setup-python@\S+\n"
        r"(?P=ind)with:\n"
        r"(?P<py>(?P=ind)[ ]+python-version:[^\n]*\n)")
    return pattern.sub(repl, text)

CACHE_REPOS = {
    "Cripple-NetStrip", "BlackGlass", "GhostMaze", "GoogleCommand", "LANScan",
    "MusicPlay", "NewsAgreggator", "ShadowSocks", "SystemMonitor", "Tetris",
    "ZombieShoot", "ClockWidget", "dnscrypt-proxy-gui", "MoodTracker", "NetMatrix",
    "TristarMania",
}

targets = []
for wf in ("release.yml", "ci.yml", "android-gate.yml"):
    r = gh("api", f"repos/neohiro/Cripple-NetStrip/contents/.github/workflows/{wf}",
           "-H", "Accept: application/vnd.github.raw")
    if r.returncode == 0:
        targets.append(("Cripple-NetStrip", wf, r.stdout))

changed_files = {}
for repo, wf, src in targets:
    out = src
    notes = []
    new_out = add_paths_ignore(out)
    if new_out:
        out = new_out
        notes.append("paths-ignore")
    if repo in CACHE_REPOS:
        new_out = add_pip_cache(out)
        if new_out != out:
            out = new_out
            notes.append("pip-cache")
    if out == src:
        notes.append("no-change")
    else:
        assert yaml_ok(out), f"{repo}/{wf}"
        changed_files[(repo, wf)] = out
    print(f"{repo}/{wf}: {', '.join(notes)}")

# other CACHE_REPOS release.yml files
for repo in sorted(CACHE_REPOS - {"Cripple-NetStrip"}):
    src = get_wf(repo, "release.yml")
    if not src:
        print(f"{repo}/release.yml: MISSING, skipped")
        continue
    out = add_pip_cache(src)
    if out != src:
        assert yaml_ok(out), repo
        changed_files[(repo, "release.yml")] = out
        print(f"{repo}/release.yml: pip-cache")
    else:
        print(f"{repo}/release.yml: no setup-python match")

import os
os.makedirs(r"C:\Users\skele\Documents\GitHub Manager\batchA", exist_ok=True)
manifest = []
for (repo, wf), content in changed_files.items():
    fp = rf"C:\Users\skele\Documents\GitHub Manager\batchA\{repo}__{wf}"
    open(fp, "w", encoding="utf-8", newline="").write(content)
    manifest.append(f"{repo}|{wf}")
open(r"C:\Users\skele\Documents\GitHub Manager\batchA\manifest.txt", "w").write("\n".join(manifest))
print(f"\nstaged {len(changed_files)} files")
