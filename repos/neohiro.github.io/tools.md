---
layout: default
title: OS App Selector — neohiro Tools Index
description: "Interactive OS app selector and tool index with vicinity blooming magnification. Launch open-source security hardening and privacy tools instantly."
permalink: /tools/
---

<div class="container" style="padding: 60px 24px;">
  <!-- OS App Selector Grid Div -->
  <div class="os-app-selector" id="os-app-selector">
    <div class="os-grid">
      {% assign all_tools = site.data.repos.repos | sort: "weight" %}
      {% for tool in all_tools %}
        <a href="{{ tool.repo_url }}" class="os-app-tile" target="_blank" rel="noopener" aria-label="{{ tool.title }}">
          <div class="os-app-icon" aria-hidden="true">
            {% if tool.category contains 'Network' or tool.category contains 'Security' %}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg>
            {% elsif tool.category contains 'Games' %}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="6" width="20" height="12" rx="2"/><path d="M7 12h.01M12 12h.01M17 12h.01"/></svg>
            {% elsif tool.category contains 'Developer' %}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M16 18l6-6-6-6"/><path d="M8 6l-6 6 6 6"/></svg>
            {% elsif tool.category contains 'Cryptography' %}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.778-7.778zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg>
            {% else %}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="3"/><path d="M9 12h6M12 9v6"/></svg>
            {% endif %}
          </div>
          <span class="os-app-title">{{ tool.title }}</span>
          <span class="os-app-sub">{{ tool.language | split: ' ' | first }}</span>
        </a>
      {% endfor %}
    </div>
  </div>

  <div style="text-align: center; margin-top: 40px;">
    <a href="{{ '/repositories/' | relative_url }}" class="btn btn-primary">View Full Repository Table →</a>
  </div>
</div>

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