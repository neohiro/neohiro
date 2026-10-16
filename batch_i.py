"""Batch I: generate_release_notes in all softprops workflows."""
import re, subprocess, os

def gh_raw(repo, wf="release.yml"):
    r = subprocess.run(["gh", "api", f"repos/neohiro/{repo}/contents/.github/workflows/{wf}",
                        "-H", "Accept: application/vnd.github.raw"],
                       capture_output=True, text=True, encoding="utf-8")
    return r.stdout if r.returncode == 0 else None

repos = subprocess.run(
    ["gh", "repo", "list", "neohiro", "--visibility=public", "--limit", "100", "--json", "name"],
    capture_output=True, text=True, encoding="utf-8")
repos = [r["name"] for r in __import__("json").loads(repos.stdout)]

os.makedirs("batchI", exist_ok=True)
manifest = []
for repo in repos:
    if repo == "neohiro":
        continue
    src = gh_raw(repo)
    if not src or "softprops/action-gh-release" not in src:
        continue
    if "generate_release_notes" in src:
        print(f"skip {repo} (already set)")
        continue
    out, n = re.subn(r"(?m)^(\s+tag_name:[^\n]*\n)", r"\1\2generate_release_notes: true\n".replace(r"\2", ""), src)
    # simpler: insert right after tag_name line with matching indent
    def repl(m):
        return m.group(1) + m.group("ind") + "generate_release_notes: true\n"
    out, n = re.subn(r"(?m)^(?P<ind>[ ]+)tag_name:[^\n]*\n)", "", src) if False else (src, 0)
    m = re.search(r"(?m)^(?P<ind>[ ]+)tag_name:[^\n]*\n", out)
    if not m:
        print(f"skip {repo}: no tag_name line")
        continue
    ind = m.group("ind")
    out = out[:m.end()] + f"{ind}generate_release_notes: true\n" + out[m.end():]
    fp = os.path.join("batchI", f"{repo}__release.yml")
    open(fp, "w", encoding="utf-8", newline="").write(out)
    manifest.append(f"{repo}")
    print(f"staged {repo}")

open(os.path.join("batchI", "manifest.txt"), "w").write("\n".join(manifest))
print(f"\nstaged {len(manifest)}")
