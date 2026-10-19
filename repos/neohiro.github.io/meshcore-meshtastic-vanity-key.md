---
layout: default
permalink: /meshcore-meshtastic-vanity-key/
title: Moved — meshcore-meshtastic-vanity-key
description: This tool was renamed to mesh-vanity-key and now lives at a new address.
sitemap: false
robots: noindex, follow
---

<!--
  Permanent redirect for the project's former address.

  The repository was renamed from `meshcore-meshtastic-vanity-key` to
  `mesh-vanity-key`, because it grew past the two protocols its original name
  implied: Meshtastic channel PSKs and `!node` IDs now sit alongside the
  MeshCore device keys. GitHub Pages serves a project site from the repository
  NAME. GitHub redirects the old *repository* URL on its own
  (github.com/neohiro/meshcore-meshtastic-vanity-key -> .../mesh-vanity-key),
  but it does NOT redirect the *Pages* path: renaming the repository moves the
  site, and the old path becomes a 404 on this user site with nothing behind it.

  This page exists to catch that. It keeps the old URL working for bookmarks,
  inbound links and anything already indexed, instead of leaving a dead end.

  It is the second hop for this tool. meshcore-vanity-key.md catches the name
  before it, so both former addresses land on the live page rather than on each
  other.

  Three mechanisms, in order of how quickly they fire:
    1. <meta http-equiv="refresh"> - fires with no JavaScript, which matters
       because a redirect that depends on JS is a redirect that fails.
    2. location.replace() - same timing, but replaces the history entry so the
       back button does not bounce the visitor straight back into a redirect
       loop. `location.href` would create exactly that trap.
    3. The visible link below. If both of the above are blocked - a strict
       Content-Security-Policy, an embedded viewer, a crawler - there is still a
       real, clickable link rather than a blank page.

  `noindex` keeps a redirect out of search results, since it is not content and
  duplicates the tool page it points at.
-->

<meta http-equiv="refresh" content="0; url=https://neohiro.github.io/mesh-vanity-key/">
<link rel="canonical" href="https://neohiro.github.io/mesh-vanity-key/">
<script>window.location.replace("https://neohiro.github.io/mesh-vanity-key/");</script>

<div class="container" style="padding:64px 24px;max-width:640px;margin:0 auto;text-align:center">
  <h1 style="font-size:1.5rem;margin-bottom:12px">This tool has moved</h1>
  <p style="color:var(--fg-muted,#8b949e);line-height:1.6;margin-bottom:24px">
    <strong>meshcore-meshtastic-vanity-key</strong> was renamed to
    <strong>mesh-vanity-key</strong>, since it covers more than those two
    protocols. You should be redirected automatically. If not, use the link below.
  </p>
  <p>
    <a href="https://neohiro.github.io/mesh-vanity-key/"
       style="display:inline-block;padding:12px 24px;border-radius:6px;
              background:var(--accent,#58a6ff);color:#0d1117;font-weight:600;
              text-decoration:none">
      Open mesh-vanity-key &rarr;
    </a>
  </p>
  <p style="margin-top:24px;font-size:0.8125rem;color:var(--fg-subtle,#6e7681)">
    Repository:
    <a href="https://github.com/neohiro/mesh-vanity-key">github.com/neohiro/mesh-vanity-key</a>
  </p>
</div>
