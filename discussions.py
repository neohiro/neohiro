"""Enable Discussions + seed announcement posts on 4 flagships."""
import json, subprocess

def gh(args, stdin=None):
    p = subprocess.run(["gh"] + args, input=stdin, capture_output=True,
                       text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr

REPOS = ["ExploitProtection", "Cripple-NetStrip", "BlackGlass", "dnscrypt-proxy-gui"]

ANNOUNCEMENTS = {
"ExploitProtection": {
 "title": "📌 Welcome — read this first",
 "body": """Welcome to the **ExploitProtection** discussions!

**Quick orientation**
- 🐛 Found a bug? Open a **Bug report** issue instead (structured form above).
- 🛡️ Vulnerability? Use **Report a vulnerability** on the Security tab — never a public issue.
- 📄 Want to add/verify mitigation entries? See [CONTRIBUTING.md](../blob/M3T4P0D.3XPL01T/CONTRIBUTING.md) — the catalog (`XploitProtection.xml`) is the heart of this project.
- 💬 This forum is for questions, usage tips and hardening chat.

**Latest builds**: [Releases](../../releases) — Windows standalone, auto-built.

*— FrenzyPenguin Media 🛡️*"""
},
"Cripple-NetStrip": {
 "title": "📌 Welcome — read this first",
 "body": """Welcome to **NetStrip / Cripple** discussions!

**Quick orientation**
- 🐛 Bugs → **Bug report** issue with OS + version filled in.
- 🔐 Security issues → Security tab, private report.
- 🧭 Usage help (rules, blocklists, LAN Shield, Android VPN) → **Q&A** category here.
- 🚀 Release notes live in [Releases](../../releases); full changelog in `changelog.md`.

**Ground rules**: no piracy talk, no attack traffic against systems you don't own.

*— FrenzyPenguin Media 🕸️*"""
},
"BlackGlass": {
 "title": "📌 Welcome — read this first",
 "body": """Welcome to **BlackGlass** discussions — the multi-client Second Life chat viewer!

**Quick orientation**
- 🐛 Viewer bugs → **Bug report** issue (include viewer version + grid).
- 💬 Second Life chat/usage questions → **Q&A**.
- 🗺️ Teleporting, minimap or Lists tab ideas → **Ideas**.
- ⚠️ Reminder: comply with the [Second Life ToS](https://www.lindenlab.com/legal/second-life-terms-and-conditions); use a test account when experimenting.

**Downloads**: [Releases](../../releases) — Windows/macOS/Linux, auto-built from tags.

*— FrenzyPenguin Media 👽*"""
},
"dnscrypt-proxy-gui": {
 "title": "📌 Welcome — read this first",
 "body": """Welcome to **dnscrypt-proxy GUI** discussions!

**Quick orientation**
- 🐛 GUI bugs → **Bug report** issue (OS + dnscrypt-proxy version please).
- 🌐 Resolver/server recommendations and encrypted-DNS questions → **Q&A**.
- 💡 Feature ideas (tray behavior, TOML editing UX…) → **Ideas**.
- ⚙️ The GUI manages [dnscrypt-proxy](https://github.com/DNSCrypt/dnscrypt-proxy) — proxy core bugs belong upstream.

**Downloads**: [Releases](../../releases).

*— FrenzyPenguin Media 🛡️*"""
},
}

# 1. enable discussions
for r in REPOS:
    rc, out, err = gh(["api", "-X", "PATCH", f"repos/neohiro/{r}", "-f", "has_discussions=true"])
    print(("enabled: " if rc == 0 else "ENABLE FAIL: ") + r)

# 2. fetch ids + create announcement
import time
for r in REPOS:
    repo_id = cat_id = None
    for attempt in range(5):
        q = {"query": 'query { repository(owner:"neohiro", name:"%s") { id discussionCategories(first:10){ nodes { id name } } } }' % r}
        rc, out, err = gh(["api", "graphql"], stdin=json.dumps(q))
        try:
            parsed = json.loads(out)
        except Exception:
            parsed = {}
        if rc != 0 or not parsed.get("data") or not parsed["data"].get("repository"):
            print(f"  attempt {attempt+1} {r}: {(err or out)[:100]}")
            time.sleep(3 * (attempt + 1)); continue
        data = parsed["data"]["repository"]
        if not data:
            time.sleep(3); continue
        repo_id = data["id"]
        cats = {c["name"]: c["id"] for c in data["discussionCategories"]["nodes"]}
        cat_id = cats.get("Announcement") or list(cats.values())[0]
        break
    if not repo_id:
        print(f"QUERY FAIL after retries: {r}"); continue
    mut = {"query": 'mutation($input: CreateDiscussionInput!) { createDiscussion(input: $input) { discussion { url } } }',
           "variables": {"input": {"repositoryId": repo_id, "categoryId": cat_id,
                                    "title": ANNOUNCEMENTS[r]["title"],
                                    "body": ANNOUNCEMENTS[r]["body"]}}}
    rc, out, err = gh(["api", "graphql"], stdin=json.dumps(mut))
    if rc == 0 and "errors" not in out:
        url = json.loads(out)["data"]["createDiscussion"]["discussion"]["url"]
        print(f"seeded {r}: {url}")
    else:
        print(f"SEED FAIL {r}: {(err or out)[:160]}")
