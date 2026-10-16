"""Append colored Sponsor/Patreon buttons to the bottom of every public README."""
import subprocess, os

TOKEN = subprocess.run(["gh", "auth", "token"], capture_output=True,
                       text=True).stdout.strip()

def gh_raw(repo, path, ref=None):
    url = f"https://api.github.com/repos/neohiro/{repo}/contents/{path}"
    if ref:
        url += f"?ref={ref}"
    r = subprocess.run(["curl.exe", "-sL", "-H", f"Authorization: Bearer {TOKEN}",
                        "-H", "Accept: application/vnd.github.raw", url],
                       capture_output=True)
    return r.stdout.decode("utf-8", errors="replace")

BLOCK = """
---

<p align="center">
  <a href="https://github.com/sponsors/neohiro"><img src="https://img.shields.io/badge/Sponsor%20on%20GitHub-%E2%9D%A4-EA4AAA?logo=githubsponsors&style=for-the-badge" alt="GitHub Sponsors"></a>&nbsp;&nbsp;
  <a href="https://www.patreon.com/frenzypenguin_media"><img src="https://img.shields.io/badge/Patreon-frenzypenguin__media-F96854?logo=patreon&style=for-the-badge" alt="Support on Patreon"></a>
</p>
"""

repos = subprocess.run(
    ["gh", "repo", "list", "neohiro", "--visibility=public", "--limit", "100",
     "--json", "name,defaultBranchRef"],
    capture_output=True, text=True, encoding="utf-8")
repos = json.loads(repos.stdout) if False else __import__("json").loads(repos.stdout)

os.makedirs("batchG_readmes", exist_ok=True)
manifest = []
for r in repos:
    name = r["name"]
    branch = r["defaultBranchRef"]["name"]
    content = gh_raw(name, "README.md", branch)
    if not content:
        print(f"SKIP {name}: no README")
        continue
    if "shields.io/badge/Sponsor" in content or "💖 Support" in content:
        print(f"SKIP {name}: already has support buttons")
        continue
    if not content.endswith("\n"):
        content += "\n"
    content += BLOCK
    fp = os.path.join("batchG_readmes", f"{name}__README.md")
    open(fp, "w", encoding="utf-8", newline="").write(content)
    manifest.append(f"{name}|{branch}")
    print(f"staged {name}")

open(os.path.join("batchG_readmes", "manifest.txt"), "w").write("\n".join(manifest))
print(f"\nstaged {len(manifest)} READMEs")
