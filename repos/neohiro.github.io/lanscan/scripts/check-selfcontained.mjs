#!/usr/bin/env node
/* Assert the shipped dashboard is genuinely self-contained.
 *
 * Privacy is the whole product here: the page must render with the network
 * switched off, so it may not reference a third party. This runs in CI so a
 * stray CDN link or analytics tag fails the build instead of quietly shipping.
 *
 * Allowed: 127.0.0.1 / localhost / ::1 (the user's own service), the canonical
 *          neohiro.github.io origin, and XML/SVG namespace URIs, which are
 *          identifiers rather than fetches.
 * Rejected: everything else in a shipped file, plus @import and known CDN and
 *          analytics host fragments.
 *
 * NAVIGATION IS NOT A REQUEST. An <a href="https://github.com/..."> download
 * button fetches nothing until the visitor clicks it, and only in a new
 * context if we say target=_blank. A <script src>, <link href>, <img src>,
 * @import or fetch() is a request the page makes on load, to a third party,
 * without anyone asking -- that is what leaks. So an anchor href to an external
 * host is allowed and everything else is not.
 *
 * That distinction is not a loophole, it is the whole point: the page stays
 * silent on the network, and the one place a visitor is shown a third-party
 * URL is a link they chose to follow. Flagging that would mean removing the
 * download links, which is worse for the user than permitting them.
 *
 * Comments and string literals that merely *mention* a URL must not trip it, so
 * comments are stripped before scanning.
 */
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative, extname } from 'node:path';

const ROOT = process.argv[2] || process.cwd();
const SHIPPED = new Set(['.html', '.css', '.js', '.svg', '.json', '.webmanifest']);
const SKIP_DIRS = new Set(['.git', 'node_modules', '.github', 'schema', 'samples']);

const ALLOWED_HOSTS = [
  '127.0.0.1', 'localhost', '::1', '[::1]',
  'neohiro.github.io', 'www.w3.org', 'json-schema.org'
];

/* An anchor the visitor has to click, rather than a resource the page loads.
   Only the href is exempt -- a `src` on the same <a> would still be a fetch,
   and `ping`/`prefetch`/`preload` are requests dressed as navigation, so those
   attribute names are checked like any other subresource reference. */
const NAV_ATTRS = new Set(['href']);
const SUBRESOURCE_ATTRS = new Set([
  'src', 'data', 'action', 'formaction', 'poster', 'manifest',
  'ping', 'prefetch', 'preload', 'srcset', 'imagesrcset',
]);
const BANNED = [
  '@import', 'fonts.googleapis.com', 'fonts.gstatic.com', 'cdn.jsdelivr.net',
  'unpkg.com', 'cdnjs.cloudflare.com', 'ajax.googleapis.com', 'use.typekit.net',
  'google-analytics.com', 'googletagmanager.com', 'gtag(', 'dataLayer.push',
  'plausible.io', 'hotjar', 'segment.com', 'sentry.io'
];

const problems = [];

function stripComments(src, ext) {
  let s = src.replace(/<!--[\s\S]*?-->/g, ' ');           // HTML comments
  if (ext === '.html') return s;
  // block + line comments, guarding against "://" inside them
  s = s.replace(/\/\*[\s\S]*?\*\//g, ' ');
  s = s.replace(/(^|[^:\\])\/\/[^\n]*/g, '$1 ');
  return s;
}

function checkUrl(raw, file, line) {
  /* A relative reference is same-origin by definition: the browser resolves it
     against the page's own origin. `new URL('assets/js/lanscan.js')` throws
     because it has no base, which used to be reported as a malformed URL. That
     was only ever reachable for absolute references, since the old bare-URL
     pattern required "//" -- so relative paths never went through here at all
     and there was nothing to get wrong. Now that attribute values are checked
     directly they do, and a relative path is exactly what they are. */
  if (!/^([a-z][a-z0-9+.-]*:)?\/\//i.test(raw)) {
    if (raw.startsWith('/') || raw.startsWith('./') || raw.startsWith('../') ||
        !/^[a-z][a-z0-9+.-]*:/i.test(raw)) {
      return;  // relative or protocol-relative-but-local
    }
    /* An explicit non-http scheme (data:, mailto:, javascript:) is not a
       network fetch to a third party. */
    if (!/^https?:/i.test(raw)) return;
  }
  let host;
  try {
    host = new URL(raw.startsWith('//') ? 'https:' + raw : raw).hostname.toLowerCase();
  } catch {
    problems.push(`${file}:${line}  malformed URL  ${raw}`);
    return;
  }
  if (!ALLOWED_HOSTS.includes(host)) {
    problems.push(`${file}:${line}  external host "${host}"  ${raw}`);
  }
}

function walk(dir) {
  for (const name of readdirSync(dir)) {
    if (SKIP_DIRS.has(name)) continue;
    const full = join(dir, name);
    if (statSync(full).isDirectory()) { walk(full); continue; }
    if (!SHIPPED.has(extname(name))) continue;

    const rel = relative(ROOT, full).replace(/\\/g, '/');
    const src = stripComments(readFileSync(full, 'utf8'), extname(name));
    const lines = src.split('\n');

    lines.forEach((line, i) => {
      const low = line.toLowerCase();

      for (const frag of BANNED) {
        if (low.includes(frag.toLowerCase())) {
          problems.push(`${rel}:${i + 1}  banned reference "${frag}"  ${line.trim()}`);
        }
      }

      /* Attribute-aware, so an anchor href to a release download is allowed
         while <script src> to the same host is not. A bare URL scan cannot tell
         those apart, and defaulting either way would be wrong on one of them.

         Each whole tag is consumed and replaced with spaces, so the bare-URL
         pass below never re-reports a URL this pass already judged -- and so a
         navigation link cannot smuggle a subresource past the exemption. */
      let rest = line;
      for (const tag of line.matchAll(/<([a-zA-Z][\w-]*)((?:"[^"]*"|'[^']*'|[^>"'])*)>/g)) {
        const [, tagName, attrBlob] = tag;
        const isAnchor = tagName.toLowerCase() === 'a';
        for (const a of attrBlob.matchAll(
          /\b(src|href|data|action|formaction|poster|manifest|ping|prefetch|preload|srcset|imagesrcset)\s*=\s*["']([^"']*)["']/gi
        )) {
          const [, attr, value] = a;
          const name = attr.toLowerCase();
          if (isAnchor && NAV_ATTRS.has(name)) continue;
          /* href on a NON-anchor tag is a fetch, not a navigation: <link> covers
             stylesheet, preload, prefetch, icon and manifest alike. Leaving
             href out of SUBRESOURCE_ATTRS because <a> also uses it would exempt
             every one of those, and the exemption would be invisible until a
             <link href> to a CDN shipped. */
          if (SUBRESOURCE_ATTRS.has(name) || (!isAnchor && name === 'href')) {
            checkUrl(value.startsWith('//') ? 'https:' + value : value, rel, i + 1);
          }
        }
        rest = rest.replace(tag[0], ' '.repeat(tag[0].length));
      }

      for (const m of rest.matchAll(/\b(?:https?:)?\/\/([^\s'"()<>\\]+)/g)) {
        const url = m[0];
        /* namespace URIs are identifiers, never fetched */
        if (/w3\.org/.test(url)) continue;
        checkUrl(url.startsWith('//') ? 'https:' + url : url, rel, i + 1);
      }
    });
  }
}

walk(ROOT);

if (problems.length) {
  console.error('self-containment check FAILED\n');
  for (const p of problems) console.error('  ' + p);
  console.error(`\n${problems.length} problem(s). The dashboard must not talk to anyone but 127.0.0.1.`);
  process.exit(1);
}
console.log('self-containment check passed — no third-party references in shipped files');
