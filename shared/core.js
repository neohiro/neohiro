/* Shared site core - SINGLE SOURCE OF TRUTH.
   Edits belong HERE; build-sites.ps1 injects this into each index.html
   between __CORE_START__/__CORE_END__ markers. Never edit injected copies. */

// ---- Configuration constants ----
const CONFIG = {
  REVEAL_THRESHOLD: 0.12,
  REVEAL_DELAY_STAGGER: 70,
  REVEAL_DELAY_CLEAR_MS: 800,
  RIPPLE_SCALE_FACTOR: 2.3,
  SELECT_FLASH_DURATION: 650,
  GLITCH_DURATION: 420,
  RANDOM_GLITCH_BASE_MS: 2600,
  RANDOM_GLITCH_VARIANCE_MS: 3400,
  TYPEWRITER_CHAR_MIN_MS: 16,
  TYPEWRITER_CHAR_MAX_MS: 34,
  TYPEWRITER_HOLD_MS: 1500,
  TYPEWRITER_ERASE_MIN_MS: 8,
  TYPEWRITER_ERASE_MAX_MS: 14,
  TYPEWRITER_NEXT_DELAY_MS: 260
};

// ---- fetch helper (no client-side cache) ----
function fetchJson(url) {
  if (!url || typeof url !== 'string') {
    return Promise.reject(new Error('fetchJson: invalid url'));
  }
  return fetch(url).then(r => {
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  });
}

// ---- tiny DOM + number helpers ----
const fmt = n => {
  if (typeof n !== 'number' || !isFinite(n)) return '0';
  return n >= 1000 ? (n / 1000).toFixed(1).replace(/\.0$/, '') + 'k' : String(n);
};

const el = (tag, className, text) => {
  const n = document.createElement(tag);
  if (className) n.className = className;
  if (text != null) n.textContent = text;
  return n;
};

// ---- reveal-on-scroll with stagger (clears delay after entry so hover feels instant) ----
function initReveal(selector) {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('in');
        observer.unobserve(entry.target);
        const target = entry.target;
        setTimeout(() => { target.style.transitionDelay = ''; }, CONFIG.REVEAL_DELAY_CLEAR_MS);
      }
    });
  }, { threshold: CONFIG.REVEAL_THRESHOLD });

  const elements = document.querySelectorAll(selector);
  elements.forEach((elm, i) => {
    elm.style.transitionDelay = (i % 3 * CONFIG.REVEAL_DELAY_STAGGER) + 'ms';
    observer.observe(elm);
  });

  return { observer, disconnect: () => observer.disconnect() };
}

// ---- repo select burst: ripple + glitch flash ----
function attachSelect(card) {
  card.addEventListener('pointerdown', e => {
    const rect = card.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height) * CONFIG.RIPPLE_SCALE_FACTOR;
    const ripple = document.createElement('span');
    ripple.className = 'ripple';
    ripple.style.cssText = `width:${size}px;height:${size}px;left:${e.clientX - rect.left}px;top:${e.clientY - rect.top}px`;
    card.appendChild(ripple);
    setTimeout(() => ripple.remove(), 800);

    if (card._selTimer) clearTimeout(card._selTimer);
    card.classList.remove('selected');
    void card.offsetWidth;
    card.classList.add('selected');
    card._selTimer = setTimeout(() => card.classList.remove('selected'), CONFIG.SELECT_FLASH_DURATION);
  });
}

// ---- glitching logo + typewriter tagline ----
let glitchTimer = null;
let randGlitchTimer = null;

function glitchLogo(logoEl) {
  if (!logoEl) return;
  if (glitchTimer) clearTimeout(glitchTimer);
  logoEl.classList.remove('glitching');
  void logoEl.offsetWidth;
  logoEl.classList.add('glitching');
  glitchTimer = setTimeout(() => logoEl.classList.remove('glitching'), CONFIG.GLITCH_DURATION);
}

function startTypewriter(typedEl, phrases, logoEl) {
  if (!typedEl || !phrases?.length) return;

  let phraseIndex = 0;

  function typePhrase(text, charIndex) {
    typedEl.textContent = text.slice(0, charIndex);
    if (charIndex < text.length) {
      const delay = CONFIG.TYPEWRITER_CHAR_MIN_MS + Math.random() * (CONFIG.TYPEWRITER_CHAR_MAX_MS - CONFIG.TYPEWRITER_CHAR_MIN_MS);
      setTimeout(() => typePhrase(text, charIndex + 1), delay);
    } else {
      setTimeout(() => {
        glitchLogo(logoEl);
        erasePhrase(text, text.length);
      }, CONFIG.TYPEWRITER_HOLD_MS);
    }
  }

  function erasePhrase(text, charIndex) {
    typedEl.textContent = text.slice(0, charIndex);
    if (charIndex > 0) {
      const delay = CONFIG.TYPEWRITER_ERASE_MIN_MS + Math.random() * (CONFIG.TYPEWRITER_ERASE_MAX_MS - CONFIG.TYPEWRITER_ERASE_MIN_MS);
      setTimeout(() => erasePhrase(text, charIndex - 1), delay);
    } else {
      phraseIndex = (phraseIndex + 1) % phrases.length;
      setTimeout(() => typePhrase(phrases[phraseIndex], 0), CONFIG.TYPEWRITER_NEXT_DELAY_MS);
    }
  }

  typePhrase(phrases[0], 0);
}

function startRandomGlitch(logoEl) {
  if (!logoEl) return;
  function tick() {
    glitchLogo(logoEl);
    randGlitchTimer = setTimeout(tick, CONFIG.RANDOM_GLITCH_BASE_MS + Math.random() * CONFIG.RANDOM_GLITCH_VARIANCE_MS);
  }
  tick();
}

function cleanupCore(observers = []) {
  if (glitchTimer) clearTimeout(glitchTimer);
  if (randGlitchTimer) clearTimeout(randGlitchTimer);
  glitchTimer = null;
  randGlitchTimer = null;
  observers.forEach(obs => {
    if (obs && typeof obs.disconnect === 'function') obs.disconnect();
  });
}

// Expose for page-level cleanup if needed
window.__neohiroCoreCleanup = cleanupCore;