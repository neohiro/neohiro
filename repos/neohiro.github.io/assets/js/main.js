// neohiro.github.io - Main JavaScript
// Matrix rain, glitch transitions, parallax, card animations, video embeds

(function() {
  'use strict';

  // Module-scoped reference to the GlitchTransition instance, so the
  // visibility-reset helper (registered before DOMContentLoaded) can clear its
  // internal `active` latch after a bfcache restore. Without this, the restored
  // page keeps active === true and silently stops animating page transitions.
  let glitchInstance = null;

  // ============================================
  // MATRIX RAIN BACKGROUND (constrained to hero area)
  // ============================================
  class MatrixRain {
    constructor() {
      this.canvas = document.getElementById('matrix-canvas');
      if (!this.canvas) return;
      this.ctx = this.canvas.getContext('2d');
      this.chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789$#@%&*';
      this.fontSize = 14;
      this.columns = 0;
      this.drops = [];
      this.running = false;
      this.init();
    }

    init() {
      this.resize();
      window.addEventListener('resize', () => this.resize());
      this.running = true;
      this.animate();
    }

    resize() {
      // Canvas is absolute-positioned inside .hero, so its layout size matches hero
      const rect = this.canvas.getBoundingClientRect();
      this.canvas.width = rect.width;
      this.canvas.height = Math.max(rect.height, 400);
      this.columns = Math.floor(this.canvas.width / this.fontSize);
      this.drops = Array(this.columns).fill(1);
    }

    animate() {
      if (!this.running) return;
      
      this.ctx.fillStyle = 'rgba(11, 14, 18, 0.05)';
      this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
      
      this.ctx.font = `${this.fontSize}px 'JetBrains Mono', monospace`;
      this.ctx.fillStyle = '#7c4dff';
      
      for (let i = 0; i < this.drops.length; i++) {
        const char = this.chars[Math.floor(Math.random() * this.chars.length)];
        const x = i * this.fontSize;
        const y = this.drops[i] * this.fontSize;
        
        this.ctx.fillText(char, x, y);
        
        if (y > this.canvas.height && Math.random() > 0.975) {
          this.drops[i] = 0;
        }
        this.drops[i]++;
      }
      
      requestAnimationFrame(() => this.animate());
    }

    destroy() {
      this.running = false;
    }
  }

  // ============================================
  // GLITCH TRANSITION OVERLAY
  // ============================================
  class GlitchTransition {
    constructor() {
      this.overlay = document.getElementById('glitch-overlay');
      this.active = false;
    }

    trigger(targetUrl, isInternal = true) {
      if (this.active) return;
      this.active = true;

      let isAnchor = false;
      let targetId = null;
      try {
        const parsed = new URL(targetUrl, window.location.href);
        if (parsed.origin === window.location.origin && parsed.pathname === window.location.pathname && parsed.hash) {
          isAnchor = true;
          targetId = parsed.hash.slice(1);
        }
      } catch (err) {
        if (typeof targetUrl === 'string' && targetUrl.startsWith('#')) {
          isAnchor = true;
          targetId = targetUrl.slice(1);
        }
      }
      
      const text = this.overlay.querySelector('.glitch-text');
      text.textContent = isInternal ? 'NEOHIRO' : 'REDIRECTING';
      
      this.overlay.classList.add('active');
      
      // Glitch animation
      let glitchCount = 0;
      const glitchInterval = setInterval(() => {
        text.style.transform = `translate(${Math.random() * 4 - 2}px, ${Math.random() * 4 - 2}px) skew(${Math.random() * 4 - 2}deg)`;
        text.style.textShadow = `${Math.random() * 10 - 5}px ${Math.random() * 10 - 5}px 0 #ff00ff, ${Math.random() * 10 - 5}px ${Math.random() * 10 - 5}px 0 #00ffff`;
        glitchCount++;
        if (glitchCount > 8) clearInterval(glitchInterval);
      }, 50);
      
      setTimeout(() => {
        clearInterval(glitchInterval);
        text.style.transform = '';
        text.style.textShadow = '';
        
        if (isAnchor) {
          const targetEl = targetId ? document.getElementById(targetId) : null;
          if (targetEl) {
            targetEl.scrollIntoView({ behavior: 'smooth' });
            history.pushState(null, '', '#' + targetId);
            setTimeout(() => {
              this.overlay.classList.remove('active');
              document.body.style.opacity = '1';
              this.active = false;
            }, 150);
          } else {
            // Anchor element doesn't exist on this page, navigate to root with hash.
            // No body fade - see the note in the internal-link branch above.
            setTimeout(() => {
              window.location.href = '/' + (targetId ? '#' + targetId : '');
            }, 150);
          }
        } else if (isInternal) {
          // Navigate behind the opaque overlay. We deliberately do NOT fade
          // document.body here: that inline `opacity: 0` is captured by the
          // bfcache entry for this page and is exactly what left the page blank
          // on Back/Forward until a manual refresh. The full-screen overlay is
          // the transition, so the body fade added nothing but the bug.
          setTimeout(() => {
            window.location.href = targetUrl;
          }, 150);
        } else {
          // External links - brief pause then redirect
          setTimeout(() => {
            window.open(targetUrl, '_blank', 'noopener,noreferrer');
            this.overlay.classList.remove('active');
            this.active = false;
          }, 300);
        }
      }, 400);
    }
  }

  // ============================================
  // PARALLAX BACKGROUND
  // ============================================
  class ParallaxBackground {
    constructor() {
      this.hero = document.querySelector('.hero');
      this.ticking = false;
      if (this.hero) this.init();
    }

    init() {
      window.addEventListener('mousemove', (e) => {
        if (!this.ticking) {
          window.requestAnimationFrame(() => {
            this.update(e.clientX, e.clientY);
            this.ticking = false;
          });
          this.ticking = true;
        }
      });
    }

    update(x, y) {
      const centerX = window.innerWidth / 2;
      const centerY = window.innerHeight / 2;
      const deltaX = (x - centerX) / centerX;
      const deltaY = (y - centerY) / centerY;
      
      const cards = document.querySelectorAll('.tool-card, .guide-card, .community-card');
      cards.forEach((card, i) => {
        const factor = (i % 3 + 1) * 2;
        card.style.transform = `translate(${deltaX * factor}px, ${deltaY * factor}px)`;
      });
    }
  }

  // ============================================
  // CARD INTERACTIONS & NEON EFFECTS
  // ============================================
  class CardEffects {
    constructor() {
      this.cards = document.querySelectorAll('.tool-card, .guide-card, .community-card, .repo-card');
      this.init();
    }

    init() {
      this.cards.forEach(card => {
        card.addEventListener('mouseenter', (e) => this.onEnter(e, card));
        card.addEventListener('mouseleave', (e) => this.onLeave(e, card));
        card.addEventListener('mousemove', (e) => this.onMove(e, card));
        card.addEventListener('click', (e) => this.onClick(e, card));
      });
    }

    onEnter(e, card) {
      card.style.transition = 'transform 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94), box-shadow 0.3s ease';
      card.style.transform = 'translateY(-8px) scale(1.02)';
      card.style.boxShadow = '0 20px 60px rgba(124, 77, 255, 0.25), 0 0 40px rgba(124, 77, 255, 0.1)';
      
      // Neon border pulse
      card.style.animation = 'neon-pulse 2s ease-in-out infinite';
      
      // Add glow to icon
      const icon = card.querySelector('.tool-icon, .guide-icon, .repo-card-icon');
      if (icon) {
        icon.style.boxShadow = '0 0 30px var(--accent)';
        icon.style.transform = 'scale(1.1) rotate(5deg)';
      }
    }

    onLeave(e, card) {
      card.style.transition = 'transform 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94), box-shadow 0.5s ease';
      card.style.transform = '';
      card.style.boxShadow = '';
      card.style.animation = '';
      
      const icon = card.querySelector('.tool-icon, .guide-icon, .repo-card-icon');
      if (icon) {
        icon.style.boxShadow = '';
        icon.style.transform = '';
      }
    }

    onMove(e, card) {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      
      const rotateX = (y - centerY) / centerY * 5;
      const rotateY = (centerX - x) / centerX * 5;
      
      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-8px) scale(1.02)`;
    }

    onClick(e, card) {
      // Ripple effect
      const ripple = document.createElement('div');
      ripple.className = 'ripple';
      const rect = card.getBoundingClientRect();
      ripple.style.left = `${e.clientX - rect.left}px`;
      ripple.style.top = `${e.clientY - rect.top}px`;
      card.appendChild(ripple);
      
      setTimeout(() => ripple.remove(), 600);
    }
  }

  // ============================================
  // YOUTUBE VIDEO EMBED MANAGER
  // ============================================
  class VideoEmbedManager {
    constructor() {
      this.embeds = new Map();
      this.init();
    }

    init() {
      // Create video cards from data
      this.videoData = [
        { id: 'dQw4w9WgXcQ', title: 'Windows Hardening Deep Dive', duration: '45:32', views: '124K', thumbnail: 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg' },
        { id: 'dQw4w9WgXcQ', title: 'Network Hardening with Cripple-NetStrip', duration: '38:15', views: '89K', thumbnail: 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg' },
        { id: 'dQw4w9WgXcQ', title: 'Linux Post-Install Security', duration: '52:47', views: '67K', thumbnail: 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg' },
        { id: 'dQw4w9WgXcQ', title: 'Supply Chain Security for PowerShell', duration: '31:22', views: '54K', thumbnail: 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg' },
        { id: 'dQw4w9WgXcQ', title: 'Building Secure Bootstraps', duration: '28:55', views: '43K', thumbnail: 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg' },
        { id: 'dQw4w9WgXcQ', title: 'Advanced Windows Exploit Mitigation', duration: '1:02:18', views: '78K', thumbnail: 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg' }
      ];
      
      this.renderVideoGrid();
    }

    renderVideoGrid() {
      const container = document.getElementById('video-grid');
      if (!container) return;
      
      container.innerHTML = this.videoData.map((video, i) => `
        <article class="video-card" data-video-id="${video.id}" style="--delay: ${i * 100}ms">
          <div class="video-thumbnail">
            <img src="${video.thumbnail}" alt="${video.title}" loading="lazy">
            <div class="video-overlay">
              <button class="play-btn" aria-label="Play ${video.title}">
                <svg viewBox="0 0 24 24" fill="currentColor" width="48" height="48"><path d="M8 5v14l11-7z"/></svg>
              </button>
              <span class="duration">${video.duration}</span>
            </div>
          </div>
          <div class="video-info">
            <h4>${video.title}</h4>
            <span class="video-meta">${video.views} views</span>
          </div>
        </article>
      `).join('');
      
      this.bindVideoEvents(container);
    }

    bindVideoEvents(container) {
      container.querySelectorAll('.video-card').forEach(card => {
        const videoId = card.dataset.videoId;
        let iframe = null;
        let isOpen = false;
        
        card.addEventListener('click', (e) => {
          if (e.target.closest('.play-btn') || e.target === card || e.target.closest('.video-thumbnail')) {
            e.preventDefault();
            e.stopPropagation();
            
            if (!isOpen) {
              this.openVideo(card, videoId);
              isOpen = true;
            }
          }
        });
        
        // Close on outside click
        document.addEventListener('click', (e) => {
          if (isOpen && !card.contains(e.target) && !e.target.closest('.video-modal')) {
            this.closeVideo(card);
            isOpen = false;
          }
        });
        
        // Close on Escape
        document.addEventListener('keydown', (e) => {
          if (e.key === 'Escape' && isOpen) {
            this.closeVideo(card);
            isOpen = false;
          }
        });
      });
    }

    openVideo(card, videoId) {
      // Create modal overlay
      const modal = document.createElement('div');
      modal.className = 'video-modal';
      modal.innerHTML = `
        <div class="video-modal-content">
          <button class="video-close" aria-label="Close video">&times;</button>
          <div class="video-wrapper">
            <iframe 
              src="https://www.youtube-nocookie.com/embed/${videoId}?autoplay=1&rel=0" 
              title="YouTube video" 
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
              allowfullscreen>
            </iframe>
          </div>
        </div>
      `;
      
      document.body.appendChild(modal);
      document.body.style.overflow = 'hidden';
      
      // Animate in
      requestAnimationFrame(() => {
        modal.classList.add('active');
      });
      
      // Close handlers
      modal.querySelector('.video-close').addEventListener('click', () => this.closeVideo(card, modal));
      modal.addEventListener('click', (e) => {
        if (e.target === modal) this.closeVideo(card, modal);
      });
    }

    closeVideo(card, modal) {
      modal.classList.remove('active');
      setTimeout(() => {
        modal.remove();
        document.body.style.overflow = '';
      }, 300);
    }
  }

  // ============================================
  // SMOOTH SCROLL & INTERSECTION OBSERVER
  // ============================================
  class ScrollAnimations {
    constructor() {
      this.observer = null;
      this.init();
    }

    init() {
      this.observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            this.observer.unobserve(entry.target);
          }
        });
      }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
      });

      document.querySelectorAll('.tool-card, .guide-card, .community-card, .repo-card, .section-header, .video-card').forEach(el => {
        el.classList.add('fade-in');
        this.observer.observe(el);
      });
    }
  }

  // ============================================
  // TYPING ANIMATION (Enhanced)
  // ============================================
  class TypingAnimation {
    constructor() {
      this.element = document.querySelector('.typing-prefix');
      this.cursor = document.querySelector('.typing-cursor');
      if (!this.element || !this.cursor) return;
      
      this.phrases = [
        "Open-source security hardening for Windows & Linux.",
        "Exploit mitigation catalogs that actually work.",
        "Encrypted DNS, firewalls, honeypots — zero fluff.",
        "STIG-style Windows hardening in one command.",
        "Network visibility. Traffic control. Zero trust.",
        "Built by FrenzyPenguin Media. No telemetry. Ever.",
        "Auditd, AppArmor, Tor — Linux post-install automated.",
        "Your system. Your rules. Our tooling.",
        "Defense is the best defense.",
        "One command. Zero compromise."
      ];
      
      this.index = 0;
      this.charIndex = 0;
      this.deleting = false;
      this.typeSpeed = 45;
      this.deleteSpeed = 15;
      this.holdTime = 2500;
      this.pauseTime = 500;
      
      this.start();
    }

    start() {
      this.type();
    }

    type() {
      const phrase = this.phrases[this.index];
      
      if (this.deleting) {
        this.element.textContent = phrase.substring(0, this.charIndex - 1);
        this.charIndex--;
      } else {
        this.element.textContent = phrase.substring(0, this.charIndex + 1);
        this.charIndex++;
      }
      
      let delay = this.deleting ? this.deleteSpeed : this.typeSpeed;
      
      if (!this.deleting && this.charIndex === phrase.length) {
        delay = this.holdTime;
        this.deleting = true;
      } else if (this.deleting && this.charIndex === 0) {
        this.deleting = false;
        this.index = (this.index + 1) % this.phrases.length;
        delay = this.pauseTime;
      }
      
      setTimeout(() => this.type(), delay);
    }
  }

  // ============================================
  // REPOSITORY FILTER & SEARCH
  // ============================================
  class RepoFilter {
    constructor() {
      this.grid = document.getElementById('repos-grid');
      this.buttons = document.querySelectorAll('.filter-btn');
      this.search = document.querySelector('.repo-search');
      this.init();
    }

    init() {
      this.buttons.forEach(btn => {
        btn.addEventListener('click', () => this.filter(btn.dataset.filter));
      });
      
      if (this.search) {
        let debounce;
        this.search.addEventListener('input', () => {
          clearTimeout(debounce);
          debounce = setTimeout(() => this.searchRepos(this.search.value), 200);
        });
      }
    }

    filter(category) {
      this.buttons.forEach(b => b.classList.remove('active'));
      document.querySelector(`[data-filter="${category}"]`)?.classList.add('active');
      
      const cards = this.grid.querySelectorAll('.repo-card');
      cards.forEach(card => {
        const cats = card.dataset.category || '';
        const show = category === 'all' || cats.includes(category);
        card.style.display = show ? 'flex' : 'none';
        if (show) card.style.animation = 'fadeInUp 0.4s ease forwards';
      });
    }

    searchRepos(query) {
      const q = query.toLowerCase().trim();
      const cards = this.grid.querySelectorAll('.repo-card');
      
      cards.forEach(card => {
        const name = card.dataset.name || '';
        const desc = card.querySelector('.repo-card-desc')?.textContent.toLowerCase() || '';
        const lang = card.dataset.language || '';
        const cat = card.dataset.category || '';
        
        const match = !q || name.includes(q) || desc.includes(q) || lang.includes(q) || cat.includes(q);
        card.style.display = match ? 'flex' : 'none';
      });
    }
  }

  // ============================================
  // LINK GUARD (Confirmation + Repo Tabs + Iframe Embed)
  // ============================================
  // Catches clicks to GitHub/external destinations, shows a confirmation
  // popup with information about the destination, a quick repo-tab jump
  // selector, and an in-page iframe preview. Visitors can open in a new
  // tab, open directly, or jump to a specific tab (Issues, Discussions,
  // Security, Wiki, Pulse, etc.) without leaving the site first.

  const REPO_TABS = [
    { id: 'overview',  label: 'Overview',          icon: '📖', path: '' },
    { id: 'issues',    label: 'Bug Reports',       icon: '🐞', path: '/issues' },
    { id: 'security',  label: 'Security Vulns',    icon: '🛡️', path: '/security' },
    { id: 'discussions', label: 'Discussions',     icon: '💬', path: '/discussions' },
    { id: 'pulse',     label: 'Pulse',             icon: '📊', path: '/pulse' },
    { id: 'wiki',      label: 'Wiki',              icon: '📚', path: '/wiki' },
    { id: 'releases',  label: 'Releases',          icon: '🚀', path: '/releases' },
    { id: 'code',      label: 'Code',              icon: '⌨️', path: '' },
    { id: 'pulls',     label: 'Pull Requests',     icon: '🔀', path: '/pulls' },
    { id: 'actions',   label: 'Actions',           icon: '⚙️', path: '/actions' }
  ];

  class LinkGuard {
    constructor() {
      this.owner = 'neohiro';
      this.overlay = null;
      this.iframe = null;
      this.lastTrigger = null;
      this.currentRepo = null;
      this.init();
    }

    init() {
      // Build a static overlay element once
      this.overlay = document.createElement('div');
      this.overlay.className = 'link-guard';
      this.overlay.setAttribute('role', 'dialog');
      this.overlay.setAttribute('aria-modal', 'true');
      this.overlay.setAttribute('aria-labelledby', 'link-guard-title');
      this.overlay.innerHTML = `
        <div class="link-guard-backdrop" data-close></div>
        <div class="link-guard-card">
          <header class="link-guard-header">
            <div class="link-guard-icon" aria-hidden="true">🔗</div>
            <div class="link-guard-heading">
              <h2 id="link-guard-title">Leaving neohiro</h2>
              <p class="link-guard-sub" id="link-guard-sub">External destination</p>
            </div>
            <button class="link-guard-close" data-close aria-label="Close">×</button>
          </header>
          <section class="link-guard-body">
            <div class="link-guard-meta" id="link-guard-meta"></div>
            <div class="link-guard-url" id="link-guard-url"></div>
            <div class="link-guard-frame" id="link-guard-frame" hidden>
              <iframe id="link-guard-iframe" title="Destination preview"
                      loading="lazy" referrerpolicy="no-referrer"></iframe>
            </div>
          </section>
          <section class="link-guard-tabs" id="link-guard-tabs" hidden>
            <label class="link-guard-section-label">Jump to repository section</label>
            <div class="link-guard-row">
              <select class="link-guard-tab" id="link-guard-tab" aria-label="Section">
                ${REPO_TABS.map(t => `<option value="${t.id}">${t.icon} ${t.label}</option>`).join('')}
              </select>
              <button class="link-guard-go" id="link-guard-go" type="button">Open Section</button>
            </div>
            <p class="link-guard-hint">Opens the chosen section of this repository directly in a new tab.</p>
          </section>
          <footer class="link-guard-actions">
            <button class="link-guard-btn link-guard-btn-ghost" data-close>Stay here</button>
            <button class="link-guard-btn link-guard-btn-primary" id="link-guard-open">Open in new tab</button>
          </footer>
        </div>
      `;
      document.body.appendChild(this.overlay);

      this.iframe = this.overlay.querySelector('#link-guard-iframe');

      // Bind events
      this.overlay.addEventListener('click', (e) => {
        if (e.target.matches('[data-close]')) this.close();
      });
      this.overlay.querySelector('#link-guard-open').addEventListener('click', () => this.openInNewTab());
      this.overlay.querySelector('#link-guard-go').addEventListener('click', () => this.openRepoTab());

      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && this.overlay.classList.contains('active')) this.close();
      });

      this.bindTriggers();
    }

    bindTriggers() {
      // Re-bind on every card/repo render
      const wire = (link) => {
        if (link.__linkGuardBound) return;
        link.__linkGuardBound = true;
        link.addEventListener('click', (e) => {
          if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
          const href = link.href;
          if (!href) return;
          if (this.shouldIntercept(href, link)) {
            e.preventDefault();
            this.open(href, link);
          }
        });
      };

      // Catch external links and github.com/* links
      const all = document.querySelectorAll('a[href]');
      all.forEach(wire);

      // Watch for dynamically added links
      const obs = new MutationObserver((muts) => {
        muts.forEach(m => m.addedNodes.forEach(n => {
          if (n.nodeType !== 1) return;
          if (n.matches && n.matches('a[href]')) wire(n);
          if (n.querySelectorAll) n.querySelectorAll('a[href]').forEach(wire);
        }));
      });
      obs.observe(document.body, { childList: true, subtree: true });
    }

    shouldIntercept(href, link) {
      // Skip in-page anchors and internal site links
      if (href.startsWith('#')) return false;
      const u = new URL(href, window.location.href);
      if (u.hostname === window.location.hostname && !u.hostname.includes('github.com')) return false;

      // Skip sponsor and a few friendly external links
      if (link && (link.dataset.linkGuard === 'off')) return false;

      // Intercept github.com and unknown external links
      if (u.hostname === 'github.com' || u.hostname.endsWith('.github.com')) return true;
      if (u.hostname === 'linktr.ee' || u.hostname === 'youtube.com' || u.hostname === 'www.youtube.com') return true;

      // Default: intercept anything that opens in new tab OR anything external
      if (link && link.target === '_blank') return true;
      if (u.hostname !== window.location.hostname) return true;
      return false;
    }

    inferRepo(url) {
      try {
        const u = new URL(url);
        if (u.hostname === 'github.com' || u.hostname === 'www.github.com') {
          const m = u.pathname.match(/^\/([^\/]+)\/([^\/]+)/);
          if (m && m[1].toLowerCase() === this.owner) return m[2];
        }
      } catch (e) {}
      return null;
    }

    isIssuesPage(url) {
      return /\/issues(\?|\/|$|#)/.test(url);
    }
    isSecurityPage(url) {
      return /\/security(\?|\/|$|#)/.test(url);
    }
    isDiscussionsPage(url) {
      return /\/discussions(\?|\/|$|#)/.test(url);
    }

    describe(url) {
      const u = new URL(url);
      const host = u.hostname;
      const repo = this.inferRepo(url);
      const desc = (() => {
        if (host.includes('github.com')) {
          if (this.isIssuesPage(url))    return 'Bug reports & open issues for the repository.';
          if (this.isSecurityPage(url))  return 'Security advisories for the repository — please disclose privately when possible.';
          if (this.isDiscussionsPage(url)) return 'Community discussions for the repository.';
          if (/\/releases(\?|\/|$|#)/.test(url)) return 'Releases / downloads for the repository.';
          if (/\/actions(\?|\/|$|#)/.test(url))  return 'CI / Actions runs for the repository.';
          if (/\/wiki(\?|\/|$|#)/.test(url))     return 'Project wiki.';
          if (/\/sponsors/.test(u.pathname))     return 'Sponsor the project via GitHub Sponsors.';
          if (/\/[^\/]+\/[^\/]+$/.test(u.pathname)) {
            return `GitHub repository page${repo ? ` for ${repo}` : ''}.`;
          }
          return 'A page on github.com.';
        }
        if (host.includes('youtube.com')) return 'A YouTube page — video / channel / playlist.';
        if (host.includes('linktr.ee'))   return 'Linktree — all public links for the project.';
        if (host.includes('sponsor'))     return 'Sponsor page.';
        if (host.includes('frenzypenguin.media') || host.includes('frenzypenguin')) return 'FrenzyPenguin Media — music artist recordings & creative projects.';
        if (host.includes('transhumanists')) return 'Transhumanists (H+) — research, philosophy & longevity ecosystem.';
        return `External destination on ${host}.`;
      })();

      const isIssues = this.isIssuesPage(url);
      const isSecurity = this.isSecurityPage(url);
      const isDisc = this.isDiscussionsPage(url);
      const isRepo = !!repo && /^\/[^\/]+\/[^\/]+(\/)?$/.test(u.pathname);

      return { repo, isIssues, isSecurity, isDisc, isRepo, desc };
    }

    open(url, trigger) {
      this.lastTrigger = trigger;
      this.lastUrl = url;
      let info, u;
      try {
        info = this.describe(url);
        u = new URL(url);
      } catch (e) {
        // Malformed URL — bypass modal and open directly
        this.close();
        if (url) window.open(url, '_blank', 'noopener,noreferrer');
        return;
      }

      // Title + sub
      this.overlay.querySelector('#link-guard-title').textContent =
        (u.hostname.includes('github.com') ? 'Open on GitHub' :
         u.hostname.includes('youtube')    ? 'Open on YouTube' :
         u.hostname.includes('linktr')     ? 'Open Linktree' :
         'Open external page');
      this.overlay.querySelector('#link-guard-sub').textContent = info.desc;

      // Meta chips
      const meta = this.overlay.querySelector('#link-guard-meta');
      const chips = [];
      chips.push(`<span class="link-guard-chip"><strong>Host</strong> ${this.escape(u.hostname)}</span>`);
      if (info.isRepo) chips.push(`<span class="link-guard-chip"><strong>Repo</strong> ${this.escape(info.repo)}</span>`);
      if (info.isIssues) chips.push(`<span class="link-guard-chip chip-warn">Bug reports</span>`);
      if (info.isSecurity) chips.push(`<span class="link-guard-chip chip-alert">Security</span>`);
      if (info.isDisc) chips.push(`<span class="link-guard-chip">Discussions</span>`);
      meta.innerHTML = chips.join('');

      // URL display
      this.overlay.querySelector('#link-guard-url').textContent = u.href;

      // Iframe preview (blocked for github.com and youtube.com)
      const frame = this.overlay.querySelector('#link-guard-frame');
      const tryIframe = this.isEmbeddable(u);
      if (tryIframe) {
        this.iframe.src = u.href;
        frame.hidden = false;
      } else {
        frame.hidden = true;
        this.iframe.src = 'about:blank';
      }

      // Quick jump: only for github.com/<owner>/<repo>
      const tabsEl = this.overlay.querySelector('#link-guard-tabs');
      const tabSel = this.overlay.querySelector('#link-guard-tab');
      const labelEl = this.overlay.querySelector('.link-guard-section-label');
      if (info.isRepo && info.repo) {
        this.currentRepo = info.repo;
        if (labelEl) labelEl.textContent = `Jump to ${this.escape(info.repo)} section`;
        if (info.isIssues) tabSel.value = 'issues';
        else if (info.isSecurity) tabSel.value = 'security';
        else if (info.isDisc) tabSel.value = 'discussions';
        else tabSel.value = 'overview';
        tabsEl.hidden = false;
      } else {
        this.currentRepo = null;
        tabsEl.hidden = true;
      }

      this.overlay.classList.add('active');
      this.overlay.querySelector('#link-guard-open').focus();
    }

    isEmbeddable(u) {
      if (u.hostname.includes('github.com')) return false;
      if (u.hostname.includes('youtube.com')) return false;
      if (u.protocol !== 'https:') return false;
      return true;
    }

    openInNewTab() {
      if (this.lastUrl) window.open(this.lastUrl, '_blank', 'noopener,noreferrer');
      this.close();
    }

    openRepoTab() {
      const repo = this.currentRepo;
      if (!repo) return;
      const tabId = this.overlay.querySelector('#link-guard-tab').value;
      const tab = REPO_TABS.find(t => t.id === tabId) || REPO_TABS[0];
      const url = `https://github.com/${this.owner}/${repo}${tab.path}`;
      window.open(url, '_blank', 'noopener,noreferrer');
      this.close();
    }

    close() {
      this.overlay.classList.remove('active');
      this.iframe.src = 'about:blank';
    }

    escape(s) {
      return String(s).replace(/[&<>"']/g, c => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
      }[c]));
    }
  }

  // ============================================
  // INITIALIZATION
  // ============================================
  function init() {
    // Initialize all components
    new MatrixRain();
    const glitch = new GlitchTransition();
    glitchInstance = glitch;
    new ParallaxBackground();
    new CardEffects();
    new ScrollAnimations();
    new TypingAnimation();
    new RepoFilter();
    new VideoEmbedManager();
    new LinkGuard();

    // BFCache restoration: ensure page is visible on back/forward navigation.
    // resetVisibility() is defined at module scope (see bottom of file) so it is
    // registered even if this init() throws before reaching this line.
    window.addEventListener('pageshow', resetVisibility);

    // Bind glitch transitions to internal links
    document.querySelectorAll('a[href^="/"], a[href^="#"], a[href^="./"]').forEach(link => {
      if (link.hostname === window.location.hostname || link.href.startsWith('/') || link.href.startsWith('#')) {
        link.addEventListener('click', (e) => {
          if (!e.metaKey && !e.ctrlKey && !e.shiftKey) {
            e.preventDefault();
            glitch.trigger(link.href, true);
          }
        });
      }
    });
    
    // External links
    document.querySelectorAll('a[target="_blank"]').forEach(link => {
      link.addEventListener('click', (e) => {
        glitch.trigger(link.href, false);
      });
    });
    
    // Add ripple CSS
    const style = document.createElement('style');
    style.textContent = `
      .ripple {
        position: absolute;
        width: 20px; height: 20px;
        background: radial-gradient(circle, rgba(124,77,255,0.4) 0%, transparent 70%);
        border-radius: 50%;
        transform: translate(-50%, -50%) scale(0);
        animation: ripple 0.6s ease-out;
        pointer-events: none;
        z-index: 10;
      }
      @keyframes ripple { to { transform: translate(-50%, -50%) scale(20); opacity: 0; } }
      
      .fade-in { opacity: 0; transform: translateY(30px); transition: opacity 0.6s ease, transform 0.6s ease; }
      .fade-in.visible { opacity: 1; transform: translateY(0); }
      
      .video-card { opacity: 0; transform: translateY(20px); animation: fadeInUp var(--delay) ease forwards; }
      @keyframes fadeInUp { to { opacity: 1; transform: translateY(0); } }
      
      .video-thumbnail { position: relative; border-radius: var(--radius); overflow: hidden; }
      .video-thumbnail img { width: 100%; height: auto; display: block; transition: transform 0.3s ease; }
      .video-card:hover .video-thumbnail img { transform: scale(1.05); }
      .video-overlay { position: absolute; inset: 0; background: rgba(11,14,18,0.8); display: flex; align-items: center; justify-content: center; opacity: 0; transition: opacity 0.3s ease; }
      .video-card:hover .video-overlay { opacity: 1; }
      .play-btn { background: linear-gradient(135deg, var(--accent), var(--accent-strong)); border: none; border-radius: 50%; width: 72px; height: 72px; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; box-shadow: 0 8px 32px rgba(124,77,255,0.4); }
      .play-btn:hover { transform: scale(1.15); box-shadow: 0 12px 48px rgba(124,77,255,0.6); }
      .duration { position: absolute; bottom: 12px; right: 12px; background: rgba(0,0,0,0.8); color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-family: var(--font-mono); }
      .video-info { padding: 12px; }
      .video-info h4 { font-size: 0.9375rem; margin-bottom: 4px; color: var(--fg); }
      .video-meta { font-size: 0.75rem; color: var(--fg-subtle); font-family: var(--font-mono); }
      
      .video-modal { position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 10000; display: flex; align-items: center; justify-content: center; opacity: 0; visibility: hidden; transition: opacity 0.3s ease, visibility 0.3s ease; }
      .video-modal.active { opacity: 1; visibility: visible; }
      .video-modal-content { position: relative; width: 90%; max-width: 900px; aspect-ratio: 16/9; }
      .video-close { position: absolute; top: -50px; right: 0; background: none; border: none; color: var(--fg-muted); font-size: 2rem; cursor: pointer; transition: color 0.2s; }
      .video-close:hover { color: var(--accent); }
      .video-wrapper { width: 100%; height: 100%; border-radius: var(--radius); overflow: hidden; }
      .video-wrapper iframe { width: 100%; height: 100%; border: none; }
      
      @keyframes neon-pulse { 0%,100% { box-shadow: 0 20px 60px rgba(124,77,255,0.25), 0 0 40px rgba(124,77,255,0.1); } 50% { box-shadow: 0 20px 80px rgba(124,77,255,0.4), 0 0 80px rgba(124,77,255,0.2); } }
      
      /* pointer-events is the load-bearing part of the idle state: this overlay is
         position:fixed; inset:0 at z-index 9999, above the back-to-top control
         (940) and the bottom dock (900), and elementFromPoint at the arrow's
         centre returned this div, swallowing every click. It is also injected at
         runtime, so before injection it is an unstyled div with no pointer-events.
         Fixed on frenzypenguin-media first; applied here for the same reason. */
      .glitch-overlay { position: fixed; inset: 0; background: var(--bg); z-index: 9999; display: flex; align-items: center; justify-content: center; opacity: 0; visibility: hidden; pointer-events: none; transition: opacity 0.2s, visibility 0.2s; }
      .glitch-overlay.active { opacity: 1; visibility: visible; pointer-events: auto; }
      .glitch-text { font-family: var(--font-ui); font-size: clamp(3rem, 10vw, 8rem); font-weight: 700; color: var(--fg); letter-spacing: 0.1em; text-transform: uppercase; }
    `;
    document.head.appendChild(style);
  }

  // Defensive visibility reset. Registered at module scope so it is guaranteed
  // to exist even if init() throws, and wired to both 'pageshow' (covers bfcache
  // restores, where event.persisted === true) and 'visibilitychange'. Clears any
  // stale inline opacity/transition a previous navigation may have left on
  // <body> and deactivates the full-screen glitch overlay. Idempotent.
  function resetVisibility() {
    try {
      if (document.body) {
        document.body.style.opacity = '1';
        document.body.style.transition = '';
      }
      const overlay = document.getElementById('glitch-overlay');
      if (overlay) overlay.classList.remove('active');
      if (glitchInstance) glitchInstance.active = false;
    } catch (e) {}
  }
  window.addEventListener('pageshow', resetVisibility);
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') resetVisibility();
  });

  // Start when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();