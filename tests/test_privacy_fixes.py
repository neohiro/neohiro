"""Tests for the privacy audit transforms in privacy_transforms.py.

Each test is fully self-contained: it builds a small fixture that mirrors
the actual original (pre-fix) file content, runs the transform function
directly, and asserts the expected post-condition.

The transforms are imported from privacy_transforms so the test suite
runs without touching the filesystem or invoking subprocesses.

Run:  python tests/test_privacy_fixes.py
Exit code 0 on success.
"""
from __future__ import annotations

import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import privacy_transforms as pt  # noqa: E402

AUTO_RESUME = {
    "name": "auto-resume",
    "html_url": "https://github.com/neohiro/auto-resume",
    "description": "Self-healing OpenCode sessions",
    "stargazers_count": 0,
    "forks_count": 0,
    "language": "JavaScript",
    "topics": ["ai-agents", "autopilot"],
    "pushed_at": "2026-08-24T22:47:07Z",
}

EP = {
    "name": "ExploitProtection",
    "html_url": "https://github.com/neohiro/ExploitProtection",
    "description": "Windows Exploit Protection Settings (Ultimate) GUI",
    "stargazers_count": 85,
    "forks_count": 11,
    "language": "Python",
    "topics": ["anonymous", "antibot"],
    "pushed_at": "2026-08-24T11:58:47Z",
}


# Original update_stats.py snippet (pre-fix)
# Pattern: agent_q and agent_commits are adjacent lines, no blank line between
STATS_PY_ORIG = (
    "import re\n"
    "import subprocess\n"
    "import urllib.parse\n"
    "from urllib.request import Request, urlopen\n"
    "\n"
    "USER = \"neohiro\"\n"
    "AGENT_EMAIL = \"opencode-agent@users.noreply.github.com\"\n"
    "TOKEN = \"ghp_REDACTED\"\n"
    "\n"
    "def gh(p):\n"
    "    req = Request(\"https://api.github.com\" + p, headers={\"Authorization\": f\"Bearer {TOKEN}\"})\n"
    "    return json.loads(urlopen(req).read())\n"
    "\n"
    "user = gh(\"/users/\" + USER)\n"
    "agent_q = quote(f\"user:{USER} author-email:{AGENT_EMAIL}\")\n"
    "agent_commits = gh(f\"/search/commits?q={agent_q}\")[\"total_count\"]\n"
    "stars = sum(r[\"stargazers_count\"] for r in gh(\"/users/\" + USER + \"/repos\"))\n"
    "contrib = gh(f\"/search/commits?q=user:{USER}\")[\"total_count\"]\n"
    "rows = [\n"
    "    (\"\U0001f4e6 Total stars earned\", fmt(stars)),\n"
    "    (\"\U0001f465 Followers\", fmt(user[\"followers\"])),\n"
    "    (\"\U0001f4e2 Public repositories\", fmt(user[\"public_repos\"])),\n"
    "    (\"\U0001f525 Contributions (last year)\", fmt(contrib)),\n"
    "    (\"\U0001f916 Agent-assisted commits\", fmt(agent_commits)),\n"
    "]\n"
    "for label, value in rows:\n"
    "    print(label, value)\n"
)


# Original stats.svg snippet (pre-fix, 350px tall with 5 rows).
# Pattern: agent row uses cy="284" r="4" fill="#7dcfff" then 4-space-indented text lines
STATS_SVG_ORIG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="1040" height="350" viewBox="0 0 1040 350" role="img">\n'
    '  <rect x="1" y="1" width="1038" height="348" rx="14" fill="#16161e" stroke="#2a2e42" stroke-width="1"/>\n'
    '  <text x="28" y="52">neohiro Stats</text>\n'
    '  <line x1="28" y1="68" x2="1012" y2="68"/>\n'
    '  <line x1="520" y1="86" x2="520" y2="330"/>\n'
    '  <circle cx="34" cy="100" r="4"/>\n'
    '  <text x="50" y="106">\U0001f4e6 Total stars earned</text>\n'
    '  <circle cx="34" cy="146" r="4"/>\n'
    '  <text x="50" y="152">\U0001f465 Followers</text>\n'
    '  <circle cx="34" cy="192" r="4"/>\n'
    '  <text x="50" y="198">\U0001f4e2 Public repositories</text>\n'
    '  <circle cx="34" cy="238" r="4"/>\n'
    '  <text x="50" y="244">\U0001f525 Contributions (last year)</text>\n'
    '    <circle cx="34" cy="284" r="4" fill="#7dcfff"/>\n'
    '    <text x="50" y="290" font-size="15" fill="#8fa3b0">\U0001f916 Agent-assisted commits</text>\n'
    '    <text x="476" y="290" text-anchor="end" font-size="17" fill="#e8eef2">31</text>\n'
    '</svg>\n'
)


# Original core.js snippet (pre-fix, with sessionStorage)
CORE_JS_ORIG = (
    "/* Shared site core - SINGLE SOURCE OF TRUTH.\n"
    "   Edits belong HERE; build-sites.ps1 injects this into each index.html\n"
    "   between __CORE_START__/__CORE_END__ markers. Never edit injected copies. */\n"
    "\n"
    "/* ---- cached GitHub API (15-min sessionStorage TTL) ---- */\n"
    "const TTL = 15 * 60 * 1000;\n"
    "function cachedJson(key, url) {\n"
    "  try {\n"
    "    const c = JSON.parse(sessionStorage.getItem('gh:' + key) || 'null');\n"
    "    if (c && Date.now() - c.t < TTL) return Promise.resolve(c.d);\n"
    "  } catch (e) {}\n"
    "  return fetch(url).then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })\n"
    "    .then(d => { try { sessionStorage.setItem('gh:' + key, JSON.stringify({ t: Date.now(), d: d })); } catch (e) {} return d; });\n"
    "}\n"
    "\n"
    "const fmt = n => n >= 1000 ? (n / 1000).toFixed(1).replace(/\\.0$/, '') + 'k' : String(n);\n"
)


# Original profile README with vercel card + sponsor link
PROFILE_README_ORIG = (
    "# neohiro\n"
    "\n"
    "## Stats\n"
    '<p align="center">\n'
    '  <a href="https://github.com/neohiro">'
    '<img src="https://github-readme-stats-git-masterrstaa-rickstaa.vercel.app/api'
    '?username=neohiro&show_icons=true&theme=tokyonight&hide_border=true&count_private=true"'
    ' alt="GitHub stats" /></a>\n'
    '  <a href="https://github.com/neohiro">'
    '<img src="https://github-readme-stats-git-masterrstaa-rickstaa.vercel.app/api/top-langs/'
    '?username=neohiro&layout=compact&theme=tokyonight&hide_border=true" alt="Top languages" /></a>\n'
    '</p>\n'
    "\n"
    "## Links\n"
    '<a class="btn sponsor" href="https://github.com/sponsors/neohiro">Sponsor</a>\n'
    '<a class="btn patreon" href="https://www.patreon.com/frenzypenguin_media">Patreon</a>\n'
)


# Original README with shields star badge (github/stars/ format from actual file)
README_WITH_BADGE = (
    "# ExploitProtection\n"
    "\n"
    "| [![ExploitProtection](https://img.shields.io/github/stars/neohiro/ExploitProtection"
    "?style=flat&label=%E2%AD%90%20ExploitProtection)]"
    "(https://github.com/neohiro/ExploitProtection) | Windows GUI |\n"
    "\n"
    "Body text.\n"
)


# Original ubuntusocks.sh (pre-fix) - uses 2-space indent for echo
UBUNTUSOCKS_ORIG = (
    "#!/bin/bash\n"
    'PASSWORD=$(openssl rand -base64 16)\n'
    '  echo "Generated password: $PASSWORD"\n'
    'cat <<EOF | sudo tee /etc/shadowsocks-libev/config.json\n'
    '{\n'
    '    "server":"0.0.0.0",\n'
    '    "server_port":8388,\n'
    '    "local_address":"127.0.0.1",\n'
    '    "local_port":1080,\n'
    '    "password":"$PASSWORD",\n'
    '    "timeout":300,\n'
    '    "method":"aes-256-gcm",\n'
    '    "fast_open":true\n'
    '}\n'
    'EOF\n'
)


# Original ubuntu README
UBUNTU_README_ORIG = (
    "# Ubuntu\n"
    "\n"
    "```bash\n"
    "sudo apt update && sudo apt upgrade -y\n"
    "```\n"
    "\n"
    "Set the root password:\n"
    "\n"
    "```bash\n"
    "sudo passwd root\n"
    "```\n"
    "\n"
    "Install extras:\n"
    "\n"
    "```bash\n"
    "sudo apt-get update && sudo apt-get upgrade -y\n"
    "```\n"
)


# Original shadowsocks doc
SS_DOC_ORIG = (
    "# Shadowsocks-libev\n"
    "\n"
    "Config example:\n"
    "\n"
    "```json\n"
    "{\n"
    '    "server":["::0", "0.0.0.0"],\n'
    '    "mode":"tcp_and_udp",\n'
    '    "server_port":8888,\n'
    '    "password":"PWRD<<<<<<<<<<<<<",\n'
    '    "method":"xchacha20-ietf-poly1305"\n'
    "}\n"
    "```\n"
)


# Original release.yml badge
README_WITH_BUILD_BADGE = (
    "# Title\n"
    "\n"
    "[![Build Status](https://github.com/neohiro/ExploitProtection/actions/workflows/"
    "release.yml/badge.svg)](https://github.com/neohiro/ExploitProtection/actions)\n"
    "\n"
    "Body text.\n"
)


class TestAgentRowRemoval(unittest.TestCase):
    def test_update_stats_py(self):
        out = pt.fix_stats_py(STATS_PY_ORIG)
        self.assertNotIn("AGENT_EMAIL", out)
        self.assertNotIn("agent_q", out)
        self.assertNotIn("agent_commits", out)
        self.assertNotIn("Agent-assisted", out)
        # Sanity: the rest is preserved
        self.assertIn("Total stars earned", out)
        self.assertIn("Followers", out)
        self.assertIn("Contributions (last year)", out)

    def test_stats_svg(self):
        out = pt.fix_stats_svg(STATS_SVG_ORIG)
        # Agent row removed
        self.assertNotIn("Agent-assisted", out)
        # Height reduced
        self.assertIn('height="304"', out)
        self.assertIn('viewBox="0 0 1040 304"', out)
        # Other rows preserved
        self.assertIn("Total stars earned", out)
        self.assertIn("Contributions (last year)", out)


class TestVercelCardRemoval(unittest.TestCase):
    def test_profile_readme(self):
        out = pt.fix_profile_readme(PROFILE_README_ORIG)
        self.assertNotIn("vercel.app", out)
        # Other content preserved
        self.assertIn("# neohiro", out)
        self.assertIn("## Links", out)


class TestLinkHardening(unittest.TestCase):
    def test_sponsor_and_patreon(self):
        out = pt.harden_links(PROFILE_README_ORIG)
        # Both sponsor and patreon links get the rel attribute
        self.assertGreaterEqual(out.count('rel="noopener noreferrer nofollow no-referrer"'), 2)

    def test_idempotent(self):
        text = (
            '<a class="btn sponsor" href="https://github.com/sponsors/neohiro" '
            'rel="noopener noreferrer nofollow no-referrer">Sponsor</a>\n'
        )
        out = pt.harden_links(text)
        # Should remain exactly 1
        self.assertEqual(out.count('rel="noopener noreferrer nofollow no-referrer"'), 1)
        # No double-attribute
        self.assertNotIn('rel="noopener noreferrer nofollow no-referrer" rel=', out)


class TestShieldsStrip(unittest.TestCase):
    def test_inline_replacement(self):
        out = pt.strip_shields(README_WITH_BADGE)
        # Star badge replaced with inline text
        self.assertIn("\u2605 85", out)
        self.assertNotIn("img.shields.io", out)
        # Other content preserved
        self.assertIn("# ExploitProtection", out)
        self.assertIn("Body text.", out)


class TestPreconnectRemoval(unittest.TestCase):
    def test_all_html(self):
        text = (
            "<!DOCTYPE html>\n"
            "<html>\n"
            "<head>\n"
            '<link rel="preconnect" href="https://api.github.com" crossorigin>\n'
            "<title>x</title>\n"
            "</head>\n"
            "<body></body>\n"
            "</html>\n"
        )
        out = pt.fix_preconnect(text)
        self.assertNotIn("api.github.com", out)
        self.assertIn("<title>x</title>", out)


class TestLiveAPIRemoval(unittest.TestCase):
    def test_pages_main(self):
        text = (
            "// boot\n"
            "cachedJson('neo-repos', 'https://api.github.com/users/neohiro/repos?per_page=100')\n"
            "  .then(repos => {\n"
            "    render(repos);\n"
            "  })\n"
            "  .catch(() => {});\n"
            "// end\n"
        )
        out = pt.fix_pages_main(text)
        self.assertNotIn("api.github.com/users", out)
        self.assertNotIn("cachedJson('neo-repos'", out)


class TestReposJson(unittest.TestCase):
    def test_strip_sensitive(self):
        data = [dict(EP), dict(AUTO_RESUME)]
        out = pt.fix_repos_json(json.dumps(data, indent=2))
        parsed = json.loads(out)
        for r in parsed:
            self.assertNotIn("stargazers_count", r)
            self.assertNotIn("forks_count", r)
            self.assertNotIn("pushed_at", r)

    def test_remove_auto_resume(self):
        data = [dict(EP), dict(AUTO_RESUME)]
        out = pt.fix_repos_no_autorename(json.dumps(data, indent=2))
        parsed = json.loads(out)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["name"], "ExploitProtection")

    def test_round_trip_shrinkage(self):
        data = [dict(EP), dict(AUTO_RESUME)]
        out = pt.fix_repos_json(json.dumps(data, indent=2))
        out = pt.fix_repos_no_autorename(out)
        parsed = json.loads(out)
        self.assertEqual(parsed, [{
            "name": "ExploitProtection",
            "html_url": "https://github.com/neohiro/ExploitProtection",
            "description": "Windows Exploit Protection Settings (Ultimate) GUI",
            "language": "Python",
            "topics": ["anonymous", "antibot"],
        }])


class TestCoreJsDeCache(unittest.TestCase):
    def test_no_sessionstorage(self):
        out = pt.fix_core_js(CORE_JS_ORIG)
        self.assertNotIn("sessionStorage", out)
        self.assertNotIn("const TTL", out)
        # The replacement helper should still be present
        self.assertIn("function cachedJson", out)
        # Other content preserved
        self.assertIn("const fmt", out)


class TestExploitProtectionPinning(unittest.TestCase):
    def test_url_replaced(self):
        text = (
            'file_url = "https://raw.githubusercontent.com/neohiro/ExploitProtection/'
            'M3T4P0D.3XPL01T/XploitProtection.xml"\n'
            'url1 = "https://raw.githubusercontent.com/neohiro/ExploitProtection/'
            'M3T4P0D.3XPL01T/media/Exploitprotectionlogo3.png"\n'
        )
        out = pt.fix_xp_py(text)
        self.assertNotIn("M3T4P0D.3XPL01T", out)
        self.assertIn("v1.1.0", out)


class TestWindowsCmdCleanup(unittest.TestCase):
    def test_maps_and_submitsamples_removed(self):
        text = (
            ":: line a\n"
            "powershell.exe Set-MpPreference -PUAProtection enable\n"
            "powershell.exe Set-MpPreference -MAPSReporting Advanced\n"
            "powershell.exe Set-MpPreference -SubmitSamplesConsent 0\n"
            ":: line b\n"
        )
        out = pt.fix_win_cmd(text)
        self.assertNotIn("MAPSReporting", out)
        self.assertNotIn("SubmitSamplesConsent", out)
        self.assertIn("PUAProtection", out)
        self.assertIn(":: line a", out)
        self.assertIn(":: line b", out)


class TestUbuntuReadme(unittest.TestCase):
    def test_passwd_root_removed(self):
        out = pt.fix_ubuntu_readme(UBUNTU_README_ORIG)
        # The dangerous line is gone
        self.assertNotIn("sudo passwd root", out)
        # The fenced code block surrounding it is also gone
        self.assertNotIn("```bash\nsudo passwd root", out)
        # Other commands preserved
        self.assertIn("sudo apt update", out)
        self.assertIn("sudo apt-get", out)


class TestSocksFix(unittest.TestCase):
    def test_fast_open_and_echo_removed(self):
        out = pt.fix_socks(UBUNTUSOCKS_ORIG)
        self.assertNotIn("fast_open", out)
        self.assertNotIn("Generated password", out)
        # Other content preserved
        self.assertIn("PASSWORD=", out)
        self.assertIn("aes-256-gcm", out)


class TestShadowsocksDocFix(unittest.TestCase):
    def test_placeholder_replaced(self):
        out = pt.fix_ss_md(SS_DOC_ORIG)
        self.assertIn("<CHANGE_ME>", out)
        self.assertNotIn("PWRD<<<<<<<<<<<<<", out)
        # Should add openssl rand instruction
        self.assertIn("openssl rand", out)


class TestBadgeRemoval(unittest.TestCase):
    def test_release_badge_removed(self):
        out = pt.remove_badges(README_WITH_BUILD_BADGE)
        self.assertNotIn("Build Status", out)
        self.assertNotIn("release.yml/badge.svg", out)
        self.assertIn("# Title", out)
        self.assertIn("Body text.", out)

    def test_idempotent(self):
        text = "# Title\n\nBody\n"
        out = pt.remove_badges(text)
        self.assertEqual(out, text)


class TestIntegration(unittest.TestCase):
    """End-to-end: chained transforms on a fixture profile README."""

    def test_integration_profile_readme(self):
        out = pt.harden_links(
            pt.strip_shields(
                pt.fix_profile_readme(PROFILE_README_ORIG)))
        self.assertNotIn("vercel.app", out)
        self.assertNotIn("img.shields.io", out)
        # Sponsor link hardened
        self.assertIn('rel="noopener noreferrer nofollow no-referrer"', out)


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases and robustness that the main fixtures don't hit."""

    def test_fix_win_cmd_preserves_trailing_newline(self):
        """A previously-fixed bug: splitlines() + join('\\n') would strip
        the trailing newline. The transform must keep file-end semantics."""
        text = "line1\nline2\n"
        out = pt.fix_win_cmd(text)
        self.assertTrue(out.endswith("\n"), "trailing newline must be preserved")
        self.assertEqual(out, text)

    def test_fix_win_cmd_preserves_crlf(self):
        """CRLF (Windows line endings) must be preserved through the transform."""
        text = "line1\r\nline2\r\n"
        out = pt.fix_win_cmd(text)
        self.assertEqual(out, text, "CRLF must not be mutated to LF")
        self.assertIn("\r\n", out)

    def test_fix_win_cmd_preserves_no_trailing_newline(self):
        text = "line1\nline2"
        out = pt.fix_win_cmd(text)
        self.assertFalse(out.endswith("\n"), "no spurious newline added")

    def test_fix_win_cmd_strips_bad_line(self):
        text = "good\npowershell.exe Set-MpPreference -MAPSReporting Advanced\nalso good\n"
        out = pt.fix_win_cmd(text)
        self.assertNotIn("MAPSReporting", out)
        self.assertIn("good", out)
        self.assertIn("also good", out)

    def test_fix_repos_json_rejects_non_list(self):
        with self.assertRaises(ValueError):
            pt.fix_repos_json('{"not": "a list"}')

    def test_fix_repos_json_skips_non_dict_entries(self):
        text = '[{"name": "a"}, "bogus", 42]'
        out = pt.fix_repos_json(text)
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["name"], "a")
        # Non-dict entries round-trip unchanged
        self.assertEqual(parsed[1], "bogus")
        self.assertEqual(parsed[2], 42)

    def test_fix_per_repo_html_strips_cachedJson_and_sessionStorage(self):
        text = (
            "<html><body>\n"
            "<script>\n"
            "/* reveal + live star count (self-contained per-page core) */\n"
            "const TTL = 15 * 60 * 1000;\n"
            "function cachedJson(key, url) {\n"
            "  return fetch(url).then(r => r.json());\n"
            "}\n"
            "cachedJson('neo-repos', 'https://api.github.com/users/x/repos')\n"
            "  .then(repos => {})\n"
            "  .catch(() => {});\n"
            "</script>\n"
            "</body></html>\n"
        )
        out = pt.fix_per_repo_html(text)
        self.assertNotIn("cachedJson", out)
        self.assertNotIn("sessionStorage", out)
        self.assertNotIn("api.github.com", out)
        self.assertNotIn("const TTL", out)
        # Structure preserved
        self.assertIn("<html>", out)
        self.assertIn("</html>", out)

    def test_fix_pages_main_is_idempotent(self):
        """Running fix_pages_main twice produces the same output as once."""
        text = (
            "// boot\n"
            "cachedJson('x', 'https://api.github.com/users/x/repos')\n"
            "  .then(repos => { render(repos); })\n"
            "  .catch(() => {});\n"
        )
        once = pt.fix_pages_main(text)
        twice = pt.fix_pages_main(once)
        self.assertEqual(once, twice)

    def test_harden_links_noop_on_plain_text(self):
        text = "# Just a README\n\nNo HTML here.\n"
        self.assertEqual(pt.harden_links(text), text)

    def test_strip_shields_noop_on_plain_text(self):
        text = "# README\n\nNo badges here.\n"
        self.assertEqual(pt.strip_shields(text), text)

    def test_fix_preconnect_noop_on_clean_html(self):
        text = "<html><head><title>x</title></head><body></body></html>\n"
        self.assertEqual(pt.fix_preconnect(text), text)

    def test_fix_xp_py_idempotent(self):
        text = "url = 'https://raw.githubusercontent.com/neohiro/ExploitProtection/v1.1.0/x.xml'\n"
        out = pt.fix_xp_py(text)
        self.assertEqual(out, text)

    def test_remove_badges_handles_multiple_badges(self):
        text = (
            "# R1\n"
            "[![Build Status](https://github.com/a/b/actions/workflows/release.yml/badge.svg)](https://github.com/a/b/actions)\n"
            "body1\n"
            "[![Build Status](https://github.com/c/d/actions/workflows/release.yml/badge.svg)](https://github.com/c/d/actions)\n"
            "body2\n"
        )
        out = pt.remove_badges(text)
        self.assertNotIn("Build Status", out)
        self.assertEqual(out.count("\n"), text.count("\n") - 2)
        self.assertIn("body1", out)
        self.assertIn("body2", out)

    def test_inline_stars_is_non_empty(self):
        """Sanity: the star map drives strip_shields; an empty map would
        silently break badge replacement and ship stale UI text."""
        self.assertGreater(len(pt.INLINE_STARS), 0)

    def test_xp_release_tag_is_pinned(self):
        """Sanity: the pin target must be a known release tag, not 'main'."""
        self.assertTrue(pt.XP_RELEASE_TAG.startswith("v"),
                        f"release tag should be version-pinned, got {pt.XP_RELEASE_TAG!r}")

    def test_fix_ss_md_idempotent(self):
        """Running fix_ss_md twice should produce identical output."""
        out1 = pt.fix_ss_md(SS_DOC_ORIG)
        out2 = pt.fix_ss_md(out1)
        self.assertEqual(out1, out2)

    def test_fix_ubuntu_install_script_idempotent(self):
        """The flag block should be inserted at most once."""
        script = (
            "#!/bin/bash\n"
            '  echo "[ERROR] This script must be run as root."\n  exit 1\nfi\n'
            "\n# Parse CLI flags\n"
            "_disable_ipv6=false\n"
            'for arg in "$@"; do\n'
            '  case "$arg" in\n'
            "    --disable-ipv6) _disable_ipv6=true ;;\n"
            '    --help|-h) echo "Usage: $0 [--disable-ipv6]"; exit 0 ;;\n'
            "  esac\n"
            "done\n"
            "\necho done\n"
        )
        out1 = pt.fix_ubuntu_install_script(script)
        out2 = pt.fix_ubuntu_install_script(out1)
        self.assertEqual(out1, out2)
        self.assertEqual(out1.count("# Parse CLI flags"), 1)

    def test_fix_ubuntu_install_script_collapses_duplicates(self):
        """A file with 3 copies of the flag block should be reduced to 1."""
        flag = (
            "\n# Parse CLI flags\n"
            "_disable_ipv6=false\n"
            'for arg in "$@"; do\n'
            '  case "$arg" in\n'
            "    --disable-ipv6) _disable_ipv6=true ;;\n"
            '    --help|-h) echo "Usage: $0 [--disable-ipv6]"; exit 0 ;;\n'
            "  esac\n"
            "done\n"
        )
        script = "header\n" + (flag * 3) + "footer\n"
        out = pt.fix_ubuntu_install_script(script)
        self.assertEqual(out.count("# Parse CLI flags"), 1)
        # And idempotent
        out2 = pt.fix_ubuntu_install_script(out)
        self.assertEqual(out, out2)

    def test_fix_ubuntu_install_script_adds_flag(self):
        """On a script that lacks the flag, the transform adds it."""
        script = (
            "#!/bin/bash\n"
            '  echo "[ERROR] This script must be run as root."\n  exit 1\nfi\n'
            "disable_ipv6 #  <--  WARNING\n"
            "echo done\n"
        )
        out = pt.fix_ubuntu_install_script(script)
        self.assertIn("# Parse CLI flags", out)
        self.assertIn("_disable_ipv6=false", out)
        self.assertIn('if [ "$_disable_ipv6" = true ]; then disable_ipv6; fi', out)

    def test_fix_xp_license_returns_dual_notice(self):
        """The transform replaces the existing LICENSE with the dual-notice text."""
        out = pt.fix_xp_license("Old proprietary license text")
        self.assertIn("DUAL LICENSE", out)
        self.assertIn("MIT", out)
        self.assertIn("CC BY-SA", out)
        # Idempotent: same input always produces same output.
        self.assertEqual(out, pt.fix_xp_license(out))

    def test_fix_repos_json_round_trip_through_serialise(self):
        """fix_repos_json must produce output that json.loads accepts and that
        contains no sensitive fields.  This is the full pipeline contract."""
        text = json.dumps([{
            "name": "ExploitProtection",
            "html_url": "https://github.com/neohiro/ExploitProtection",
            "stargazers_count": 99,
            "forks_count": 3,
            "pushed_at": "2026-08-27T00:00:00Z",
        }, {
            "name": "OtherRepo",
            "html_url": "https://github.com/neohiro/OtherRepo",
        }], indent=4)
        out = pt.fix_repos_json(text)
        parsed = json.loads(out)
        self.assertEqual(len(parsed), 2)
        self.assertNotIn("stargazers_count", parsed[0])
        self.assertNotIn("forks_count", parsed[0])
        self.assertNotIn("pushed_at", parsed[0])
        # Idempotent on the post-condition.
        self.assertEqual(out, pt.fix_repos_json(out))

    def test_fix_core_js_replaces_sessionstorage_with_fetch(self):
        """The post-condition is: no sessionStorage anywhere, and the new
        cachedJson helper is a thin fetch wrapper that does not cache."""
        text = (
            "/* ---- cached GitHub API ---- */\n"
            "const TTL = 600000;\n"
            "function cachedJson(key, url) {\n"
            "  const c = JSON.parse(sessionStorage.getItem('gh:' + key) || 'null');\n"
            "  if (c && Date.now() - c.t < TTL) return Promise.resolve(c.d);\n"
            "  return fetch(url).then(r => r.json())\n"
            "    .then(d => { sessionStorage.setItem('gh:' + key, JSON.stringify({t:Date.now(),d:d})); return d; });\n"
            "}\n"
        )
        out = pt.fix_core_js(text)
        self.assertNotIn("sessionStorage", out)
        self.assertNotIn("TTL", out)
        self.assertIn("function cachedJson", out)
        # Idempotent.
        self.assertEqual(out, pt.fix_core_js(out))

    def test_fix_pages_main_strips_live_fetch_and_is_idempotent(self):
        """The live-fetch block is replaced with a no-op comment; running the
        transform again is a no-op."""
        text = (
            "cachedJson('repos', 'https://api.github.com/orgs/neohiro/repos')\n"
            "  .then(repos => { console.log(repos); })\n"
            "  .catch(() => {});\n"
        )
        once = pt.fix_pages_main(text)
        self.assertNotIn("api.github.com", once)
        self.assertNotIn("cachedJson(", once)
        twice = pt.fix_pages_main(once)
        self.assertEqual(once, twice)

    def test_strip_shields_handles_inline_text_substitution(self):
        """The post-condition is: the badge markdown link is gone, replaced
        with a bare star-count string like '★ 27'."""
        text = (
            "Repo: ExploitProtection\n"
            "![ExploitProtection](https://img.shields.io/github/stars/neohiro/ExploitProtection?style=social)\n"
        )
        out = pt.strip_shields(text)
        self.assertNotIn("img.shields.io", out)
        # 85 is the hardcoded value for ExploitProtection in INLINE_STARS.
        self.assertIn("85", out)

    def test_harden_links_preserves_existing_rel(self):
        """If a target <a> already has rel=, do not duplicate it."""
        text = '<a class="btn sponsor" href="https://github.com/sponsors/me" rel="noopener">click</a>'
        out = pt.harden_links(text)
        # rel= should appear exactly once.
        self.assertEqual(out.count("rel="), 1)
        self.assertIn("noopener", out)

    def test_fix_preconnect_strips_only_api_github(self):
        """Other preconnect links must be preserved."""
        text = (
            '<link rel="preconnect" href="https://api.github.com" crossorigin>\n'
            '<link rel="preconnect" href="https://fonts.googleapis.com" crossorigin>\n'
        )
        out = pt.fix_preconnect(text)
        self.assertNotIn("api.github.com", out)
        self.assertIn("fonts.googleapis.com", out)

    def test_detect_json_indent_handles_2_and_4_space(self):
        """The detector must return the object-open indent so the round-trip
        via json.dumps(indent=N) is byte-identical to the source."""
        self.assertEqual(pt._detect_json_indent('[\n  {"a": 1}\n]\n'), 2)
        self.assertEqual(pt._detect_json_indent('[\n    {"a": 1}\n]\n'), 4)
        self.assertEqual(pt._detect_json_indent('[]\n'), 4)
        self.assertEqual(pt._detect_json_indent(''), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
