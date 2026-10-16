"""Iteratively fix undefined/unused imports in generated modules using pyflakes."""
import subprocess, re, os, sys

PKG = r"repos\BlackGlass\blackglass"
LAUNCHER = r"repos\BlackGlass\BlackGlass.py.new"

NAME_TO_IMPORTS = {
    "urllib": ["import urllib.parse", "import urllib.request"],
    "html_parser": ["import html as html_parser"],
    "UUID": ["from uuid import UUID"],
    "get_mac": ["from uuid import getnode as get_mac"],
    "__uuid__": ["import uuid as __uuid__"],
}

def stdlib_line(name):
    if name in NAME_TO_IMPORTS:
        return NAME_TO_IMPORTS[name]
    return [f"import {name}"]

def run_pyflakes(paths):
    p = subprocess.run([sys.executable, "-m", "pyflakes"] + paths,
                       capture_output=True, text=True)
    return p.stdout.splitlines()

paths = []
for root, _, files in os.walk(PKG):
    for fn in files:
        if fn.endswith(".py"):
            paths.append(os.path.join(root, fn))
paths.append(LAUNCHER)

changed = True
rounds = 0
while changed and rounds < 6:
    rounds += 1
    changed = False
    findings = run_pyflakes(paths)
    per_file_undef = {}
    per_file_unused = {}
    for ln in findings:
        m = re.match(r"(.+?):(\d+):\d+: undefined name '([^']+)'", ln)
        if m:
            per_file_undef.setdefault(m.group(1), set()).add(m.group(3))
            continue
        m = re.match(r"(.+?):\d+:\d+: '([^']+)' imported but unused", ln)
        if m and not ln.endswith("_(__init__)"):
            per_file_unused.setdefault(m.group(1), []).append(m.group(2))

    for path, names in per_file_undef.items():
        src = open(path, encoding="utf-8").read().splitlines(keepends=True)
        # find insertion index: after last import-ish line within first 40 lines
        idx = 0
        for i, l in enumerate(src[:60]):
            if l.startswith(("import ", "from ")) or l.startswith(("                      ",)) and ")" in l and i > 0 and src[i-1].startswith(("import", "from", " ")):
                idx = i + 1
            if l.strip() == "" and idx:
                break
        new_lines = []
        for n in sorted(names):
            for imp in stdlib_line(n):
                if imp + "\n" not in "".join(src):
                    new_lines.append(imp + "\n")
        if new_lines:
            src[idx:idx] = new_lines
            open(path, "w", encoding="utf-8", newline="").write("".join(src))
            print(f"[{os.path.basename(path)}] added: {[l.strip() for l in new_lines]}")
            changed = True

    # trim unused injected stdlib imports only (never touch package-relative ones)
    for path, unused in per_file_unused.items():
        src = open(path, encoding="utf-8").read().splitlines(keepends=True)
        removed = False
        keep = []
        body_start = len(src)
        for i, l in enumerate(src):
            if l.strip() and not l.startswith(('"""', 'import', 'from', ' ', ')')):
                body_start = i
                break
        for i, l in enumerate(src):
            mod = None
            m = re.match(r"import ([a-zA-Z_][\w.]*)", l)
            if m:
                mod = m.group(1).split(".")[0]
            m2 = re.match(r"from [a-zA-Z_.]+ import .* as (\w+)", l)
            if m2 and m2.group(1) in unused:
                if i < body_start:
                    removed = True
                    continue
            elif mod and len(mod.split(".")) == 1 and any(u == mod or u.startswith(mod + ".") for u in unused):
                if i < body_start:
                    removed = True
                    continue
            keep.append(l)
        if removed:
            open(path, "w", encoding="utf-8", newline="").write("".join(keep))
            print(f"[{os.path.basename(path)}] trimmed unused imports")
            changed = True

print(f"Done after {rounds} round(s).")
findings = run_pyflakes(paths)
real = [f for f in findings if "undefined name" in f]
print(f"Remaining undefined names: {len(real)}")
for r in real[:10]:
    print(" ", r)
unused_left = [f for f in findings if "imported but unused" in f]
print(f"Unused import warnings left: {len(unused_left)} (cosmetic)")
