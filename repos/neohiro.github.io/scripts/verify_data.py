"""
Verify _data/repos.yml matches _tools/*.md front matter.

Catches:
- repos.yml has entries without matching _tools file
- _tools has files without matching repos.yml entry
- field drift between repos.yml and _tools front matter for any
  non-numeric / non-timestamp key in ALLOWED_KEYS
- unknown fields in either source
- UTF-8 BOM in either source
- mojibake (Latin-1→UTF-8 round-trip) on em-dash / middle-dot
"""
import re
import glob
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT  = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
YAML_PATH  = os.path.join(REPO_ROOT, "_data", "repos.yml")
TOOLS_DIR  = os.path.join(REPO_ROOT, "_tools")

ALLOWED_KEYS = {
    "name", "title", "tagline", "platform", "language", "category",
    "featured", "weight", "repo_url", "demo_url", "docs_url", "icon",
    "stars", "forks", "open_issues", "created_at", "pushed_at",
    "deprecated", "deprecated_at", "deprecated_reason", "successor_repo"
}
DRIFT_KEYS = frozenset(ALLOWED_KEYS - {"name", "stars", "forks", "open_issues", "created_at", "pushed_at"})

# Byte-level signatures of "double-encoded" UTF-8 mojibake. Each entry is
# (replacement target, replacement string). These show up when UTF-8 bytes
# are decoded as Latin-1 and the resulting string is re-encoded as UTF-8.
# We match the trailing bytes of that pattern so the warning is precise.
MOJIBAKE_PATTERNS = [
    (b"\xc3\xa2\xe2\x82\xac",       "em-dash (—)"),
    (b"\xc3\x82\xc2\xb7",           "middle-dot (·)"),
]

def parse_front_matter(path):
    with open(path, "rb") as f:
        raw = f.read()
    if raw.startswith(b"\xef\xbb\xbf"):
        return "BOM"
    text = raw.decode("utf-8")
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.DOTALL)
    if not m:
        return None
    data = {}
    for line in m.group(1).split("\n"):
        if not line.strip():
            continue
        mm = re.match(r"^(\w+):\s*(.*)$", line)
        if mm:
            data[mm.group(1)] = mm.group(2).strip()
    return data

def parse_yaml_repos(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if text.startswith("\ufeff"):
        print("FATAL: _data/repos.yml has BOM")
        sys.exit(2)
    repos = {}
    current = None
    for raw in text.split("\n"):
        line = raw.rstrip()
        if line.startswith("  - name:"):
            if current:
                repos[current.get("name")] = current
            current = {"name": line.split(":", 1)[1].strip().strip('"')}
        elif line.startswith("    ") and current is not None and ":" in line:
            k, v = line.strip().split(":", 1)
            v = v.strip()
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            current[k.strip()] = v
    if current:
        repos[current.get("name")] = current
    return repos


def normalize(v):
    """Normalize a value for equality comparison across YAML/MD forms."""
    if v is None:
        return ""
    s = str(v).strip()
    if s in ("true", "True", "TRUE"):
        return "true"
    if s in ("false", "False", "FALSE"):
        return "false"
    if s.startswith('"') and s.endswith('"'):
        s = s[1:-1]
    return s.strip()


errors = []
warnings = []

# Parse tools
tools = {}
for path in sorted(glob.glob(os.path.join(TOOLS_DIR, "*.md"))):
    fm = parse_front_matter(path)
    if fm == "BOM":
        errors.append(f"{path}: still has UTF-8 BOM")
        continue
    if fm is None:
        errors.append(f"{path}: missing or invalid front matter")
        continue
    name = os.path.basename(path).replace(".md", "")
    if "name" in fm and fm["name"] != name:
        warnings.append(f"{path}: front matter name={fm['name']!r} does not match filename={name!r}")
    tools[name] = fm

# Mojibake regression guard. Scans raw bytes (mojibake is a byte-level
# signature, not a text one) so the check works regardless of how the
# file was decoded upstream.
for path in sorted(glob.glob(os.path.join(TOOLS_DIR, "*.md"))):
    with open(path, "rb") as f:
        raw = f.read()
    for sig, label in MOJIBAKE_PATTERNS:
        if sig in raw:
            errors.append(f"{path}: mojibake {label} (re-encode UTF-8 of UTF-8-as-Latin-1)")

with open(YAML_PATH, "rb") as f:
    yaml_raw = f.read()
for sig, label in MOJIBAKE_PATTERNS:
    if sig in yaml_raw:
        errors.append(f"{YAML_PATH}: mojibake {label}")

# Parse yaml
yaml_repos = parse_yaml_repos(YAML_PATH)
yaml_names = set(yaml_repos.keys())
tool_names = set(tools.keys())

# Check schema
for name, repo in yaml_repos.items():
    for k in repo.keys():
        if k not in ALLOWED_KEYS:
            errors.append(f"repos.yml entry {name!r}: unknown field {k!r}")

# Check coverage
missing_from_yaml = tool_names - yaml_names
extra_in_yaml = {name for name in (yaml_names - tool_names)
                 if normalize(yaml_repos[name].get("deprecated")) != "true"}
if missing_from_yaml:
    errors.append(f"_tools files missing from _data/repos.yml: {sorted(missing_from_yaml)}")
if extra_in_yaml:
    errors.append(f"_data/repos.yml entries without _tools file: {sorted(extra_in_yaml)}")

# Check key field consistency
for name in tool_names & yaml_names:
    fm = tools[name]
    ym = yaml_repos[name]
    for k in DRIFT_KEYS:
        fm_v = normalize(fm.get(k, ""))
        ym_v = normalize(ym.get(k, ""))
        if fm_v and ym_v and fm_v != ym_v:
            errors.append(f"{name}: field {k!r} drift: tools={fm_v!r} yaml={ym_v!r}")

# Result
print("=" * 60)
print(f"Tools:    {len(tools)}")
print(f"Repos:    {len(yaml_repos)}")
print(f"Errors:   {len(errors)}")
print(f"Warnings: {len(warnings)}")
print("=" * 60)
for e in errors:
    print(f"  ERROR   {e}")
for w in warnings:
    print(f"  WARN    {w}")
sys.exit(1 if errors else 0)
