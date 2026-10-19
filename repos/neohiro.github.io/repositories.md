---
layout: default
title: All Repositories
description: "Complete index of neohiro public repositories — security tools, privacy utilities, games, and developer tools"
permalink: /repositories/
---

<div class="repos-page" id="repositories">
  <div class="container">
    <nav class="repos-breadcrumb" aria-label="Breadcrumb">
      <a href="{{ '/' | relative_url }}">neohiro</a>
      <span aria-hidden="true">/</span>
      <span aria-current="page">All Repositories</span>
    </nav>

    <header class="repos-header">
      <h1>All Repositories</h1>
      <p class="repos-subtitle">{{ site.data.repos.repos | size }} public projects — security, privacy, games, and developer tools</p>
    </header>

    <div class="repos-toolbar">
      <div class="repos-filters" role="group" aria-label="Filter repositories">
        <button class="filter-btn active" data-filter="all">All</button>
        <button class="filter-btn" data-filter="security">Security & Privacy</button>
        <button class="filter-btn" data-filter="network">Network Tools</button>
        <button class="filter-btn" data-filter="developer">Developer Tools</button>
        <button class="filter-btn" data-filter="games">Games</button>
        <button class="filter-btn" data-filter="utilities">Utilities</button>
        <button class="filter-btn" data-filter="guides">Guides</button>
        <button class="filter-btn" data-filter="pages">GitHub Pages</button>
        <button class="filter-btn" data-filter="deprecated" id="filter-deprecated-btn">Deprecated</button>
      </div>

      <div class="repos-controls">
        <select class="repo-sort" id="repo-sort" aria-label="Sort repositories">
          <option value="default">Default order</option>
          <option value="stars-desc">Most stars ↓</option>
          <option value="stars-asc">Fewest stars ↑</option>
          <option value="forks-desc">Most forks ↓</option>
          <option value="forks-asc">Fewest forks ↑</option>
          <option value="issues-desc">Most open issues ↓</option>
          <option value="updated-desc">Recently updated</option>
          <option value="updated-asc">Least recently updated</option>
          <option value="created-desc">Recently created</option>
          <option value="created-asc">Oldest created</option>
          <option value="name-asc">Name A → Z</option>
          <option value="name-desc">Name Z → A</option>
          <option value="year-2026">Created 2026</option>
          <option value="year-2025">Created 2025</option>
          <option value="year-2024">Created 2024 or earlier</option>
        </select>

        <input type="search" class="repo-search" id="repo-search" placeholder="Search repositories..." aria-label="Search repositories">
      </div>
    </div>

    <div class="repos-stats" aria-live="polite">
      <span class="stat"><strong id="count-all">{{ site.data.repos.repos | size }}</strong> repositories</span>
      <span class="stat"><strong id="count-featured">{{ site.data.repos.repos | where: "featured", true | size }}</strong> featured</span>
      <span class="stat"><strong id="count-deprecated">{{ site.data.repos.repos | where: "deprecated", true | size }}</strong> deprecated</span>
      <span class="stat"><strong id="count-stars">—</strong> total stars</span>
    </div>

    <div class="repos-grid" id="repos-grid">
      {% assign sorted_tools = site.data.repos.repos | sort: "weight" %}
      {% for tool in sorted_tools %}
        {% assign categories = tool.category | split: ", " %}
        {% assign is_deprecated = tool.deprecated | default: false %}
        <article class="repo-card visible"
                 data-category="{{ categories | join: ' ' }}"
                 data-name="{{ tool.title | downcase }}"
                 data-language="{{ tool.language | downcase }}"
                 data-repo="{{ tool.repo_url | split: '/' | last }}"
                 data-stars="{{ tool.stars | default: 0 }}"
                 data-forks="{{ tool.forks | default: 0 }}"
                 data-issues="{{ tool.open_issues | default: 0 }}"
                 data-pushed="{{ tool.pushed_at }}"
                 data-created="{{ tool.created_at }}"
                 data-deprecated="{{ is_deprecated }}"
                 itemscope itemtype="https://schema.org/SoftwareApplication">
          {% if is_deprecated %}
            <div class="repo-card-deprecated-badge" title="Deprecated — moved to {{ tool.successor_repo }}">
              <svg viewBox="0 0 16 16" width="12" height="12" fill="currentColor" aria-hidden="true"><path d="M8 0a8 8 0 100 16A8 8 0 008 0zm.75 4.75a.75.75 0 00-1.5 0v3.5a.75.75 0 00.37.65l2.5 1.5a.75.75 0 10.76-1.3L8.75 7.84V4.75z"/></svg>
              DEPRECATED
            </div>
          {% endif %}
          <div class="repo-card-icon" aria-hidden="true">
            {% if tool.category contains 'Security' or tool.category contains 'Network' %}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg>
            {% elsif tool.category contains 'Games' %}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="6" width="20" height="12" rx="2"/><path d="M12 12h.01"/><path d="M17 12h.01"/><path d="M7 12h.01"/></svg>
            {% elsif tool.category contains 'Developer' %}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M16 18l6-6-6-6"/><path d="M8 6l-6 6 6 6"/></svg>
            {% elsif tool.category contains 'Network' %}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="2" width="6" height="6" rx="1"/><rect x="16" y="2" width="6" height="6" rx="1"/><rect x="9" y="16" width="6" height="6" rx="1"/><path d="M5 8v4h14V8"/><path d="M12 14v4"/></svg>
            {% elsif tool.category contains 'Guides' %}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>
            {% elsif tool.category contains 'Pages' %}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/></svg>
            {% else %}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="3"/><path d="M9 12h6M12 9v6"/></svg>
            {% endif %}
          </div>
          <h3 class="repo-card-name" itemprop="name">
            <a href="{{ tool.repo_url }}" target="_blank" rel="noopener">{{ tool.title }}</a>
            {% if tool.featured %}
              <span class="featured-badge" title="Featured">★</span>
            {% endif %}
          </h3>
          <p class="repo-card-desc" itemprop="description">{{ tool.tagline }}</p>
          {% if is_deprecated and tool.successor_repo %}
            <p class="repo-card-successor">
              <strong>Successor:</strong>
              <a href="{{ tool.successor_repo }}" target="_blank" rel="noopener">{{ tool.successor_repo | split: '/' | last }}</a>
            </p>
          {% endif %}
          <div class="repo-card-meta">
            <span class="repo-platform" itemprop="operatingSystem">{{ tool.platform }}</span>
            {% if tool.language %}
              <span class="repo-lang">{{ tool.language }}</span>
            {% endif %}
            {% if tool.category %}
              <span class="repo-category">{{ tool.category }}</span>
            {% endif %}
          </div>
          {% if tool.stars %}
          <div class="repo-card-stats">
            <span class="stat-item" title="Stars"><svg viewBox="0 0 16 16" width="12" height="12" fill="currentColor" aria-hidden="true"><path d="M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z"/></svg> {{ tool.stars }}</span>
            <span class="stat-item" title="Forks"><svg viewBox="0 0 16 16" width="12" height="12" fill="currentColor" aria-hidden="true"><path d="M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75v-.878a2.25 2.25 0 111.5 0v.878a2.25 2.25 0 01-2.25 2.25h-1.5v2.128a2.251 2.251 0 11-1.5 0V8.5h-1.5A2.25 2.25 0 013.5 6.25v-.878a2.25 2.25 0 111.5 0zM5 3.25a.75.75 0 10-1.5 0 .75.75 0 001.5 0zm6.75.75a.75.75 0 100-1.5.75.75 0 000 1.5zm-3 8.75a.75.75 0 10-1.5 0 .75.75 0 001.5 0z"/></svg> {{ tool.forks }}</span>
            {% if tool.open_issues > 0 %}
            <span class="stat-item" title="Open Issues"><svg viewBox="0 0 16 16" width="12" height="12" fill="currentColor" aria-hidden="true"><path d="M8 9.5a1.5 1.5 0 100-3 1.5 1.5 0 000 3z"/><path d="M8 0a8 8 0 100 16A8 8 0 008 0zM1.5 8a6.5 6.5 0 1113 0 6.5 6.5 0 01-13 0z"/></svg> {{ tool.open_issues }}</span>
            {% endif %}
          </div>
          {% endif %}
          <div class="repo-card-links">
            <a href="{{ tool.repo_url }}" class="repo-link" itemprop="url">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              Details
            </a>
            <a href="{{ tool.repo_url }}" class="repo-link repo-link-external" target="_blank" rel="noopener">
              <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14"><path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/></svg>
              GitHub
            </a>
          </div>
          <div class="repo-card-actions">
            <a href="{{ tool.repo_url }}/issues" class="repo-action-btn repo-action-bug" target="_blank" rel="noopener" title="Bug Reports">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><path d="M12 2a10 10 0 0 1 10 10c0 5.52-4.48 10-10 10S2 17.52 2 12h2a8 8 0 1 0 16 0H2c0-4.41 3.59-8 8-8z"/></svg>
              Bug
            </a>
            <a href="{{ tool.repo_url }}/security" class="repo-action-btn repo-action-sec" target="_blank" rel="noopener" title="Security / Vulnerabilities">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><path d="M12 2L3 7v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z"/></svg>
              Sec
            </a>
            <a href="{{ tool.repo_url }}/discussions" class="repo-action-btn repo-action-disc" target="_blank" rel="noopener" title="Discussions">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              Discuss
            </a>
          </div>
        </article>
      {% endfor %}
    </div>

    <div class="repos-footer">
      <p>Part of <a href="https://github.com/neohiro" target="_blank" rel="noopener">neohiro</a> — {{ site.description }}</p>
      <p><a href="{{ '/' | relative_url }}">← Back to Home</a></p>
    </div>
  </div>
</div>

 <script>
(function() {
  'use strict';
  document.addEventListener('DOMContentLoaded', function() {
    var grid = document.getElementById('repos-grid');
    if (!grid) return;
    var cards = Array.from(grid.querySelectorAll('.repo-card'));
    var filterBtns = document.querySelectorAll('.filter-btn');
    var searchInput = document.getElementById('repo-search');
    var sortSelect = document.getElementById('repo-sort');
    var countAll = document.getElementById('count-all');
    var countFeatured = document.getElementById('count-featured');
    var countDeprecated = document.getElementById('count-deprecated');
    var countStars = document.getElementById('count-stars');

    // ── Make all cards visible immediately ──────────────────────────────────
    cards.forEach(function(c) { c.classList.add('visible'); });

    // ── Stats ────────────────────────────────────────────────────────────────
    if (countAll) countAll.textContent = cards.length;
    if (countFeatured) {
      countFeatured.textContent = grid.querySelectorAll('.featured-badge').length;
    }
    if (countDeprecated) {
      countDeprecated.textContent = cards.filter(function(c) {
        return c.dataset.deprecated === 'True' || c.dataset.deprecated === 'true';
      }).length;
    }
    if (countStars) {
      var totalStars = cards.reduce(function(s, c) {
        return s + (parseInt(c.dataset.stars || '0', 10) || 0);
      }, 0);
      countStars.textContent = totalStars;
    }

    // ── State ────────────────────────────────────────────────────────────
    var activeFilter = 'all';
    var activeQuery = '';
    var activeSort = 'default';

    function applyFilters() {
      cards.forEach(function(card) {
        var cats = (card.dataset.category || '').toLowerCase();
        var name = (card.dataset.name || '').toLowerCase();
        var desc = (card.querySelector('.repo-card-desc') || {}).textContent || '';
        var lang = (card.dataset.language || '').toLowerCase();
        var repo = (card.dataset.repo || '').toLowerCase();
        var isDeprecated = card.dataset.deprecated === 'True' || card.dataset.deprecated === 'true';
        desc = desc.toLowerCase();
        var q = activeQuery.toLowerCase().trim();

        var show = true;
        if (activeFilter !== 'all') {
          if (activeFilter === 'deprecated') {
            show = isDeprecated;
          } else {
            show = cats.includes(activeFilter);
          }
        }
        if (show && q) {
          show = name.includes(q) || desc.includes(q) || lang.includes(q) || cats.includes(q) || repo.includes(q);
        }
        card.style.display = show ? '' : 'none';
        if (show) {
          card.style.animation = '';
          void card.offsetWidth;
          card.style.animation = 'fadeInUp 0.35s ease forwards';
        }
      });

      // Update count
      var visibleCount = cards.filter(function(c) { return c.style.display !== 'none'; }).length;
      if (countAll) countAll.textContent = visibleCount;

      // Apply sort to visible cards
      applySort();
    }

    function applySort() {
      var visible = cards.filter(function(c) { return c.style.display !== 'none'; });
      if (activeSort === 'default') return;
      visible.sort(function(a, b) {
        var va = 0, vb = 0;
        switch (activeSort) {
          case 'stars-desc':   va = parseInt(a.dataset.stars||'0',10); vb = parseInt(b.dataset.stars||'0',10); return vb - va;
          case 'stars-asc':   va = parseInt(a.dataset.stars||'0',10); vb = parseInt(b.dataset.stars||'0',10); return va - vb;
          case 'forks-desc':  va = parseInt(a.dataset.forks||'0',10);  vb = parseInt(b.dataset.forks||'0',10);  return vb - va;
          case 'forks-asc':   va = parseInt(a.dataset.forks||'0',10);  vb = parseInt(b.dataset.forks||'0',10);  return va - vb;
          case 'issues-desc': va = parseInt(a.dataset.issues||'0',10); vb = parseInt(b.dataset.issues||'0',10); return vb - va;
          case 'updated-desc':va = a.dataset.pushed || ''; vb = b.dataset.pushed || ''; return vb.localeCompare(va);
          case 'updated-asc': va = a.dataset.pushed || ''; vb = b.dataset.pushed || ''; return va.localeCompare(vb);
          case 'created-desc':va = a.dataset.created || ''; vb = b.dataset.created || ''; return vb.localeCompare(va);
          case 'created-asc': va = a.dataset.created || ''; vb = b.dataset.created || ''; return va.localeCompare(vb);
          case 'name-asc':   va = a.dataset.name || ''; vb = b.dataset.name || ''; return va.localeCompare(vb);
          case 'name-desc':  va = a.dataset.name || ''; vb = b.dataset.name || ''; return vb.localeCompare(va);
          case 'year-2026': va = (a.dataset.created||'').startsWith('2026'); vb = (b.dataset.created||'').startsWith('2026'); return vb - va;
          case 'year-2025': va = (a.dataset.created||'').startsWith('2025'); vb = (b.dataset.created||'').startsWith('2025'); return vb - va;
          case 'year-2024': va = !(a.dataset.created||'').startsWith('2025') && !(a.dataset.created||'').startsWith('2026'); vb = !(b.dataset.created||'').startsWith('2025') && !(b.dataset.created||'').startsWith('2026'); return vb - va;
        }
        return 0;
      });
      visible.forEach(function(c) { grid.appendChild(c); });
    }

    // ── Filter buttons ─────────────────────────────────────────────────
    filterBtns.forEach(function(btn) {
      btn.addEventListener('click', function() {
        activeFilter = this.dataset.filter;
        filterBtns.forEach(function(b) { b.classList.remove('active'); });
        this.classList.add('active');
        applyFilters();
      });
    });

    // ── Search ──────────────────────────────────────────────────────
    var searchDebounce;
    if (searchInput) {
      searchInput.addEventListener('input', function() {
        clearTimeout(searchDebounce);
        searchDebounce = setTimeout(function() {
          activeQuery = searchInput.value;
          applyFilters();
        }, 200);
      });
    }

    // ── Sort ────────────────────────────────────────────────────────
    if (sortSelect) {
      sortSelect.addEventListener('change', function() {
        activeSort = sortSelect.value;
        applyFilters();
      });
    }

    // ── Initial render ───────────────────────────────────────────────
    applyFilters();
  });
})();
</script>

<style>
.repos-page { padding: 40px 0 80px; }
.repos-breadcrumb { display: flex; align-items: center; gap: 8px; font-size: 0.875rem; color: var(--fg-subtle); margin-bottom: 40px; }
.repos-breadcrumb a { color: var(--fg-subtle); }
.repos-breadcrumb a:hover { color: var(--accent); }
.repos-breadcrumb span[aria-current] { color: var(--fg); font-weight: 500; }

.repos-header { text-align: center; margin-bottom: 32px; }
.repos-header h1 { margin-bottom: 12px; }
.repos-subtitle { font-size: 1.125rem; color: var(--fg-muted); max-width: 600px; margin: 0 auto; }

.repos-toolbar { display: flex; justify-content: space-between; align-items: center; gap: 20px; margin-bottom: 24px; flex-wrap: wrap; }
.repos-filters { display: flex; gap: 10px; flex-wrap: wrap; }
.filter-btn { padding: 8px 18px; font-size: 0.8125rem; font-weight: 500; color: var(--fg-muted); background: var(--bg-card); border: 1px solid var(--border); border-radius: 999px; cursor: pointer; transition: all var(--transition); }
.filter-btn:hover { color: var(--fg); border-color: var(--border-hover); }
.filter-btn.active { color: white; background: var(--accent); border-color: var(--accent); }

.repo-search { padding: 10px 16px; font-size: 0.875rem; color: var(--fg); background: var(--bg-card); border: 1px solid var(--border); border-radius: 999px; min-width: 240px; }
.repo-search:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-dim); }
.repo-search::placeholder { color: var(--fg-subtle); }

.repos-controls { display: flex; gap: 10px; flex-wrap: wrap; }
.repo-sort { padding: 9px 14px; font-size: 0.85rem; color: var(--fg); background: var(--bg-card); border: 1px solid var(--border); border-radius: 999px; cursor: pointer; appearance: none; -webkit-appearance: none; min-width: 200px; font-family: var(--font-ui); transition: border-color var(--transition); }
.repo-sort:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-dim); }
.repo-sort:hover { border-color: var(--border-hover); }

.repos-stats { display: flex; justify-content: center; gap: 32px; margin-bottom: 32px; font-size: 0.875rem; color: var(--fg-subtle); flex-wrap: wrap; }
.repos-stats .stat { display: flex; align-items: center; gap: 6px; }
.repos-stats strong { color: var(--fg); font-family: var(--font-mono); }

.repos-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
.repo-card { display: flex; flex-direction: column; padding: 24px; background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); transition: all var(--transition); position: relative; opacity: 0; }
.repo-card.visible { opacity: 1; }
.repo-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, var(--accent), var(--accent-strong)); border-radius: var(--radius) var(--radius) 0 0; opacity: 0; transition: opacity var(--transition); }
.repo-card:hover { border-color: var(--accent); transform: translateY(-4px); box-shadow: var(--shadow-lg); }
.repo-card:hover::before { opacity: 1; }

.repo-card-deprecated-badge { display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; font-size: 0.68rem; font-weight: 700; font-family: var(--font-mono); color: #f59e0b; background: rgba(245,158,11,0.1); border: 1px solid rgba(245,158,11,0.4); border-radius: 4px; margin-bottom: 8px; }
.repo-card-successor { font-size: 0.78rem; color: var(--fg-muted); margin-bottom: 8px; }
.repo-card-successor a { color: var(--accent); }
.repo-card-successor a:hover { text-decoration: underline; }

.repo-card-icon { display: inline-flex; align-items: center; justify-content: center; width: 48px; height: 48px; border-radius: var(--radius-sm); background: var(--accent-dim); color: var(--accent); margin-bottom: 16px; }
.repo-card-icon svg { width: 24px; height: 24px; }

.repo-card-name { margin-bottom: 10px; font-size: 1.0625rem; display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }
.repo-card-name a { color: var(--fg); text-decoration: none; transition: color var(--transition); }
.repo-card-name a:hover { color: var(--accent); }
.featured-badge { font-size: 0.75rem; color: var(--orange); animation: pulse 2s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.15); } }

.repo-card-desc { font-size: 0.875rem; line-height: 1.5; color: var(--fg-muted); margin-bottom: 16px; flex: 1; }

.repo-card-meta { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; font-size: 0.75rem; font-family: var(--font-mono); }
.repo-platform, .repo-lang, .repo-category { padding: 3px 8px; background: var(--bg); border: 1px solid var(--border); border-radius: 4px; color: var(--fg-subtle); }

.repo-card-stats { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 12px; }
.stat-item { display: inline-flex; align-items: center; gap: 4px; font-size: 0.78rem; font-family: var(--font-mono); color: var(--fg-muted); }
.stat-item svg { opacity: 0.7; }

.repo-card-links { display: flex; gap: 10px; margin-top: auto; }
.repo-link { display: inline-flex; align-items: center; gap: 6px; padding: 10px 16px; font-size: 0.8125rem; font-weight: 600; border-radius: var(--radius-sm); background: var(--accent-dim); color: var(--accent); border: 1px solid transparent; transition: all var(--transition); text-decoration: none; }
.repo-link:hover { background: var(--accent); color: white; }
.repo-link-external { background: transparent; color: var(--fg-muted); border-color: var(--border); }
.repo-link-external:hover { background: var(--bg); color: var(--fg); border-color: var(--border-hover); }

.repo-card-actions { display: flex; gap: 6px; margin-top: 10px; }
.repo-action-btn { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; font-size: 0.72rem; font-weight: 600; border-radius: 4px; text-decoration: none; border: 1px solid; transition: all var(--transition); }
.repo-action-bug { color: var(--orange); border-color: var(--orange); background: rgba(255,167,38,0.06); }
.repo-action-bug:hover { background: rgba(255,167,38,0.15); }
.repo-action-sec { color: var(--red); border-color: var(--red); background: rgba(239,83,80,0.06); }
.repo-action-sec:hover { background: rgba(239,83,80,0.15); }
.repo-action-disc { color: var(--green); border-color: var(--green); background: rgba(102,187,106,0.06); }
.repo-action-disc:hover { background: rgba(102,187,106,0.15); }

.repos-footer { text-align: center; margin-top: 48px; padding-top: 24px; border-top: 1px solid var(--border); color: var(--fg-subtle); font-size: 0.875rem; }
.repos-footer a { color: var(--fg-subtle); }
.repos-footer a:hover { color: var(--accent); }

@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

@media (max-width: 768px) {
  .repos-grid { grid-template-columns: 1fr; }
  .repos-toolbar { flex-direction: column; align-items: stretch; }
  .repos-filters { justify-content: center; }
  .repo-search { width: 100%; min-width: 0; }
  .repos-stats { gap: 16px; font-size: 0.8125rem; }
}
</style>