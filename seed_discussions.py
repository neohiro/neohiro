"""Seed announcement discussions (GraphQL inline queries)."""
import json, time

def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")

def gh(args, stdin=None):
    p = subprocess.run(["gh"] + args, input=stdin, capture_output=True,
                       text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr

import subprocess
REPOS = ["ExploitProtection", "Cripple-NetStrip", "BlackGlass", "dnscrypt-proxy-gui"]

ANNOUNCEMENTS = json.load(open("announcements.json", encoding="utf-8"))

for r in REPOS:
    repo_id = cat_id = None
    for attempt in range(4):
        rc, out, err = gh(["api", "graphql", "-f",
            'query=' + ('query { repository(owner:"neohiro", name:"%s") { id discussionCategories(first:10){ nodes { id name } } } }' % r)])
        try:
            parsed = json.loads(out)
        except Exception:
            parsed = {}
        if rc != 0 or not parsed.get("data") or not parsed["data"].get("repository"):
            print(f"  attempt {attempt+1} {r}: {(err or out)[:90]}")
            time.sleep(3 * (attempt + 1)); continue
        repo_id = parsed["data"]["repository"]["id"]
        cats = {c["name"]: c["id"] for c in parsed["data"]["repository"]["discussionCategories"]["nodes"]}
        cat_id = cats.get("Announcement") or next(iter(cats.values()))
        break
    if not repo_id:
        print(f"QUERY FAIL after retries: {r}"); continue

    a = ANNOUNCEMENTS[r]
    mut = ('mutation { createDiscussion(input: {repositoryId: "%s", categoryId: "%s", '
           'title: "%s", body: "%s"}) { discussion { url } } }'
           % (repo_id, cat_id, esc(a["title"]), esc(a["body"])))
    rc, out, err = gh(["api", "graphql", "-f", f"query={mut}"])
    try:
        parsed = json.loads(out)
        url = parsed["data"]["createDiscussion"]["discussion"]["url"]
        print(f"seeded {r}: {url}")
    except Exception:
        print(f"SEED FAIL {r}: {(err or out)[:160]}")
