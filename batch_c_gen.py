"""Batch C: CONTRIBUTING.md + issue forms + PR template for 3 flagships."""
import os, ast

ROOT = r"C:\Users\skele\Documents\GitHub Manager\scaffold"
os.makedirs(ROOT, exist_ok=True)

CONTACTS = "[frenzypenguin.media](https://linktr.ee/frenzypenguin.media)"

def contributing(about, setup, notes):
    return f"""# Contributing to {about}

Thanks for helping out! This project accepts issues and pull requests.

## Reporting bugs

Open a **Bug report** issue and fill in every field of the form - OS version,
app version and reproduction steps make the difference between a fix and a
close. For anything you believe is exploitable, use **Report a vulnerability**
on the Security tab instead (see SECURITY.md).

## Development setup

{setup}

{notes}

## Pull requests

1. Fork and create a topic branch.
2. Keep changes focused - one fix or feature per PR.
3. Test against the live target (Windows / grid) before submitting where feasible.
4. Describe **what** and **why** in the PR body.

## Contact

{CONTACTS}
"""

SETUPS = {
 "ExploitProtection": (
   "**ExploitProtection**",
   "```bash\npip install -r requirements.txt\npython ExploitProtection.PY\n```\n\nNo third-party dependencies beyond the standard library are required at runtime.",
   """## Improving the protection database

The most valuable contribution is not code - it's the catalog:
[XploitProtection.xml](XploitProtection.xml). Add or verify mitigation entries
for popular Windows software, keep formatting consistent with existing
entries, and submit a PR. Changes are validated by importing the XML with
`Set-ProcessMitigation` on a clean Windows VM before merge."""),
 "Cripple-NetStrip": (
   "**Cripple-NetStrip**",
   "```bash\npip install -r requirements.txt\npip install -e .\npython -m pytest tests/\nflake8 netstrip/ --count --select=E9,F63,F7,F82 --show-source\npython main.py\n```\n\nAndroid builds use `buildozer` (see buildozer.spec); CI covers lint, import smoke tests and unit tests on three OSes.",
   """## Code layout

`netstrip/` is fully modular: `core/` (engine, DNS proxy, blocklist manager,
interceptor), `gui/views/`, `platform/`, `data/`. Entry point is `main.py`.
Please match the existing module boundaries rather than growing monoliths."""),
 "BlackGlass": (
   "**BlackGlass**",
   "```bash\npip install -r requirements.txt\npython BlackGlass.py\n```\n\nRequires Python 3.7+; Pillow is optional (map tiles degrade gracefully without it).",
   """## Code layout

```
blackglass/
├── lltypes / codec / messages / packet   # protocol stack
├── network                               # login, circuits, LLSD
├── agent                                 # SecondLifeAgent session logic
├── credentials                           # local profile storage
└── ui/                                   # widgets, theme, minimap, chat, login, app
```

Protocol layers must never import UI code. A great first contribution is a
new message template in `messages.py` or an improvement confined to a single
file under `ui/`."""),
}

FILES = {}

for key, (title, setup, notes) in SETUPS.items():
    FILES[f"{key}/CONTRIBUTING.md"] = contributing(title, setup, notes)

bug = """name: Bug report
description: Report something broken
labels: [bug]
body:
  - type: textarea
    id: description
    attributes:
      label: What happened?
      description: Also tell us what you expected to happen instead.
    validations:
      required: true
  - type: textarea
    id: steps
    attributes:
      label: Steps to reproduce
      placeholder: |
        1. Launch ...
        2. Click ...
        3. See error
    validations:
      required: true
  - type: dropdown
    id: os
    attributes:
      label: Operating system
      options:
        - Windows 11
        - Windows 10
        - Linux (please specify in description)
        - macOS
    validations:
      required: true
  - type: dropdown
    id: source
    attributes:
      label: How are you running it?
      options:
        - Latest release download
        - Run from source
    validations:
      required: true
  - type: input
    id: version
    attributes:
      label: App version / release tag
      placeholder: v1.6.0
  - type: textarea
    id: logs
    attributes:
      label: Logs or screenshots
      description: Attach anything that helps. Remove personal data first.
"""

feature = """name: Feature request
description: Suggest an idea
labels: [enhancement]
body:
  - type: textarea
    id: problem
    attributes:
      label: Problem to solve
      description: What are you trying to do that currently doesn't work well?
    validations:
      required: true
  - type: textarea
    id: solution
    attributes:
      label: Proposed solution
    validations:
      required: true
  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives considered
"""

config = f"""blank_issues_enabled: false
contact_links:
  - name: Questions & contact
    url: https://linktr.ee/frenzypenguin.media
    about: General questions that are not bugs or feature requests.
"""

pr_template = """## Summary

<!-- What does this PR change and why? -->

## Checklist

- [ ] Tested locally against the real target
- [ ] Focused scope - one change per PR
- [ ] Docs/README updated if behavior or usage changed
"""

FILES["ExploitProtection/.github/ISSUE_TEMPLATE/bug_report.yml"] = bug
FILES["ExploitProtection/.github/ISSUE_TEMPLATE/feature_request.yml"] = feature
FILES["ExploitProtection/.github/ISSUE_TEMPLATE/config.yml"] = config
FILES["ExploitProtection/.github/PULL_REQUEST_TEMPLATE.md"] = pr_template

for src_key in ("Cripple-NetStrip", "BlackGlass"):
    FILES[f"{src_key}/.github/ISSUE_TEMPLATE/bug_report.yml"] = bug
    FILES[f"{src_key}/.github/ISSUE_TEMPLATE/feature_request.yml"] = feature
    FILES[f"{src_key}/.github/ISSUE_TEMPLATE/config.yml"] = config
    FILES[f"{src_key}/.github/PULL_REQUEST_TEMPLATE.md"] = pr_template

import json
manifest = {}
for rel, content in FILES.items():
    fp = os.path.join(ROOT, rel.replace("/", "__"))
    open(fp, "w", encoding="utf-8", newline="").write(content)
    repo = rel.split("/")[0]
    path_in_repo = rel[len(repo) + 1:]
    manifest.setdefault(repo, []).append({"path": path_in_repo, "file": fp})

open(os.path.join(ROOT, "manifest.json"), "w").write(json.dumps(manifest))
print(f"generated {len(FILES)} files across {len(manifest)} repos")
