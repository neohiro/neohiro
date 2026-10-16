"""Rename ExploitProtection.PY -> ExploitProtection.py + update all references."""
import re

# 1. fetch current source
import subprocess
r = subprocess.run(["gh","api","repos/neohiro/ExploitProtection/contents/ExploitProtection.PY?ref=M3T4P0D.3XPL01T",
                    "-H","Accept: application/vnd.github.raw"],
                   capture_output=True)
src = r.stdout.decode("utf-8")

# 2. fetch release.yml + README, patch refs
def gh_raw(path):
    r = subprocess.run(["gh","api",f"repos/neohiro/ExploitProtection/contents/{path}?ref=M3T4P0D.3XPL01T",
                        "-H","Accept: application/vnd.github.raw"], capture_output=True)
    return r.stdout.decode("utf-8")

rel = gh_raw(".github/workflows/release.yml").replace(
    "ExploitProtection.PY", "ExploitProtection.py")
readme = gh_raw("README.md").replace(
    "blob/M3T4P0D.3XPL01T/ExploitProtection.py", "blob/M3T4P0D.3XPL01T/ExploitProtection.py")

open(r"batchF\ep_source.py.txt", "w", encoding="utf-8", newline="").write(src)
open(r"batchF\ep_release.yml", "w", encoding="utf-8", newline="").write(rel)
open(r"batchF\ep_readme.md", "w", encoding="utf-8", newline="").write(readme)

import ast
print("staged rename payload:",
      len(src), "bytes source |",
      "release refs .PY left:", rel.count(".PY"), "|",
      "readme .PY path refs:", readme.count("ExploitProtection.PY"))
