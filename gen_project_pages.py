#!/usr/bin/env python3
"""Generate the self-contained project/guide subpages served on
neohiro.github.io (one page per card in pages-site/index.html).

Each subpage follows the same security/perf rules the test gates enforce on
the index pages: no external scripts, no inline event handlers, keyframes
limited to transform/opacity (+ whitelisted brand props), no backdrop-filter,
will-change <= 4, no preconnect to api.github.com (privacy: only fetched
on user interaction, never pre-connected), no plaintext http:// except
W3C NS URIs.

Run from the workspace root:  python gen_project_pages.py
"""
import html
import os

# Anchor output next to this script so cwd-independent runs work
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "pages-site")
os.makedirs(OUT_DIR, exist_ok=True)

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>\U0001F47D</text></svg>">
<title>@@TITLE@@ — neohiro</title>
<meta name="description" content="@@DESC@@">
<style>
:root{
  --bg:#04060a; --card:rgba(16,22,29,.85);
  --cyan:#00e5ff; --violet:#7c4dff; --green:#66bb6a;
  --text:#e8eef2; --muted:#8fa3b0; --line:rgba(0,229,255,.14);
}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--text);
  font-family:'Segoe UI',system-ui,-apple-system,sans-serif;
  overflow-x:hidden;min-height:100vh;display:flex;flex-direction:column}
.aurora{position:fixed;inset:-20%;z-index:-2;filter:blur(64px);opacity:.55;will-change:transform;
  background:
    radial-gradient(38vw 38vw at 18% 24%, rgba(124,77,255,.35), transparent 60%),
    radial-gradient(32vw 32vw at 82% 18%, rgba(0,229,255,.28), transparent 60%),
    radial-gradient(40vw 40vw at 70% 85%, rgba(102,187,106,.20), transparent 62%);
  animation:drift 26s ease-in-out infinite alternate}
@keyframes drift{50%{transform:translate3d(-4%,3%,0) scale(1.08)}100%{transform:translate3d(3%,-3%,0) scale(.96)}}
.grid{position:fixed;inset:0;z-index:-1;pointer-events:none;overflow:hidden;
  mask-image:radial-gradient(ellipse at 50% 30%,#000 30%,transparent 75%);
  -webkit-mask-image:radial-gradient(ellipse at 50% 30%,#000 30%,transparent 75%)}
.grid::before{content:"";position:absolute;inset:-112px;will-change:transform;
  background-image:linear-gradient(var(--line) 1px,transparent 1px),
                   linear-gradient(90deg,var(--line) 1px,transparent 1px);
  background-size:56px 56px;
  animation:gridpan 40s linear infinite}
@keyframes gridpan{to{transform:translate3d(56px,112px,0)}}
.wrap{width:100%;max-width:860px;margin:0 auto;padding:0 24px}
.crumbs{padding-top:34px;font-size:13.5px}
.crumbs a{color:var(--muted);text-decoration:none;border:1px solid var(--line);
  padding:7px 14px;border-radius:999px;transition:.25s}
.crumbs a:hover{color:var(--cyan);border-color:var(--cyan)}
.head{text-align:center;padding:44px 0 10px}
.kicker{display:inline-block;font-size:12px;letter-spacing:.35em;color:var(--cyan);
  border:1px solid var(--line);padding:7px 16px;border-radius:999px;margin-bottom:22px;
  animation:pulse 4s ease-in-out infinite}
@keyframes pulse{50%{box-shadow:0 0 22px rgba(0,229,255,.25)}}
h1{font-size:clamp(34px,6vw,58px);font-weight:800;letter-spacing:-.02em;line-height:1.08}
.desc{margin-top:16px;color:var(--muted);font-size:clamp(15.5px,2.4vw,19px);line-height:1.65;max-width:640px;margin-left:auto;margin-right:auto}
.tags{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-top:20px}
.tag{font-size:11px;padding:4px 11px;border-radius:999px;border:1px solid rgba(255,255,255,.12);color:var(--muted)}
.panel{margin:38px 0 26px;border-radius:18px;padding:30px 30px 26px;background:var(--card);
  border:1px solid rgba(255,255,255,.06);
  opacity:0;transform:translateY(26px);transition:opacity .55s ease,transform .55s cubic-bezier(.2,.8,.2,1)}
.panel.in{opacity:1;transform:none}
.panel h2{font-size:13px;letter-spacing:.35em;text-transform:uppercase;color:var(--cyan);
  margin-bottom:18px;display:flex;align-items:center;gap:16px}
.panel h2::after{content:"";flex:1;height:1px;background:linear-gradient(90deg,var(--line),transparent)}
.panel ul{list-style:none}
.panel li{color:var(--muted);font-size:15px;line-height:1.7;padding:7px 0 7px 26px;position:relative}
.panel li::before{content:"";position:absolute;left:4px;top:16px;width:8px;height:8px;border-radius:50%;
  background:linear-gradient(135deg,var(--cyan),var(--violet))}
.meta{margin-top:16px;font-size:13px;color:var(--muted)}
.stars{color:#ffd54f;font-weight:600}
.btnrow{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;margin-top:26px}
.btn{display:inline-flex;align-items:center;gap:10px;padding:14px 28px;border-radius:999px;
  font-weight:700;font-size:15px;text-decoration:none;letter-spacing:.02em;
  transition:transform .25s,box-shadow .25s,border-color .25s}
.btn:hover{transform:translateY(-3px)}
.btn.gh{background:linear-gradient(135deg,var(--cyan),#0092b8);color:#03131a;
  box-shadow:0 8px 28px rgba(0,229,255,.30)}
.btn.ghost{border:1px solid var(--line);color:var(--muted)}
.btn.ghost:hover{border-color:var(--violet);color:var(--text)}
footer{margin-top:auto;padding:40px 0 52px;text-align:center;color:var(--muted);font-size:13.5px}
footer .heart{color:#ea4aaa}
footer a{color:var(--cyan);text-decoration:none}
@media(max-width:640px){.panel{padding:24px 20px}.btnrow .btn{width:100%;justify-content:center}}
@media(prefers-reduced-motion:reduce){
  .aurora,.grid::before,.kicker{animation:none}
  .panel{opacity:1;transform:none;transition:none}}
</style>
</head>
<body>
<div class="aurora"></div><div class="grid"></div>

<main class="wrap">
  <nav class="crumbs"><a href="./">&#8592; neohiro home</a></nav>

  <header class="head">
    <span class="kicker">@@KICKER@@</span>
    <h1>@@H1@@</h1>
    <p class="desc">@@DESC@@</p>
    <div class="tags">@@TAGS@@</div>
  </header>

  <section class="panel">
    <h2>Highlights</h2>
    <ul>
@@ITEMS@@
    </ul>
    @@META@@
    <div class="btnrow">
      <a class="btn gh" href="https://github.com/neohiro/@@REPO@@" data-repo="@@REPO@@">View on GitHub &#8599;</a>
      <a class="btn ghost" href="./">Back to all projects</a>
    </div>
  </section>
</main>

<footer class="wrap">
  <p>Part of <a href="./">neohiro.github.io</a> · Made with <span class="heart">&hearts;</span> by <a href="https://github.com/neohiro">neohiro</a></p>
</footer>

<script>
/* reveal + live star count (self-contained per-page core) */
const TTL = 15 * 60 * 1000;
function cachedJson(key, url) {
  try {
    const c = JSON.parse(sessionStorage.getItem('gh:' + key) || 'null');
    if (c && Date.now() - c.t < TTL) return Promise.resolve(c.d);
  } catch (e) {}
  return fetch(url).then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then(d => { try { sessionStorage.setItem('gh:' + key, JSON.stringify({ t: Date.now(), d: d })); } catch (e) {} return d; });
}
const obs = new IntersectionObserver(es => es.forEach(e => {
  if (e.isIntersecting) { e.target.classList.add('in'); obs.unobserve(e.target); }
}), { threshold: .12 });
document.querySelectorAll('.panel').forEach(p => obs.observe(p));
const starEl = document.querySelector('.stars[data-repo]');
if (starEl) {
  cachedJson('neo-repos', 'https://api.github.com/users/neohiro/repos?per_page=100')
    .then(repos => {
      const hit = repos.find(r => r.name.toLowerCase() === starEl.dataset.repo.toLowerCase());
      if (hit && typeof hit.stargazers_count === 'number') starEl.textContent = '\u2605 ' + hit.stargazers_count;
    }).catch(() => {});
}
</script>
</body>
</html>
"""

PAGES = [
    dict(file="ExploitProtection.html", repo="ExploitProtection", kicker="FEATURED TOOL",
         title="ExploitProtection", h1="ExploitProtection", stars=85,
         desc="Windows Exploit Protection settings (Ultimate) GUI — a community-maintained "
              "mitigation catalog plus a fast manager for bulk hardening.",
         tags=["Python", "Windows", "Hardening"],
         items=["Community-maintained catalog of Exploit Protection mitigations (Ultimate preset)",
                "Point-and-click GUI instead of registry spelunking",
                "Bulk-apply proven mitigations across one machine or a fleet"]),
    dict(file="Cripple-NetStrip.html", repo="Cripple-NetStrip", kicker="FEATURED TOOL",
         title="Cripple-NetStrip", h1="Cripple-NetStrip", stars=3,
         desc="Next-gen network hardening suite: DNS sinkhole, firewall, domain filter and "
              "debloater across Windows, Linux, macOS and Android.",
         tags=["Network", "DNS", "Firewall"],
         items=["DNS sinkhole with domain filtering",
                "Firewall rules and debloating in one suite",
                "Cross-platform: Windows, Linux, macOS and Android"]),
    dict(file="dnscrypt-proxy-gui.html", repo="dnscrypt-proxy-gui", kicker="FEATURED TOOL",
         title="dnscrypt-proxy GUI", h1="dnscrypt-proxy GUI", stars=27,
         desc="Cross-platform graphical front-end for dnscrypt-proxy — encrypted DNS made "
              "point-and-click.",
         tags=["DNS", "Privacy", "GUI"],
         items=["Manages dnscrypt-proxy without touching config files",
                "Encrypted DNS with server picking made simple",
                "Cross-platform by design"]),
    dict(file="BlackGlass.html", repo="BlackGlass", kicker="FEATURED TOOL",
         title="BlackGlass", h1="BlackGlass", stars=9,
         desc="Multi-client Second Life chat viewer with live minimap radar, in-session "
              "teleporting and a per-user Lists tab.",
         tags=["Second Life", "Protocol", "Tkinter"],
         items=["Multiple chat clients in one glass interface",
                "Live minimap radar of nearby residents",
                "In-session teleporting and a per-user Lists tab"]),
    dict(file="HoneyScan.html", repo="HoneyScan", kicker="FEATURED TOOL",
         title="HoneyScan", h1="HoneyScan", stars=2,
         desc="Passive honeypot for home networks — watch port scanners and snoopers in real "
              "time, beginner-friendly.",
         tags=["Honeypot", "IDS", "Learning"],
         items=["Passive monitoring — no packets sent, nothing to trip over",
                "Real-time view of port scanners and snoopers",
                "Built to be a friendly first step into network defense"]),
    dict(file="SystemMonitor.html", repo="SystemMonitor", kicker="FEATURED TOOL",
         title="SystemMonitor", h1="SystemMonitor", stars=0,
         desc="Futuristic desktop-widget system health monitor: rounded glass tiles, deep "
              "sensor chain, true manufacturer metrics.",
         tags=["psutil", "Widget", "Sensors"],
         items=["Rounded glass tiles for CPU, memory, disks and more",
                "Deep sensor chain, not just the basics",
                "True manufacturer metrics where the hardware exposes them"]),
    dict(file="windows.html", repo="windows", kicker="HARDENING GUIDE",
         title="Windows hardening guide", h1="\U0001FA9F windows", stars=None,
         desc="STIG-style manual + automated Windows 10/11 new-install hardening checklist.",
         tags=["Windows", "Hardening", "Guide"],
         items=["Manual checklist walking through every setting that matters",
                "Automation scripts for repeatable new-install hardening",
                "Aimed at Windows 10 and 11 fresh installs"]),
    dict(file="ubuntu.html", repo="ubuntu", kicker="HARDENING GUIDE",
         title="Ubuntu hardening guide", h1="\U0001F427 ubuntu", stars=None,
         desc="Post-install Linux hardening: firewall, encrypted DNS, Tor routing, fail2ban.",
         tags=["Linux", "Ubuntu", "Guide"],
         items=["Firewall baseline first, then layered services",
                "Encrypted DNS with optional Tor routing",
                "fail2ban to shut down brute-force noise"]),
]

def render(p):
    # All dynamic strings are HTML-escaped before interpolation. The PAGES list
    # currently only contains ASCII values that don't need escaping, but this
    # keeps the template safe if those entries ever include <, >, &, or quotes.
    e = html.escape
    tags = "".join(f'<span class="tag">{e(t)}</span>' for t in p["tags"])
    items = "\n".join(f"      <li>{e(it)}</li>" for it in p["items"])
    repo = e(p["repo"], quote=True)  # also escape quotes for attribute values
    meta = (f'<p class="meta">Currently <span class="stars" data-repo="{repo}">'
            f'\u2605 {p["stars"]}</span> on GitHub (updates live).</p>'
            if p["stars"] is not None else "")
    out = (TEMPLATE
           .replace("@@TITLE@@", e(p["title"]))
           .replace("@@KICKER@@", e(p["kicker"]))
           .replace("@@H1@@", e(p["h1"]))
           .replace("@@DESC@@", e(p["desc"]))
           .replace("@@TAGS@@", tags)
           .replace("@@ITEMS@@", items)
           .replace("@@META@@", meta)
           .replace("@@REPO@@", repo))
    return out

for p in PAGES:
    path = os.path.join(OUT_DIR, p["file"])
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(render(p))
    print("wrote", path)
