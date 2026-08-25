#!/usr/bin/env python3
"""Generate self-hosted GitHub stats & language SVG cards for the profile README."""
import json, subprocess, os, sys
from collections import defaultdict
from urllib.parse import quote

USER = "neohiro"

def gh(endpoint):
    r = subprocess.run(["gh", "api", endpoint], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"{endpoint}: {r.stderr.decode()[:120]}")
    return json.loads(r.stdout.decode("utf-8"))

def gql(query):
    r = subprocess.run(["gh", "api", "graphql", "-f", f"query={query}"],
                       capture_output=True, text=True, encoding="utf-8")
    out = json.loads(r.stdout)
    return out["data"]

# ---------- gather data ----------
user = gh(f"/users/{USER}")
followers = user["followers"]

repos = gh(f"/users/{USER}/repos?per_page=100&type=owner&sort=updated")
repos = [r for r in repos if not r.get("fork")]
total_stars = sum(r["stargazers_count"] for r in repos)
total_repos = len(repos)

contrib = gql('{ user(login: "%s") { contributionsCollection { contributionCalendar { totalContributions } } } }' % USER)
contributions = contrib["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]

# Commits pushed via LLM agents are authored with the agent identity, so they
# never show up in the contribution calendar — count them explicitly instead.
AGENT_EMAIL = "opencode-agent@users.noreply.github.com"
agent_q = quote(f"user:{USER} author-email:{AGENT_EMAIL}")
agent_commits = gh(f"/search/commits?q={agent_q}")["total_count"]

lang_bytes = defaultdict(int)
for r in repos:
    try:
        langs = gh(f"/repos/{USER}/{r['name']}/languages")
        for k, v in langs.items():
            lang_bytes[k] += v
    except Exception:
        pass

LANG_COLORS = {
    "Python": "#3572A5", "Batchfile": "#C1F12E", "Shell": "#89e051",
    "HTML": "#e34c26", "CSS": "#563d7c", "LSL": "#37548d",
    "PowerShell": "#012456", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "Dockerfile": "#384d54", "Makefile": "#427819",
}
top_langs = sorted(lang_bytes.items(), key=lambda kv: -kv[1])[:6]
total_lb = sum(lang_bytes.values()) or 1

# ---------- svg helpers ----------
FONT = "Segoe UI,Roboto,Helvetica,Arial,sans-serif"
BG, BORDER = "#16161e", "#2a2e42"
TITLE_C, TEXT_C, MUTED_C = "#70a5fd", "#e8eef2", "#8fa3b0"
ACCENTS = ["#70a5fd", "#bb9af7", "#9ece6a", "#ff9e64", "#7dcfff", "#f7768e"]

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")

def fmt(n):
    return f"{n:,}"

# ---------- stats card ----------
W = 500
rows = [
    ("⭐ Total stars earned", fmt(total_stars)),
    ("👥 Followers", fmt(followers)),
    ("📦 Public repositories", fmt(total_repos)),
    ("🔥 Contributions (last year)", fmt(contributions)),
    ("🤖 Agent-assisted commits", fmt(agent_commits)),
]
H = 106 + len(rows) * 46 + 14
parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub stats">',
    f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="14" fill="{BG}" stroke="{BORDER}" stroke-width="1"/>',
    f'<text x="28" y="52" font-family="{FONT}" font-size="20" font-weight="700" fill="{TITLE_C}">neohiro&#39;s GitHub Stats</text>',
    f'<line x1="24" y1="68" x2="{W-24}" y2="68" stroke="{BORDER}" />',
]
y = 106
for i, (label, value) in enumerate(rows):
    ac = ACCENTS[i % len(ACCENTS)]
    parts.append(f'<circle cx="34" cy="{y-6}" r="4" fill="{ac}"/>')
    parts.append(f'<text x="50" y="{y}" font-family="{FONT}" font-size="15" fill="{MUTED_C}">{esc(label)}</text>')
    parts.append(f'<text x="{W-28}" y="{y}" text-anchor="end" font-family="{FONT}" font-size="17" font-weight="700" fill="{TEXT_C}">{value}</text>')
    y += 46
parts.append("</svg>")
stats_svg = "\n".join(parts)

# ---------- languages card ----------
n = len(top_langs)
LH = 96 + n * 34
LW = 500
lparts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{LW}" height="{LH}" viewBox="0 0 {LW} {LH}" role="img" aria-label="Top languages">',
    f'<rect x="1" y="1" width="{LW-2}" height="{LH-2}" rx="14" fill="{BG}" stroke="{BORDER}" stroke-width="1"/>',
    f'<text x="26" y="50" font-family="{FONT}" font-size="20" font-weight="700" fill="#bb9af7">Top Languages</text>',
    f'<line x1="22" y1="66" x2="{LW-22}" y2="66" stroke="{BORDER}"/>',
]
bar_y = 92
seg_x = 22
bar_w_total = LW - 44
for name, b in top_langs:
    color = LANG_COLORS.get(name, "#8fa3b0")
    pct = b / total_lb
    lparts.append(f'<text x="26" y="{bar_y+18}" font-family="{FONT}" font-size="13.5" fill="{TEXT_C}">{esc(name)}</text>')
    lparts.append(f'<text x="{LW-26}" y="{bar_y+18}" text-anchor="end" font-family="{FONT}" font-size="13.5" fill="{MUTED_C}">{pct*100:.1f}%</text>')
    lparts.append(f'<rect x="24" y="{bar_y+26}" width="{bar_w_total}" height="7" rx="3.5" fill="#22252f"/>')
    lparts.append(f'<rect x="24" y="{bar_y+26}" width="{max(4, bar_w_total*pct)}" height="7" rx="3.5" fill="{color}"/>')
    bar_y += 34
lparts.append("</svg>")
langs_svg = "\n".join(lparts)

open("stats.svg", "w", encoding="utf-8").write(stats_svg)
open("langs.svg", "w", encoding="utf-8").write(langs_svg)
print(f"stats: stars={total_stars} followers={followers} repos={total_repos} contrib={contributions} agent_commits={agent_commits}")
print(f"languages: {[(k, round(v/total_lb*100,1)) for k,v in top_langs]}")
