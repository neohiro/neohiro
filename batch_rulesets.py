"""Create default-branch protection rulesets on ALL repositories."""
import json, subprocess

def gh_json(method, endpoint, body=None):
    args = ["gh", "api", "-X", method, endpoint]
    if body is not None:
        args += ["--input", "-"]
        p = subprocess.run(args, input=json.dumps(body), capture_output=True,
                           text=True, encoding="utf-8")
    else:
        p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr

repos = subprocess.run(
    ["gh", "repo", "list", "neohiro", "--limit", "100", "--json", "name,isPrivate,defaultBranchRef"],
    capture_output=True, text=True, encoding="utf-8")
repos = json.loads(repos.stdout)

RULESET = {
    "name": "default-branch-protection",
    "target": "branch",
    "enforcement": "active",
    "conditions": {
        "ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}
    },
    "rules": [
        {"type": "deletion"},
        {"type": "non_fast_forward"}
    ]
}

ok = skip = fail = 0
for r in repos:
    name = r["name"]
    vis = "private" if r["isPrivate"] else "public"
    # skip if a ruleset with this name already exists
    rc, out, _ = gh_json("GET", f"/repos/neohiro/{name}/rulesets")
    if rc == 0:
        existing = json.loads(out)
        if any(rs.get("name") == RULESET["name"] for rs in existing):
            print(f"SKIP {name} ({vis}): ruleset already present")
            skip += 1
            continue
    rc, out, err = gh_json("POST", f"/repos/neohiro/{name}/rulesets", RULESET)
    if rc == 0:
        rid = json.loads(out).get("id", "?")
        print(f"OK   {name} ({vis}): ruleset id {rid}")
        ok += 1
    else:
        print(f"FAIL {name} ({vis}): {err.strip()[:100]}")
        fail += 1

print(f"\ncreated={ok} skipped={skip} failed={fail}")
