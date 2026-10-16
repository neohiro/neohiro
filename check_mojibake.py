#!/usr/bin/env python3
"""Scan GitHub account/org/repo metadata, remote READMEs and local staging files for mojibake."""
import json, re, subprocess, sys, glob, os

USER = "neohiro"

def gh_json(endpoint):
    r = subprocess.run(["gh", "api", endpoint], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"{endpoint}: {r.stderr.decode('utf-8', 'replace')[:150]}")
    return json.loads(r.stdout.decode("utf-8"))

def gh_raw(endpoint):
    r = subprocess.run(["gh", "api", endpoint, "-H", "Accept: application/vnd.github.raw"],
                       capture_output=True)
    if r.returncode != 0:
        return None
    return r.stdout  # raw bytes, untouched by any console encoding

MOJIBAKE = [
    (re.compile("\ufffd"), "U+FFFD replacement char"),
    (re.compile(r"[\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF][\u007F-\u00BF]"), "cp1252-style double-encoded UTF-8"),
    (re.compile("â€"), "smart-punctuation artifact"),
    (re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]{2,}"), "CJK run (unexpected?)"),
]

def find_problems(text):
    hits = []
    for rx, label in MOJIBAKE:
        for m in rx.finditer(text):
            s = max(0, m.start() - 25)
            ctx = repr(text[s:m.end() + 25])
            hits.append(f"[{label}] ...{ctx}...")
    # dedupe, keep order
    seen, out = set(), []
    for h in hits:
        key = h.split("]", 1)[1][:60]
        if key not in seen:
            seen.add(key); out.append(h)
    return out[:5]

def check_text(name, data_bytes, report):
    if data_bytes is None:
        return
    try:
        text = data_bytes.decode("utf-8")          # strict
    except UnicodeDecodeError as e:
        report.append(f"{name}: INVALID UTF-8 ({e})")
        return
    if data_bytes.startswith(b"\xef\xbb\xbf"):
        report.append(f"{name}: has UTF-8 BOM")
    problems = find_problems(text)
    for p in problems:
        report.append(f"{name}: {p}")

report = []

# ---------- account ----------
print("scanning account...", flush=True)
me = gh_json(f"/users/{USER}")
for k in ("name", "bio", "company", "blog", "location", "twitter_username"):
    v = me.get(k)
    if v:
        check_text(f"account.{k}", v.encode("utf-8"), report)

# ---------- orgs ----------
print("scanning orgs...", flush=True)
orgs = gh_json(f"/users/{USER}/orgs")
for o in orgs:
    full = gh_json(f"/orgs/{o['login']}")
    for k in ("name", "description", "blog", "location"):
        v = full.get(k)
        if v:
            check_text(f"org:{o['login']}.{k}", v.encode("utf-8"), report)

# ---------- repos: metadata + readme ----------
print("listing repos...", flush=True)
repos = []
page = 1
while True:
    batch = gh_json(f"/users/{USER}/repos?per_page=100&type=owner&sort=updated&page={page}")
    repos.extend(batch)
    if len(batch) < 100:
        break
    page += 1

for i, r in enumerate(repos, 1):
    name = r["name"]
    print(f"  [{i}/{len(repos)}] {name}", flush=True)
    for k in ("description",):
        v = r.get(k)
        if v:
            check_text(f"{name}.description", v.encode("utf-8"), report)
    raw = gh_raw(f"/repos/{USER}/{name}/readme")
    if raw is None:
        report.append(f"{name}: no README")
    else:
        check_text(f"{name}/README.md", raw, report)

# ---------- explicit orgs from CLI ----------
for org in sys.argv[1:]:
    print(f"scanning org {org}...", flush=True)
    try:
        full = gh_json(f"/orgs/{org}")
    except RuntimeError as e:
        report.append(f"org:{org}: UNREACHABLE ({e})")
        continue
    for k in ("name", "description", "blog", "location"):
        v = full.get(k)
        if v:
            check_text(f"org:{org}.{k}", v.encode("utf-8"), report)
    o_repos = gh_json(f"/orgs/{org}/repos?per_page=100&type=all&sort=updated")
    for r in o_repos:
        name = f"{org}/{r['name']}"
        print(f"  {name}", flush=True)
        if r.get("description"):
            check_text(f"{name}.description", r["description"].encode("utf-8"), report)
        raw = gh_raw(f"/repos/{USER}/{r['name']}/readme")
        if raw is None:
            raw = gh_raw(f"/repos/{org}/{r['name']}/readme")
        if raw is None:
            report.append(f"{name}: no README")
        else:
            check_text(f"{name}/README.md", raw, report)

# ---------- local staging ----------
print("scanning local staging files...", flush=True)
local_targets = (
    glob.glob(os.path.join("batchG_readmes", "*.md"))
    + glob.glob(os.path.join("batchG_readmes", "*.txt"))
    + glob.glob(os.path.join("profile", "*"))
    + ["org-profile-readme.md", "frenzypenguin-media-site/repos.json",
       "frenzypenguin-media-site/index.html", "frenzypenguin-media-site/main.js",
       "pages-site/index.html", "pages-site/main.js"]
)
for fp in local_targets:
    if os.path.isfile(fp):
        with open(fp, "rb") as f:
            check_text(fp, f.read(), report)

print()
with open("mojibake_report.txt", "w", encoding="utf-8") as f:
    if report:
        f.write(f"=== {len(report)} FINDING(S) ===\n")
        f.write("\n".join(report) + "\n")
    else:
        f.write("=== ALL CLEAN ===\n")
print(open("mojibake_report.txt", encoding="utf-8").read().encode("ascii", "backslashreplace").decode())
