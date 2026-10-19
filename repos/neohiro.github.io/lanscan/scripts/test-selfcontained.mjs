/*
 * Tests for check-selfcontained.mjs — the privacy gate on the LANScan
 * dashboard. Run: node lanscan/scripts/test-selfcontained.mjs
 *
 * The gate is the only thing standing between a stray CDN link and a page that
 * phones a third party on every load, so it is tested rather than trusted. The
 * case that matters most is the exemption: an anchor href to a release download
 * is allowed, and the day that exemption silently widened to include subresource
 * tags the gate would stop being a gate.
 */
import { execFileSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, mkdirSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';

const HERE = fileURLToPath(new URL('.', import.meta.url));
const SCRIPT = join(HERE, 'check-selfcontained.mjs');

let pass = 0;
const failures = [];

function run(files) {
  const dir = mkdtempSync(join(tmpdir(), 'selfcontained-'));
  try {
    for (const [name, body] of Object.entries(files)) {
      const full = join(dir, name);
      mkdirSync(join(full, '..'), { recursive: true });
      writeFileSync(full, body, 'utf8');
    }
    try {
      execFileSync(process.execPath, [SCRIPT, dir], { encoding: 'utf8', stdio: 'pipe' });
      return { ok: true, out: '' };
    } catch (err) {
      return {
        ok: false,
        out: `${(err.stdout || '') + (err.stderr || '')}`,
      };
    }
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

function check(name, condition, detail = '') {
  if (condition) {
    pass++;
  } else {
    failures.push(`${name}${detail ? ` — ${detail}` : ''}`);
  }
}

/* ---------- must PASS: nothing external ---------- */

{
  const r = run({ 'index.html': '<h1>hi</h1>' });
  check('plain page passes', r.ok, r.out);
}

{
  const r = run({
    'index.html': '<a href="https://github.com/neohiro/LANScan/releases/latest/download/LANScan-Windows.zip">Windows</a>',
  });
  check('anchor href to a release download is allowed (navigation, not a request)', r.ok, r.out);
}

{
  const r = run({
    'index.html': '<a href="https://example.com/">x</a>\n<a href="https://example.org/">y</a>',
  });
  check('several external anchor hrefs are allowed', r.ok, r.out);
}

{
  const r = run({
    'index.html': '<script src="assets/js/lanscan.js"></script><link rel="stylesheet" href="assets/css/lanscan.css">',
  });
  check('relative subresources pass', r.ok, r.out);
}

{
  const r = run({
    'index.html': '<!-- https://cdn.example.com/nope.css -->\n<p>ok</p>',
  });
  check('a URL inside an HTML comment is not a reference', r.ok, r.out);
}

{
  const r = run({
    'assets.js': '// see https://cdn.example.com/nope.js\nconst a = 1;\n',
  });
  check('a URL inside a JS comment is not a reference', r.ok, r.out);
}

{
  const r = run({
    'index.html': '<a href="https://neohiro.github.io/lanscan/">site</a><a href="http://127.0.0.1:8787">local</a>',
  });
  check('the site origin and loopback are allowed', r.ok, r.out);
}

{
  const r = run({
    'index.html': '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0"/></svg>',
  });
  check('an XML namespace URI is an identifier, not a fetch', r.ok, r.out);
}

/* ---------- must FAIL: a third party the page loads ---------- */

{
  const r = run({
    'index.html': '<script src="https://cdn.jsdelivr.net/npm/x.js"></script>',
  });
  check('<script src> to a CDN fails', !r.ok && /external host/.test(r.out), r.out);
}

{
  const r = run({
    'index.html': '<img src="https://tracker.example.com/pixel.gif">',
  });
  check('<img src> to a third party fails (an analytics pixel)', !r.ok, r.out);
}

{
  const r = run({
    'index.html': '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter">',
  });
  check('<link href> to a font CDN fails', !r.ok, r.out);
}

{
  /* The exemption must not leak to a tag that is also navigation-shaped. */
  const r = run({
    'index.html': '<a href="https://example.com/"><img src="https://tracker.example.com/p.gif"></a>',
  });
  check('<img src> inside an <a href> still fails — the exemption is per-attribute', !r.ok, r.out);
}

{
  const r = run({
    'index.html': '<a href="https://example.com/" ping="https://tracker.example.com/ping">x</a>',
  });
  check('ping= on an anchor fails — it is a request dressed as navigation', !r.ok, r.out);
}

{
  const r = run({
    'index.html': '<link rel="preload" href="https://cdn.example.com/x.css" as="style">',
  });
  check('rel=preload to a CDN fails — preload fetches on load', !r.ok, r.out);
}

{
  const r = run({
    'index.html': '<script>fetch("https://api.example.com/data")</script>',
  });
  check('a fetch() in inline script fails', !r.ok, r.out);
}

{
  const r = run({
    'index.html': '<script>const u = "https://api.visitorbadge.io/x"; fetch(u);</script>',
  });
  check('an analytics endpoint in a script literal fails', !r.ok, r.out);
}

{
  const r = run({
    'assets.css': '@import url("https://fonts.googleapis.com/css?family=Inter");',
  });
  check('@import fails', !r.ok, r.out);
}

{
  const r = run({
    'index.html': '<script src="data:text/javascript,void 0"></script>',
  });
  check('a data: URI is not a third-party fetch', r.ok, r.out);
}

/* ---------- report shape ---------- */

{
  const r = run({
    'index.html': '<script src="https://cdn.example.com/a.js"></script><img src="https://cdn.example.com/b.gif">',
  });
  check('reports both offenders, not just the first', !r.ok && (r.out.match(/external host/g) || []).length === 2, r.out);
}

{
  const r = run({
    'index.html': '<script src="https://cdn.example.com/a.js"></script>',
  });
  check('the report names file and line', !r.ok && /index\.html:1/.test(r.out), r.out);
}

/* ---------- the real shipped dashboard ---------- */

{
  const repoRoot = join(HERE, '..', '..');
  try {
    execFileSync(process.execPath, [SCRIPT, join(repoRoot, 'lanscan')], { encoding: 'utf8', stdio: 'pipe' });
    check('the shipped dashboard is self-contained', true);
  } catch (err) {
    check('the shipped dashboard is self-contained', false, `${err.stdout || ''}${err.stderr || ''}`);
  }
}

/* -------------------------------------------------------------------------- */

console.log(`${pass} pass, ${failures.length} fail`);
for (const f of failures) console.log(`  (fail) ${f}`);
process.exit(failures.length ? 1 : 0);