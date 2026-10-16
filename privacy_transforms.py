"""Pure string transforms for the privacy audit batch.

Each transform function takes a string and returns a string with no file
I/O, no subprocess calls, and no mutation of arguments.  The module also
exposes a small set of read-only constants (REL_NEEDED, INLINE_STARS,
XP_RELEASE_TAG, BAD_WIN_LINES, MIT_LICENSE, etc.) which the orchestrator
and tests may consume.

Side-effect-free design lets the unit-test suite run instantly and stay
isolated from the orchestrator.  Tests import these functions and assert
post-conditions on in-memory fixtures; the orchestrator (batch_privacy.py)
imports them and applies them to files.
"""
from __future__ import annotations

import json
import re

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

REL_NEEDED = "noopener noreferrer nofollow no-referrer"
REL_ATTR = f'rel="{REL_NEEDED}"'

# Hardcoded star counts kept in sync with the last committed snapshot.
# Drift is fine: these are display-only and get overwritten on the next
# stat-refresh cycle.
INLINE_STARS: dict[str, int] = {
    "ExploitProtection": 85,
    "dnscrypt-proxy-gui": 27,
    "BlackGlass": 9,
    "Cripple-NetStrip": 3,
    "HoneyScan": 2,
    "SystemMonitor": 0,
    "LANScan": 0,
}

# Release tag to pin ExploitProtection downloads to. Bump when releasing.
XP_RELEASE_TAG = "v1.1.0"

# Exact lines to strip from windows_hardening.cmd (telemetry opt-ins).
BAD_WIN_LINES: frozenset[str] = frozenset({
    "powershell.exe Set-MpPreference -MAPSReporting Advanced",
    "powershell.exe Set-MpPreference -SubmitSamplesConsent 0",
})


# ---------------------------------------------------------------------------
# #1 - drop the agent-commits row from stats
# ---------------------------------------------------------------------------

def fix_stats_py(text: str) -> str:
    """Remove the opencode-agent counter from update_stats.py."""
    text = re.sub(r"^AGENT_EMAIL = .*\n", "", text, flags=re.MULTILINE)
    # Drop the agent_q + agent_commits pair (must be adjacent lines).
    text = re.sub(
        r"^agent_q = quote\(.*\nagent_commits = gh\(f\"/search/commits\?q=\{agent_q\}\"\)\[\"total_count\"\]\n",
        "", text, flags=re.MULTILINE)
    text = re.sub(
        r"# Commits pushed via LLM agents are authored with the agent identity.*?\n",
        "", text)
    text = re.sub(
        "    \\(\"" + "\U0001f916" + " Agent-assisted commits\".*?\\),\n",
        "", text)
    return text


def fix_stats_svg(text: str) -> str:
    """Remove the agent row from stats.svg and resize the canvas."""
    text = re.sub(
        '    <circle cx="34" cy="284" r="4" fill="#7dcfff"/>\n'
        '    <text x="50" y="290"[^<]*</text>\n'
        '    <text x="476" y="290"[^<]*</text>\n', "", text)
    text = text.replace(
        'width="1040" height="350" viewBox="0 0 1040 350"',
        'width="1040" height="304" viewBox="0 0 1040 304"')
    text = text.replace('height="348"', 'height="302"')
    text = text.replace('y2="330"', 'y2="284"')
    return text


# ---------------------------------------------------------------------------
# #2 - remove vercel.app third-party stats card
# ---------------------------------------------------------------------------

def fix_profile_readme(text: str) -> str:
    return re.sub(
        r'  <a href="https://github\.com/neohiro">'
        r'<img src="https://github-readme-stats-git-masterrstaa-rickstaa\.vercel\.app[^"]*"[^>]*/></a>\s*\n',
        "", text)


# ---------------------------------------------------------------------------
# #3 - harden outbound sponsor links
# ---------------------------------------------------------------------------

def _add_rel_if_missing(match: re.Match) -> str:
    """Insert the rel= attribute into an opening <a ...> tag, but only if
    the tag does not already have one. The match must be the full tag
    including the closing '>'."""
    tag = match.group(0)
    if "rel=" in tag:
        return tag
    return tag[:-1] + f" {REL_ATTR}>"


_HARDEN_TARGETS: tuple[re.Pattern[str], ...] = tuple(re.compile(p) for p in (
    r'<a class="btn sponsor" href="[^"]*">',
    r'<a class="btn patreon" href="[^"]*">',
    r'<a class="btn linktree" href="[^"]*">',
    r'<a href="https://(?:github\.com/sponsors|www\.patreon\.com|linktr\.ee)[^"]*">',
    r'<a href="https://github\.com/sponsors/[^"]*">',
))


def harden_links(text: str) -> str:
    for pat in _HARDEN_TARGETS:
        text = pat.sub(_add_rel_if_missing, text)
    return text


# ---------------------------------------------------------------------------
# #4 - replace shields.io star badges with inline text
# ---------------------------------------------------------------------------

def strip_shields(text: str) -> str:
    # Drop generic shields.io badge images (consume any leading indent too)
    text = re.sub(
        r'(?m)^[ \t]*<img src="https://img\.shields\.io/badge/[^"]*"[^>]*/>[ \t]*\n',
        "", text)
    text = re.sub(
        r"(?m)^[ \t]*\[!\[([^\]]*)\]\(https://img\.shields\.io/[^)]*\)\]\([^)]*\)[ \t]*\n",
        "", text)
    # Star badges: two URL formats seen in the wild.
    for name, stars in INLINE_STARS.items():
        text = re.sub(
            r'!\[\]\(https://img\.shields\.io/badge/%E2%AD%90-' + re.escape(name) + r'-\w+\)',
            f"\u2605 {stars}", text)
        text = re.sub(
            r'!\[(' + re.escape(name) + r')\]\(https://img\.shields\.io/github/stars/[^)]*\)',
            f"\u2605 {stars}", text)
    return text


# ---------------------------------------------------------------------------
# #5 - remove api.github.com preconnect
# ---------------------------------------------------------------------------

def fix_preconnect(text: str) -> str:
    return re.sub(
        r'<link rel="preconnect" href="https://api\.github\.com" crossorigin>\s*\n', "", text)


# ---------------------------------------------------------------------------
# #6 - remove live GitHub API fetch (multiple file shapes)
# ---------------------------------------------------------------------------

def fix_pages_main(text: str) -> str:
    text = re.sub(
        r"cachedJson\([^)]*\)\s*\n\s*\.then\(repos => \{.*?\.catch\(\(\) => \{\}\);",
        "/* live star refresh removed - site uses committed snapshot only */",
        text, flags=re.DOTALL)
    return text


def fix_per_repo_html(text: str) -> str:
    """Strip self-contained cachedJson + sessionStorage + live api.github.com
    call from per-repo HTML pages. The static ★ count in the markup stays
    visible; only the client-side overwriter script is removed."""
    text = re.sub(
        r'<script>\s*\n\s*/\* reveal \+ live star count.*?</script>\s*\n',
        "", text, flags=re.DOTALL)
    text = re.sub(
        r"const TTL = .*?function cachedJson\(key, url\) \{.*?\n\}\s*",
        "", text, flags=re.DOTALL)
    text = re.sub(
        r"cachedJson\([^)]*\)\s*\n\s*\.then\(repos => \{.*?\.catch\(\(\) => \{\}\);",
        "/* live star refresh removed */", text, flags=re.DOTALL)
    return text


def fix_index_html(text: str) -> str:
    """Drop the live-fetch block from index.html but keep the cachedJson
    helper that other site code depends on."""
    text = re.sub(
        r"/\* ---- live star counts.*?\.catch\(\(\) => \{\}\);\s*",
        "/* live star counts: removed - site uses committed snapshot only */\n",
        text, flags=re.DOTALL)
    return text


def fix_fp_index_html(text: str) -> str:
    """Drop the 'fresh path' live fetch from frenzypenguin-media-site.
    The site already loads repos.json (line ~380), so the live fetch is
    a redundant backup that should go."""
    text = re.sub(
        r"/\* fresh path: live API via sessionStorage cache \*/.*?\.catch\(\(\) => \{\s*if \(!dataDone\) \{.*?dataDone = true; if \(pendingName\) routeHash\(\);\s*\}\s*\}\);\s*",
        "/* live fresh path removed - committed repos.json is the only data source */\n",
        text, flags=re.DOTALL)
    return text


# ---------------------------------------------------------------------------
# #7 + #9 - clean repos.json (strip sensitive fields, drop auto-resume)
# ---------------------------------------------------------------------------

_SENSITIVE_REPO_FIELDS = ("stargazers_count", "forks_count", "pushed_at")


def _detect_json_indent(text: str) -> int:
    """Return the leading whitespace width of the first JSON object/array
    open-bracket at the top level's child.  This matches what
    ``json.dumps(indent=N)`` would produce, so the round-trip is stable.

    Falls back to 4 for top-level scalars, empty input, or unparseable text.
    """
    for line in text.splitlines():
        if not line or line[0] not in " \t":
            continue
        for i, ch in enumerate(line):
            if ch not in " \t":
                if ch in "{[":
                    return i
                if ch in ('"', "'"):
                    # A key at this level = previous level's open-bracket indent.
                    return max(i - 1, 1)
                break
    return 4


def fix_repos_json(text: str) -> str:
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError("repos.json: expected a JSON array at top level")
    for repo in data:
        if not isinstance(repo, dict):
            continue
        for k in _SENSITIVE_REPO_FIELDS:
            repo.pop(k, None)
    return json.dumps(data, indent=_detect_json_indent(text), ensure_ascii=False) + "\n"


def fix_repos_no_autorename(text: str) -> str:
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError("repos.json: expected a JSON array at top level")
    data = [r for r in data if r.get("name") != "auto-resume"]
    return json.dumps(data, indent=_detect_json_indent(text), ensure_ascii=False) + "\n"


# ---------------------------------------------------------------------------
# #8 - remove sessionStorage cache from shared core.js
# ---------------------------------------------------------------------------

_NEW_CORE_HELPER = (
    "/* ---- fetch helper (no client-side cache) ---- */\n"
    "function cachedJson(key, url) {\n"
    "  return fetch(url).then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); });\n"
    "}\n"
)


def fix_core_js(text: str) -> str:
    """Replace the sessionStorage-cached helper with a no-cache fetch wrapper."""
    text = re.sub(
        r"/\* ---- cached GitHub API[^*]*\*/\s*\n",
        "", text)
    text = re.sub(
        r"const TTL = .*?\nfunction cachedJson\(key, url\) \{.*?\n\}\s*\n",
        _NEW_CORE_HELPER, text, flags=re.DOTALL)
    return text


# ---------------------------------------------------------------------------
# #11 - pin ExploitProtection download URLs to a release tag
# ---------------------------------------------------------------------------

_OLD_XP_URL = "https://raw.githubusercontent.com/neohiro/ExploitProtection/M3T4P0D.3XPL01T/"
_NEW_XP_URL = f"https://raw.githubusercontent.com/neohiro/ExploitProtection/{XP_RELEASE_TAG}/"


def fix_xp_py(text: str) -> str:
    return text.replace(_OLD_XP_URL, _NEW_XP_URL)


# ---------------------------------------------------------------------------
# #16 - expand extension warning in windows README
# ---------------------------------------------------------------------------

_OLD_WIN_NOTE = (
    "> \u26a0\ufe0f **Note:** the script re-associates `.bat` and other script files to open in "
    "Notepad instead of executing. If you legitimately use these extensions you will need to run them "
    "manually from cmd/PowerShell or right-click \u2192 *Run as administrator*."
)
_NEW_WIN_NOTE = (
    "> \u26a0\ufe0f **Note:** the script changes the file association of `.bat`, `.cmd`, `.js`, "
    "`.jse`, `.vbs`, `.vbe`, `.hta`, `.wsf` and `.ps1` so they open in Notepad instead of "
    "executing. If you rely on any of these extensions you must run them manually from "
    "cmd/PowerShell or right-click \u2192 *Run as administrator*. Review the script before "
    "running if you use any of these file types."
)


def fix_win_readme(text: str) -> str:
    return text.replace(_OLD_WIN_NOTE, _NEW_WIN_NOTE)


# ---------------------------------------------------------------------------
# #18 - remove MAPSReporting/SubmitSamplesConsent from windows_hardening.cmd
# ---------------------------------------------------------------------------

def fix_win_cmd(text: str) -> str:
    """Strip telemetry lines, preserving both the line-ending style (LF/CRLF)
    and the trailing newline of the original file.  Re-running is a no-op."""
    lines = text.splitlines()
    out = [line.rstrip("\r") for line in lines if line.strip() not in BAD_WIN_LINES]
    # Detect line ending: prefer CRLF if the original used CRLF separators
    # (any \r\n pair), so the file is written back with the same convention
    # the editor / repo expects.
    crlf = "\r\n" in text
    sep = "\r\n" if crlf else "\n"
    new = sep.join(out)
    trailing = ""
    if text.endswith("\r\n"):
        trailing = "\r\n"
    elif text.endswith("\n"):
        trailing = "\n"
    return new + trailing


# ---------------------------------------------------------------------------
# #20 - remove sudo passwd root from ubuntu README
# ---------------------------------------------------------------------------

def fix_ubuntu_readme(text: str) -> str:
    return re.sub(r"\n```bash\nsudo passwd root\n```\n", "\n", text)


# ---------------------------------------------------------------------------
# #22 - fix ubuntusocks.sh (drop fast_open, drop password echo)
# ---------------------------------------------------------------------------

def fix_socks(text: str) -> str:
    text = re.sub(r'    "fast_open":true\n', "", text)
    text = re.sub(r'  echo "Generated password: \$PASSWORD"\n', "", text)
    return text


# ---------------------------------------------------------------------------
# #23 - gate disable_ipv6 behind --disable-ipv6 flag
# ---------------------------------------------------------------------------

_EUID_CHECK = '  echo "[ERROR] This script must be run as root."\n  exit 1\nfi\n'
_FLAG_BLOCK = (
    "\n# Parse CLI flags\n"
    "_disable_ipv6=false\n"
    'for arg in "$@"; do\n'
    '  case "$arg" in\n'
    "    --disable-ipv6) _disable_ipv6=true ;;\n"
    '    --help|-h) echo "Usage: $0 [--disable-ipv6]"; exit 0 ;;\n'
    "  esac\n"
    "done\n"
)

# Pre-compiled regexes for the flag-block collapse pattern.  The block text
# contains characters that are regex metacharacters ($, |, (, )) so each line
# is escaped at module load, then joined into a single literal-block pattern.
_RE_META = re.compile(r"[.^$*+?()\[\]{}|\\]")
def _lit(s: str) -> str:
    """Escape regex metacharacters but leave `#`, letters, digits alone."""
    return _RE_META.sub(lambda m: "\\" + m.group(), s)

_FLAG_BLOCK_LINES = "\n".join(
    _lit(line) for line in _FLAG_BLOCK.lstrip("\n").rstrip("\n").split("\n")
) + "\n"
# Match 1+ consecutive flag blocks (with optional blank lines between them).
_FLAG_BLOCK_COLLAPSE_RE = re.compile(
    "(?:" + _FLAG_BLOCK_LINES + "(?:\n+" + _FLAG_BLOCK_LINES + ")*)+"
)


def _collapse_flag_blocks(text: str) -> str:
    """Reduce N consecutive copies of the flag block down to exactly 1.

    Non-consecutive duplicates (e.g. separated by unrelated code) are left
    alone on purpose — the user may have intentionally added a second block
    in a different code path.
    """
    while True:
        new = _FLAG_BLOCK_COLLAPSE_RE.sub(_FLAG_BLOCK_LINES, text)
        if new == text:
            return text
        text = new


def fix_ubuntu_install_script(text: str) -> str:
    """Gate disable_ipv6 behind --disable-ipv6 flag. Fully idempotent."""
    if "# Parse CLI flags" not in text:
        if _EUID_CHECK not in text:
            return text
        text = text.replace(_EUID_CHECK, _EUID_CHECK + _FLAG_BLOCK, 1)
        text = re.sub(
            r"^disable_ipv6 #  <--  WARNING.*$",
            'if [ "$_disable_ipv6" = true ]; then disable_ipv6; fi  # opt-in via --disable-ipv6',
            text, flags=re.MULTILINE)
        return text
    return _collapse_flag_blocks(text)


# ---------------------------------------------------------------------------
# #24 - replace placeholder password in SHADOWSOCKS-LIBEV.md
# ---------------------------------------------------------------------------

_SS_INSTRUCTION_MARKER = "> openssl rand -base64 32\n> ```\n"


def fix_ss_md(text: str) -> str:
    """Replace placeholder password and append openssl-rand instructions.

    Idempotent: the function detects the presence of the previously-appended
    instruction block and skips re-insertion on subsequent runs.
    """
    text = text.replace(
        '"password":"PWRD<<<<<<<<<<<<<"',
        '"password":"<CHANGE_ME>"',
    )
    if _SS_INSTRUCTION_MARKER in text:
        return text
    instruction = (
        "\n> **IMPORTANT:** Replace `<CHANGE_ME>` with a strong, randomly "
        "generated password.\n"
        "> Generate one with:\n"
        "> ```bash\n"
        "> openssl rand -base64 32\n"
        "> ```\n"
    )
    text = re.sub(r"(\n\}\s*\n```)", r"\1" + instruction, text, count=1)
    return text


# ---------------------------------------------------------------------------
# #43 - remove 404 release.yml Build Status badges
# ---------------------------------------------------------------------------

_BADGE_PAT = re.compile(
    r"(?m)^[ \t]*"  # consume any leading whitespace on the line
    r"\[!\[Build Status\]\(https://github\.com/[\w-]+/[\w-]+/actions/"
    r"workflows/release\.yml/badge\.svg\)\]\([^)]+\)[ \t]*\n"
)


def remove_badges(text: str) -> str:
    return _BADGE_PAT.sub("", text)


# ---------------------------------------------------------------------------
# LICENSE documents
# ---------------------------------------------------------------------------

MIT_LICENSE = """MIT License

Copyright (c) 2025 FrenzyPenguin Media

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

CC_DATA_LICENSE = """Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)

The XploitProtection.xml mitigation database (the "Data") is licensed under
Creative Commons Attribution-ShareAlike 4.0 International.

Full terms: https://creativecommons.org/licenses/by-sa/4.0/

You are free to:
  - Share - copy and redistribute the material in any medium or format
  - Adapt - remix, transform, and build upon the material for any purpose,
    even commercially

Under the following terms:
  - Attribution - You must give appropriate credit and indicate if changes
    were made. You may do so in any reasonable manner, but not in any way
    that suggests the licensor endorses you or your use.
  - ShareAlike - If you remix, transform, or build upon the material, you
    must distribute your contributions under the same license as the
    original.

XploitProtection.xml aggregates community-contributed settings credited in
the project README's "Merged Repositories" section.
"""

DUAL_NOTICE = """Copyright (c) 2025 FrenzyPenguin Media

This project uses a DUAL LICENSE model:

  - LICENSE-CODE (MIT)         covers the Python source code and all
                               executable scripts in this repository.
  - LICENSE-DATA (CC BY-SA 4.0) covers XploitProtection.xml, the bundled
                               mitigation settings catalog.

See the respective LICENSE-CODE and LICENSE-DATA files for full terms.
"""


def fix_xp_license(text: str) -> str:
    return DUAL_NOTICE


# ---------------------------------------------------------------------------
# Governance documents (org-level SECURITY.md / COC / CONTRIBUTING)
# ---------------------------------------------------------------------------

SECURITY_MD = """# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in any project under the
**FrenzyPenguin Media** or **neohiro** GitHub organisation, please report
it privately so we can address it before it is publicly disclosed.

**Please do not open a public GitHub issue for security bugs.**

### How to report

1. Navigate to the repository's **Security** tab (under the shield icon).
2. Click **Report a vulnerability** and fill in the template.
3. Alternatively, contact maintainers via the channels on
   [linktr.ee/frenzypenguin.media](https://linktr.ee/frenzypenguin.media).

We aim to acknowledge reports within **48 hours** and to provide a
resolution timeline within **30 days**. We follow the GitHub
[Coordinated Vulnerability Disclosure][cvd] policy.

[cvd]: https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-disclosure/security-vulnerabilities

### What to include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- (Optional) Suggested fix

### What to expect

- We will not pursue legal action against good-faith researchers.
- We will credit reporters in the advisory if desired.
- We will keep you updated throughout the remediation process.

## Security hardening projects

These projects are **defensive tools** - please do not use them for
unauthorised testing of systems you do not own or have explicit
permission to test.
"""

COC_MD = """# Contributor Covenant Code of Conduct

## Our Pledge

We as members, contributors, and leaders pledge to make participation in
our community a harassment-free experience for everyone, regardless of
age, body size, visible or invisible disability, ethnicity, sex
characteristics, gender identity and expression, level of experience,
education, socio-economic status, nationality, personal appearance,
race, religion, or sexual identity and orientation.

## Our Standards

Examples of behaviour that contributes to a positive environment:

* Using welcoming and inclusive language
* Being respectful of differing viewpoints and experiences
* Gracefully accepting constructive criticism
* Focusing on what is best for the community
* Showing empathy towards other community members

Examples of unacceptable behaviour:

* The use of sexualised language or imagery and unwelcome sexual
  attention or advances
* Trolling, insulting or derogatory comments, and personal or
  political attacks
* Public or private harassment
* Publishing others' private information without explicit permission
* Other conduct which could reasonably be considered inappropriate

## Enforcement

Instances of abusive, harassing, or otherwise unacceptable behaviour
may be reported by contacting the project team via the
[Security tab](https://github.com/neohiro/.github/security).
All complaints will be reviewed and investigated and will result in a
response that is deemed necessary and appropriate. Project maintainers
are obligated to maintain confidentiality.

## Attribution

This Code of Conduct is adapted from the [Contributor Covenant][homepage],
version 2.1, available at
https://www.contributor-covenant.org/version/2/1/code_of_conduct.html.

[homepage]: https://www.contributor-covenant.org
"""

CONTRIBUTING_MD = """# Contributing

Thank you for your interest in contributing to FrenzyPenguin Media /
neohiro projects.

## Getting started

1. **Fork** the repository you want to improve.
2. **Clone** your fork locally.
3. **Create a branch**: `git checkout -b fix/my-fix`
4. **Make your changes** - keep them focused and small.
5. **Test** your changes before submitting a pull request.
6. **Open a PR** against the `main` branch.

## Pull request checklist

- [ ] My code follows the existing style of this project.
- [ ] I have added or updated tests for new behaviour.
- [ ] I have added or updated documentation for any user-facing change.
- [ ] Any new binary assets are verified by checksum and signed where
      possible.
- [ ] I have not committed secrets, credentials or private data.

## Reporting bugs

Please open a **GitHub Issue** using the Bug Report template. Include:

- Your operating system and version
- Steps to reproduce the issue
- Expected vs actual behaviour
- Python/interpreter version if applicable

## Security disclosures

See [SECURITY.md](SECURITY.md) - do **not** open a public issue for
security vulnerabilities.

## License

By submitting a contribution, you agree that your work will be licensed
under the project's applicable license (see each repository's `LICENSE`
file).
"""


__all__ = (
    "REL_NEEDED",
    "REL_ATTR",
    "INLINE_STARS",
    "XP_RELEASE_TAG",
    "BAD_WIN_LINES",
    "fix_stats_py",
    "fix_stats_svg",
    "fix_profile_readme",
    "harden_links",
    "strip_shields",
    "fix_preconnect",
    "fix_pages_main",
    "fix_per_repo_html",
    "fix_index_html",
    "fix_fp_index_html",
    "fix_repos_json",
    "fix_repos_no_autorename",
    "fix_core_js",
    "fix_xp_py",
    "fix_win_readme",
    "fix_win_cmd",
    "fix_ubuntu_readme",
    "fix_socks",
    "fix_ubuntu_install_script",
    "fix_ss_md",
    "remove_badges",
    "fix_xp_license",
    "MIT_LICENSE",
    "CC_DATA_LICENSE",
    "DUAL_NOTICE",
    "SECURITY_MD",
    "COC_MD",
    "CONTRIBUTING_MD",
)
