---
layout: default
title: neohiro
description: "Security hardening & privacy tools for Windows and Linux. Defense is the best defense."
---

<div class="hero" id="home">
  <canvas id="matrix-canvas" aria-hidden="true"></canvas>
  <div class="container">
    <div class="hero-content">
      <img class="hero-avatar"
           src="https://github.com/neohiro.png"
           alt="neohiro avatar"
           width="92" height="92"
           fetchpriority="high">
      <div class="hero-badges" aria-label="Affiliations">
        <span class="badge badge-metapod">METAPOD</span>
        <a href="https://frenzypenguin.media/" class="badge badge-fpm" target="_blank" rel="noopener">FrenzyPenguin Media</a>
      </div>

      <h1 class="hero-title">Defense is the best defense.</h1>

      <p class="hero-tagline">
        Open-source security hardening for Windows &amp; Linux.
        Exploit mitigation that actually works. Zero telemetry. Ever.
      </p>

      <div class="hero-cta">
        <a href="#featured-tools" class="btn btn-primary">Explore Tools</a>
        <a href="{{ '/repositories/' | relative_url }}" class="btn btn-secondary">All Repositories</a>
        <a href="https://github.com/login/oauth/authorize?client_id=neohiro&scope=read%3Auser" class="btn btn-ghost btn-login" id="login-btn">
          <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18" aria-hidden="true"><path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/></svg>
          Login with GitHub
        </a>
      </div>
    </div>
  </div>
</div>

<!-- Live Signal — sits below the full-height hero, so it is only reached by scrolling.
     aria-live is deliberately OFF: this element rewrites itself ~20x/second and a
     polite live region would flood a screen reader with single-character updates. -->
<section class="section section-quotes" id="quotes" aria-label="Live signal">
  <div class="typewriter-wrap">
    <span class="typewriter-prefix" aria-hidden="true"><span class="typewriter-dot"></span>live signal</span>
    <p class="typewriter-visually-hidden">Short factual one-liners from the neohiro stack, typed out below.</p>
    <div class="typewriter" id="tw-text" aria-hidden="true"></div>
    <div class="typewriter-attribution" id="tw-attrib" aria-hidden="true"></div>
  </div>
</section>

<script>
  /* Live signal — short, factual one-liners, each tied to something that ships.
     Type → hold → erase → next, and only while the section is actually on screen. */
  (function () {
    const QUOTES = [
      { t: "One command. Full rollback.",           a: "Harden-Windows" },
      { t: "Encrypted DNS. Click to switch.",      a: "dnscrypt-proxy-gui" },
      { t: "3.2M domains blocked. 49 feeds.",      a: "Cripple-NetStrip" },
      { t: "Windows, macOS, Linux, Android.",       a: "Cripple-NetStrip" },
      { t: "ASR, CFG, DEP, SEHOP — toggled.",      a: "ExploitProtection" },
      { t: "Firewall, DNSCrypt, Tor, AppArmor.",    a: "neohiro/linux" },
      { t: "Sees every connection. Live.",          a: "Cripple-NetStrip" },
      { t: "Vanity Ed25519 keys. In-browser.",      a: "mesh-vanity-key" },
      { t: "DNS restored exactly as it was.",       a: "dnscrypt-proxy-gui" },
      { t: "110 milestones. Seven verticals.",      a: "Transhumanists (H+)" },
      { t: "Passive honeypot. Zero config.",        a: "HoneyScan" },
      { t: "Sessions heal themselves.",             a: "auto-resume" },
      { t: "Audit it, then fix it.",                a: "neohiro-doctor" },
      { t: "Hardening as a checklist.",             a: "neohiro/linux" },
      { t: "Zero telemetry. No accounts.",          a: "neohiro" },
      { t: "Windows, macOS, Linux. One app.",       a: "dnscrypt-proxy-gui" },
      { t: "Every packet, accounted for.",          a: "Cripple-NetStrip" },
      { t: "Leave a message. A human reads it.",    a: "neohiro" },
      { t: "Defense is the best defense.",          a: "neohiro" }
    ];

    const elText  = document.getElementById('tw-text');
    const elAttr  = document.getElementById('tw-attrib');
    if (!elText) return;

    // The cursor is a SIBLING of #tw-text, never a child: appending it into the
    // text node would subject it to #tw-text's own text styling.
    const cursor = document.createElement('span');
    cursor.className = 'typewriter-cursor';
    elText.parentNode.insertBefore(cursor, elText.nextSibling);

    let qi = 0, ci = 0, deleting = false;

    function tick() {
      const q = QUOTES[qi];
      if (!deleting) {
        ci++;
        elText.textContent = q.t.slice(0, ci);
        if (ci >= q.t.length) {
          elAttr.textContent = '— ' + q.a;
          deleting = true;
          return setTimeout(tick, 1400);
        }
        return setTimeout(tick, 32 + Math.random() * 34);
      }
      ci--;
      elText.textContent = q.t.slice(0, ci);
      if (ci <= 0) {
        deleting = false;
        qi = (qi + 1) % QUOTES.length;
        elAttr.textContent = '';
        return setTimeout(tick, 240);
      }
      return setTimeout(tick, 14 + Math.random() * 16);
    }

    // Don't burn cycles typing while the hero fills the viewport.
    function begin() { setTimeout(tick, 250); }
    if ('IntersectionObserver' in window) {
      const io = new IntersectionObserver(function (entries) {
        for (const entry of entries) {
          if (entry.isIntersecting) { io.disconnect(); begin(); return; }
        }
      }, { threshold: 0.35 });
      io.observe(elText.parentNode);
    } else {
      begin();
    }
  })();
</script>

<!-- Production-Grade Tools -->
<style>.tool-stars{font-size:12px;color:#ffd54f;margin-left:8px;font-weight:600}</style>
<section class="section" id="featured-tools" style="padding-bottom:24px">
  <div class="container">
    <header class="section-header">
      <h2>Featured Tools</h2>
      <p class="section-subtitle">Production-grade security tooling — battle-tested, zero telemetry, and the live research stack it all feeds</p>
    </header>

    <div class="tools-grid">
      {% assign featured = site.data.repos.repos | where_exp: "tool", "tool.featured == true" | sort: "weight" %}
      {% for tool in featured %}
        {%- comment -%} Icons live in the _tools collection front matter, not in repos.yml. {%- endcomment -%}
        {% assign tool_page = site.tools | where: "name", tool.name | first %}
        <article class="tool-card card-3d" itemscope itemtype="https://schema.org/SoftwareApplication">
          <div class="tool-icon" aria-hidden="true">
            {% if tool_page.icon %}
              {{ tool_page.icon }}
            {% elsif tool.category contains 'Network' or tool.category contains 'Security' %}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg>
            {% elsif tool.category contains 'Games' %}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="6" width="20" height="12" rx="2"/><path d="M7 12h.01M12 12h.01M17 12h.01"/></svg>
            {% elsif tool.category contains 'Developer' %}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M16 18l6-6-6-6"/><path d="M8 6l-6 6 6 6"/></svg>
            {% elsif tool.category contains 'Guides' %}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>
            {% else %}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="3"/><path d="M9 12h6M12 9v6"/></svg>
            {% endif %}
          </div>
          <h3 class="tool-name" itemprop="name">{{ tool.title | escape }}{% if tool.stars %}<span class="tool-stars">★ {{ tool.stars }}</span>{% endif %}</h3>
          <p class="tool-desc" itemprop="description">{{ tool.tagline | escape }}</p>
          <div class="tool-meta">
            <span class="tool-platform" itemprop="operatingSystem">{{ tool.platform | escape }}</span>
            {% if tool.language %}
              <span class="tool-lang">{{ tool.language | escape }}</span>
            {% endif %}
          </div>
          <div class="tool-links">
            <a href="{{ tool.repo_url | escape }}" class="tool-link" target="_blank" rel="noopener" itemprop="url">
              <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16" aria-hidden="true"><path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/></svg>
              Repository
            </a>
            {% if tool.demo_url %}
              <a href="{{ tool.demo_url | escape }}" class="tool-link tool-link-secondary" target="_blank" rel="noopener">{{ tool.demo_label | default: "Demo" | escape }}</a>
            {% endif %}
          </div>
        </article>
      {% endfor %}

      {%- comment -%} Ecosystem entries (non-neohiro) share the grid so the row stays balanced. {%- endcomment -%}
      {% for eco in site.data.ecosystem.entries %}
        <article class="tool-card tool-card--ecosystem card-3d accent-{{ eco.accent | default: 'purple' | strip | escape }}" itemscope itemtype="https://schema.org/SoftwareApplication">
          <div class="tool-icon" aria-hidden="true">{{ eco.icon }}</div>
          <h3 class="tool-name" itemprop="name">{{ eco.title | escape }}</h3>
          <p class="tool-desc" itemprop="description">{{ eco.tagline | escape }}</p>
          <div class="tool-meta">
            {% if eco.pill %}<span class="tool-pill">{{ eco.pill | escape }}</span>{% endif %}
            <span class="tool-platform" itemprop="operatingSystem">{{ eco.platform | escape }}</span>
            {% if eco.language %}<span class="tool-lang">{{ eco.language | escape }}</span>{% endif %}
          </div>
          <ul class="tool-highlights">
            {% for h in eco.highlights %}<li>{{ h }}</li>{% endfor %}
          </ul>
          <div class="tool-links">
            <a href="{{ eco.repo_url | escape }}" class="tool-link" target="_blank" rel="noopener" itemprop="url">
              <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16" aria-hidden="true"><path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/></svg>
              {{ eco.repo_label | default: "Repository" | escape }}
            </a>
            {% if eco.live_url %}
              <a href="{{ eco.live_url | escape }}" class="tool-link tool-link-live" target="_blank" rel="noopener">
                <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>
                {{ eco.live_label | default: "Live data" | escape }}
              </a>
            {% endif %}
          </div>
          {% if eco.repo_note %}<span class="tool-footnote">{{ eco.repo_note | escape }}</span>{% endif %}
        </article>
      {% endfor %}
    </div>
    <p class="tools-grid-note">
      Ecosystem cards link to projects run on the same stack. Full inventory in
      <a href="{{ '/repositories/' | relative_url }}">Repositories</a>.
    </p>
  </div>
</section>

<!-- OS App Selector — Interactive Tool Index with Vicinity Blooming -->
<section class="section" id="os-selector-section" style="padding-top:24px">
  <div class="container">
    <header class="section-header"><h2>OS App Selector</h2></header>
    <div class="os-app-selector" id="os-app-selector">
      <div class="os-grid">
        {% assign all_tools = site.data.repos.repos | sort: "weight" %}
        {% for tool in all_tools %}
          {% unless tool.name == 'ubuntu' or tool.name == 'mobile-sync' %}
          <a href="{{ tool.repo_url }}" class="os-app-tile" target="_blank" rel="noopener" aria-label="{{ tool.title }}">
            <div class="os-app-icon" aria-hidden="true">
              {% if tool.category contains 'Network' or tool.category contains 'Security' or tool.category contains 'Hardening' %}
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/><path d="M12 6v6m-3 3h6"/></svg>
              {% elsif tool.category contains 'Cryptography' %}
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="11" width="18" height="10" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/><circle cx="12" cy="16" r="1.5" fill="currentColor"/></svg>
              {% elsif tool.category contains 'Games' %}
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="6" width="20" height="12" rx="2"/><path d="M7 12h.01M12 12h.01M17 12h.01"/><path d="M6 9l2 2 4-4"/></svg>
              {% elsif tool.category contains 'Developer' or tool.category contains 'Utilities' or tool.category contains 'System Utilities' %}
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
              {% elsif tool.category contains 'Communication' or tool.category contains 'Media' %}
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/><circle cx="9" cy="12" r="1" fill="currentColor"/><circle cx="13" cy="12" r="1" fill="currentColor"/><circle cx="17" cy="12" r="1" fill="currentColor"/></svg>
              {% elsif tool.category contains 'Information' or tool.category contains 'Health' %}
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/><circle cx="12" cy="12" r="3" fill="none" stroke="currentColor"/></svg>
              {% elsif tool.category contains 'Privacy' %}
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3" fill="currentColor"/></svg>
              {% else %}
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="3"/><path d="M9 12h6M12 9v6"/></svg>
              {% endif %}
            </div>
            <span class="os-app-title">{{ tool.title }}</span>
            <span class="os-app-sub">{{ tool.language | split: ' ' | first }}</span>
          </a>
          {% endunless %}
        {% endfor %}
      </div>
    </div>
  </div>
</section>

<script>
  (function() {
    const selector = document.getElementById('os-app-selector');
    if (!selector) return;
    // Accessibility: respect reduced-motion preference
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const grid = selector.querySelector('.os-grid');
    const tiles = Array.from(grid.querySelectorAll('.os-app-tile'));

    let rafId = null;
    let mouseX = 0, mouseY = 0;

    function updateTiles() {
      const rect = selector.getBoundingClientRect();
      tiles.forEach(tile => {
        const tRect = tile.getBoundingClientRect();
        const tx = tRect.left + tRect.width / 2 - rect.left;
        const ty = tRect.top + tRect.height / 2 - rect.top;
        const dist = Math.hypot(mouseX - tx, mouseY - ty);
        const radius = 200;
        if (dist < radius) {
          const factor = 1 + (1 - dist / radius) * 0.35;
          tile.style.setProperty('--tile-scale', factor.toFixed(3));
        } else {
          tile.style.setProperty('--tile-scale', '1');
        }
      });
      rafId = requestAnimationFrame(updateTiles);
    }

    selector.addEventListener('mousemove', (e) => {
      const rect = selector.getBoundingClientRect();
      mouseX = e.clientX - rect.left;
      mouseY = e.clientY - rect.top;
      selector.style.setProperty('--mouse-x', mouseX + 'px');
      selector.style.setProperty('--mouse-y', mouseY + 'px');
      if (!rafId) rafId = requestAnimationFrame(updateTiles);
    });

    selector.addEventListener('mouseleave', () => {
      if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
      tiles.forEach(tile => tile.style.setProperty('--tile-scale', '1'));
    });

    // Ripple effect on click
    tiles.forEach(tile => {
      tile.addEventListener('pointerdown', (e) => {
        const ripple = document.createElement('span');
        ripple.className = 'os-app-ripple';
        const rect = tile.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height) * 1.5;
        ripple.style.cssText = `
          width: ${size}px; height: ${size}px;
          left: ${e.clientX - rect.left}px;
          top: ${e.clientY - rect.top}px;
        `;
        tile.appendChild(ripple);
        requestAnimationFrame(() => ripple.classList.add('active'));
        setTimeout(() => ripple.remove(), 600);
      });
    });
  })();
</script>

<!-- Hardening Guides (OS-level) -->
<section class="section section-alt" id="hardening-guides">
  <div class="container">
    <header class="section-header">
      <h2>Hardening Guides</h2>
      <p class="section-subtitle">Step-by-step post-install security for your operating system</p>
    </header>

    <div class="guides-grid">
      <article class="guide-card">
        <div class="guide-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="2" y="4" width="20" height="16" rx="2"/>
            <path d="M8 4v16M16 4v16M4 8h16"/>
          </svg>
        </div>
        <h3>Windows 10/11 STIG-Style Hardening</h3>
        <p>18 modules, 4 profiles, allow-lists, rollback, dry-run — one command.</p>
        <a href="https://github.com/neohiro/windows" class="guide-link" target="_blank" rel="noopener">
          View Guide <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </a>
      </article>

      <article class="guide-card">
        <div class="guide-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M12 2l10 7v10l-10 7-10-7v-10l10-7z"/>
            <path d="M2 12h20M12 2v20"/>
          </svg>
        </div>
        <h3>Linux Post-Install Hardening</h3>
        <p>Firewall, encrypted DNS, Tor, auditd, AppArmor — automated.</p>
        <a href="https://github.com/neohiro/linux" class="guide-link" target="_blank" rel="noopener">
          View Guide <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </a>
      </article>
    </div>
  </div>
</section>

<section class="section" id="community">
  <div class="container">
    <header class="section-header">
      <h2>Community & Support</h2>
      <p class="section-subtitle">Pick a project, then choose how to engage</p>
    </header>

    <!-- Project Selector -->
    <div class="project-selector" id="project-selector">
      <label for="project-select" class="visually-hidden">Select a project</label>
      <select id="project-select" class="project-select" aria-label="Select a project to view community links">
        <option value="" disabled selected>-- Choose a project --</option>
      </select>
    </div>

    <!-- Action Cards (shown after project selection) -->
    <div class="community-grid" id="community-actions">
      <a class="community-card card-3d" id="action-bugs" href="#" role="button" tabindex="0" aria-label="Open bug reports for selected project">
        <h3>Bug Reports</h3>
        <p>Structured issue templates with required diagnostics.</p>
        <span class="card-action">Open Issues →</span>
      </a>

      <a class="community-card card-3d" id="action-security" href="#" role="button" tabindex="0" aria-label="Report security vulnerability for selected project">
        <h3>Security Vulnerabilities</h3>
        <p>Private disclosure via Security Advisories tab.</p>
        <span class="card-action">Report Security →</span>
      </a>

      <a class="community-card card-3d" id="action-discussions" href="#" role="button" tabindex="0" aria-label="Join discussions for selected project">
        <h3>Discussions</h3>
        <p>Questions, showcases, and feature requests.</p>
        <span class="card-action">Join Discussion →</span>
      </a>

      <a class="community-card card-3d" id="action-sponsor" href="https://github.com/sponsors/neohiro" target="_blank" rel="noopener" aria-label="Sponsor neohiro on GitHub">
        <h3>Sponsor</h3>
        <p>Support ongoing development via GitHub Sponsors or Patreon.</p>
        <span class="card-action">Sponsor neohiro →</span>
      </a>
    </div>

    <a class="fpm-spotlight card-3d" href="https://frenzypenguin.media" target="_blank" rel="noopener" aria-label="FrenzyPenguin Media — music artist recordings & creative content">
      <div class="community-card-icon" aria-hidden="true" style="margin: 0 auto 14px; color: var(--purple);">
        <svg viewBox="0 0 24 24" fill="currentColor" width="36" height="36"><path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.814v-8l8 3.993-8 4.007z"/></svg>
      </div>
      <h3>🎬 FrenzyPenguin Media</h3>
      <p>Music artist recordings, creative projects, and multimedia content from the makers of neohiro.</p>
      <span class="card-action" style="color: var(--purple);">Explore frenzypenguin.media →</span>
    </a>
  </div>
</section>

<!-- Transhumanists — live research dashboard. Deliberately the last block on the
     page so the security tooling above reads as the entry point and this is the
     "and here is what it feeds" payoff. -->
<section class="section signal-promo" id="live-data" aria-labelledby="live-data-title">
  <div class="container">
    <div class="signal-card card-3d accent-purple">
      <div class="signal-card-grid">
        <div class="signal-card-copy">
          <span class="signal-card-eyebrow">🧬 Transhumanists (H+)</span>
          <h2 id="live-data-title">Human progress, on a world map.</h2>
          <p class="signal-card-lede">
            Every tool above ships telemetry-free. The one thing we do publish is
            <em>signal</em>: breakthroughs scored, categorised and pinned to the place
            they happened.
          </p>
          <ul class="signal-card-stats">
            <li><strong>7</strong><span>verticals</span></li>
            <li><strong>110+</strong><span>milestones</span></li>
            <li><strong>daily</strong><span>refresh</span></li>
          </ul>
          <ul class="signal-card-verticals">
            <li>Biotechnology</li>
            <li>Computing &amp; AGI</li>
            <li>Quantum</li>
            <li>Cybersecurity</li>
            <li>Spaceflight</li>
            <li>Renewable Energy</li>
            <li>Defense</li>
          </ul>
          <div class="signal-card-actions">
            <a href="https://transhumanists.github.io/" class="btn btn-primary" target="_blank" rel="noopener">
              <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>
              Open live data
            </a>
            <a href="https://github.com/frenzypenguin-media" class="btn btn-secondary" target="_blank" rel="noopener">
              Source on GitHub
            </a>
          </div>
        </div>

        <a class="signal-card-map" href="https://transhumanists.github.io/" target="_blank" rel="noopener"
           aria-label="Open the Transhumanists live dashboard world map">
          <span class="signal-card-map-grid" aria-hidden="true"></span>
          <span class="signal-card-map-pins" aria-hidden="true">
            <i style="--x:22%; --y:38%"></i>
            <i style="--x:41%; --y:27%"></i>
            <i style="--x:58%; --y:52%"></i>
            <i style="--x:73%; --y:34%"></i>
            <i style="--x:34%; --y:61%"></i>
            <i style="--x:66%; --y:71%"></i>
          </span>
          <span class="signal-card-map-cta">transhumanists.github.io ↗</span>
        </a>
      </div>
    </div>
  </div>
</section>

<script>
  (function() {
    'use strict';

    // NOTE: the old #consent-card onboarding flow was removed from the markup but
    // its handler stayed here. `card.classList` on the null result threw a
    // TypeError on the very first line of this IIFE, which silently killed every
    // feature below it: the project selector never populated, the scroll progress
    // bar never mounted, click ripples and card tilt never bound. Do not re-add
    // unguarded DOM lookups here — guard with `if (!el) return;`.

    document.addEventListener("click", function(e) {
      const target = e.target.closest(".btn, .legal-link, .guide-link, .card-action, .community-card, .tool-link, .fpm-spotlight");
      if (!target) return;
      const rect = target.getBoundingClientRect();
      const ripple = document.createElement("span");
      ripple.className = "click-ripple";
      const size = Math.max(rect.width, rect.height) * 1.4;
      ripple.style.width = ripple.style.height = size + "px";
      ripple.style.left = (e.clientX - rect.left - size / 2) + "px";
      ripple.style.top = (e.clientY - rect.top - size / 2) + "px";
      target.appendChild(ripple);
      setTimeout(() => ripple.remove(), 700);
    });

    const loginBtn = document.getElementById("login-btn");
    if (loginBtn) {
      loginBtn.addEventListener("click", function(e) {
        sessionStorage.setItem("neohiro.login.intent", "1");
        const rect = loginBtn.getBoundingClientRect();
        for (let i = 0; i < 12; i++) {
          const spark = document.createElement("span");
          spark.className = "login-spark";
          spark.style.left = (rect.left + rect.width / 2) + "px";
          spark.style.top = (rect.top + rect.height / 2) + "px";
          const angle = (Math.PI * 2 * i) / 12;
          const dist = 50 + Math.random() * 60;
          spark.style.setProperty("--dx", Math.cos(angle) * dist + "px");
          spark.style.setProperty("--dy", Math.sin(angle) * dist + "px");
          document.body.appendChild(spark);
          setTimeout(() => spark.remove(), 900);
        }
      });
    }

    const progress = document.createElement("div");
    progress.className = "scroll-progress";
    document.body.appendChild(progress);
    window.addEventListener("scroll", function() {
      const h = document.documentElement;
      const max = h.scrollHeight - h.clientHeight;
      const pct = max > 0 ? (h.scrollTop / max) * 100 : 0;
      progress.style.width = pct + "%";
    }, {passive: true});

    const revealTargets = document.querySelectorAll(".section, .legal-card, .tool-card, .guide-card, .community-card, .quote-card, .fpm-spotlight, .signal-card");
    revealTargets.forEach(el => el.classList.add("reveal"));
    if ("IntersectionObserver" in window) {
      const io = new IntersectionObserver(entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add("reveal-in");
            io.unobserve(entry.target);
          }
        });
      }, {threshold: 0.08, rootMargin: "0px 0px -10% 0px"});
      revealTargets.forEach(el => io.observe(el));
    } else {
      revealTargets.forEach(el => el.classList.add("reveal-in"));
    }

    document.querySelectorAll(".tool-card, .guide-card, .quote-card, .fpm-spotlight, .signal-card").forEach(card => {
      card.addEventListener("mousemove", function(e) {
        const rect = card.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width - 0.5;
        const y = (e.clientY - rect.top) / rect.height - 0.5;
        card.style.setProperty("--mx", (x * 8) + "px");
        card.style.setProperty("--my", (y * 8) + "px");
      });
      card.addEventListener("mouseleave", function() {
        card.style.setProperty("--mx", "0px");
        card.style.setProperty("--my", "0px");
      });
    });

    // Project selector & community actions
    const projectSelect = document.getElementById("project-select");
    const communityActions = document.getElementById("community-actions");
    if (projectSelect && communityActions) initProjectSelector(projectSelect, communityActions);

    function initProjectSelector(projectSelect, communityActions) {
      const actionCards = {
        bugs: document.getElementById("action-bugs"),
        security: document.getElementById("action-security"),
        discussions: document.getElementById("action-discussions")
      };
      const REPOS_JSON = "{{ '/assets/data/repos.json' | relative_url }}";

      async function loadRepos() {
        try {
          const resp = await fetch(REPOS_JSON);
          if (!resp.ok) throw new Error("HTTP " + resp.status);
          const data = await resp.json();
          const repos = data.repos || data;
          repos.forEach(repo => {
            const opt = document.createElement("option");
            const url = repo.repo_url || "https://github.com/neohiro/" + repo.name;
            opt.value = url;
            opt.textContent = repo.title || repo.name;
            opt.dataset.repoUrl = url;
            opt.dataset.name = repo.name;
            projectSelect.appendChild(opt);
          });
        } catch (e) {
          console.warn("Could not load project list:", e);
          projectSelect.innerHTML = '<option value="">Failed to load projects</option>';
        }
      }

      function updateActionLinks(repoUrl) {
        if (!repoUrl) return;
        const map = {
          bugs: repoUrl + "/issues",
          security: repoUrl + "/security/advisories/new",
          discussions: repoUrl + "/discussions"
        };
        Object.keys(map).forEach(function(k) {
          const el = actionCards[k];
          if (!el) return;
          el.href = map[k];
          const label = el.querySelector(".card-action");
          if (label) label.textContent = (k === "bugs" ? "Open Issues" : k === "security" ? "Report Security" : "Join Discussion") + " →";
        });
      }

      projectSelect.addEventListener("change", function() {
        const selected = this.options[this.selectedIndex];
        if (selected && selected.value) {
          updateActionLinks(selected.dataset.repoUrl);
        }
        communityActions.style.display = "grid";
      });

      // Keyboard support for action cards (Enter/Space to follow link)
      communityActions.querySelectorAll("a[role='button']").forEach(card => {
        card.addEventListener("keydown", function(e) {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            this.click();
          }
        });
        // Open dynamic targets in a new tab without leaking the opener
        card.addEventListener("click", function(e) {
          if (this.href && this.href !== "#") {
            e.preventDefault();
            window.open(this.href, "_blank", "noopener");
          } else {
            e.preventDefault();
            const sel = document.getElementById("project-select");
            const selWrap = document.getElementById("project-selector");
            if (sel) sel.focus();
            if (selWrap) selWrap.scrollIntoView({ behavior: "smooth", block: "center" });
          }
        });
      });

      loadRepos();
    }
  })();
</script>
