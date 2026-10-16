const io = initReveal('.card');
document.querySelectorAll('.card').forEach(attachSelect);

/* ---- typewriter tagline ---- */
startTypewriter([
  'Security hardening & privacy tooling',
  'Exploit mitigations made simple',
  'From ExploitProtection to HoneyScan',
  'Encrypted DNS for everyone',
  'Firewalls · sinkholes · honeypots',
  'Zero telemetry. Full transparency.',
  'STIG-grade guides for fresh installs',
  'Guides, videos & community',
  '29 open-source tools and counting',
  'Defense is the best defense'
]);

/* ---- dynamic projects feed: committed snapshot first, cached API refresh ---- */
const grid = document.getElementById('projects');
const REPOS = {};
let pendingName = null, dataDone = false, liveLoaded = false, lastCardRect = null;
let shownRepo = null, lastFocus = null, missingKey = null;

function repoCard(r, i) {
  const card = el('div', 'card'); card.style.transitionDelay = (i % 3 * 70) + 'ms';
  const a = card.appendChild(el('a', 'fill')); a.href = '#/r/' + encodeURIComponent(r.name);
  a.addEventListener('click', () => { lastCardRect = card.getBoundingClientRect(); });
  const h3 = el('h3'); h3.append(el('span', null, r.name), el('span', 'stars', '★ ' + fmt(r.stargazers_count)));
  card.appendChild(h3);
  card.appendChild(el('p', null, r.description || 'No description yet.'));
  const tags = el('div', 'tags');
  [r.language].concat(r.topics || []).filter(Boolean).slice(0, 3).forEach(t => tags.appendChild(el('span', 'tag', t)));
  if (!tags.children.length) tags.appendChild(el('span', 'tag', 'repository'));
  card.appendChild(tags);
  return card;
}
function renderRepos(all) {
  grid.innerHTML = '';
  all.forEach((r, i) => {
    REPOS[r.name.toLowerCase()] = r;
    const c = repoCard(r, i); grid.appendChild(c); attachSelect(c); io.observe(c);
  });
}

/* fast path: pre-rendered snapshot ships with the site */
fetch('repos.json').then(r => r.ok ? r.json() : null).then(rows => {
  if (liveLoaded || !rows || !rows.length) return;
  renderRepos(rows); dataDone = true; if (pendingName) routeHash();
}).catch(() => {});

/* fresh path: live API via sessionStorage cache */
Promise.all([
  cachedJson('fp-org', 'https://api.github.com/orgs/frenzypenguin-media/repos?per_page=100').catch(() => []),
  cachedJson('neo-repos', 'https://api.github.com/users/neohiro/repos?per_page=100&sort=pushed').catch(() => [])
]).then(lists => {
  const seen = [], all = [];
  lists.flat().forEach(r => {
    const k = r.name.toLowerCase();
    if (seen.includes(k) || r.fork || /github\.io$/.test(r.name) || r.name === '.github') return;
    seen.push(k); all.push(r);
  });
  all.sort((a, b) => b.stargazers_count - a.stargazers_count || new Date(b.pushed_at) - new Date(a.pushed_at));
  if (!all.length) throw new Error('no repos');
  liveLoaded = true;
  renderRepos(all);
  if (missingKey && REPOS[missingKey] && location.hash.indexOf('#/r/') === 0) { missingKey = null; routeHash(); }
  dataDone = true; if (pendingName) routeHash();
}).catch(() => {
  if (!dataDone) {
    grid.innerHTML = '';
    const c = el('div', 'card'), h3 = el('h3'), p = el('p', '',
      'Live project feed is unavailable right now — browse the full toolbox instead:'), a = el('a');
    h3.textContent = 'Browse all projects'; a.href = 'https://github.com/neohiro?tab=repositories';
    a.textContent = 'github.com/neohiro'; a.style.color = 'var(--teal)'; a.style.textDecoration = 'none';
    c.append(h3, p, a); grid.appendChild(c); attachSelect(c); io.observe(c);
    dataDone = true; if (pendingName) routeHash();
  }
});

/* ---- per-repo detail view (#/r/<name>) ---- */
const overlay = document.getElementById('overlay'), panel = document.getElementById('panel'),
  pvName = document.getElementById('pv-name'), pvDesc = document.getElementById('pv-desc'),
  pvMeta = document.getElementById('pv-meta'), pvTags = document.getElementById('pv-tags'),
  pvOpen = document.getElementById('pv-open');
let shownRepo = null, lastFocus = null;

function fillPanel(r) {
  pvName.textContent = r.name;
  pvDesc.textContent = r.description || 'No description yet.';
  pvMeta.innerHTML = '';
  [['★', fmt(r.stargazers_count) + ' stars'],
   ['⑂', fmt(r.forks_count) + ' forks'],
   ['⟳', 'updated ' + new Date(r.pushed_at).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })]
  ].forEach(m => { const s = el('span'); s.append(el('b', null, m[0] + ' '), document.createTextNode(m[1])); pvMeta.appendChild(s); });
  pvTags.innerHTML = '';
  [r.language].concat(r.topics || []).filter(Boolean).slice(0, 4).forEach(t => pvTags.appendChild(el('span', 'tag', t)));
  if (!pvTags.children.length) pvTags.appendChild(el('span', 'tag', 'repository'));
  pvOpen.href = r.html_url; pvOpen.textContent = 'Open repository ↗';
}
function openDetail(r) {
  if (shownRepo === r.name) return;
  if (!shownRepo) lastFocus = document.activeElement;
  shownRepo = r.name; missingKey = null;
  const rm = matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (lastCardRect && !rm) {
    const dx = (lastCardRect.left + lastCardRect.width / 2) - innerWidth / 2;
    const dy = (lastCardRect.top + lastCardRect.height / 2) - innerHeight / 2;
    panel.style.transform = `translate(${dx}px,${dy}px) scale(.18)`;
    void panel.offsetWidth;
  }
  lastCardRect = null;
  fillPanel(r);
  document.body.classList.add('detail');
  panel.style.transform = '';
  overlay.setAttribute('aria-hidden', 'false');
  panel.focus({ preventScroll: true });
  pvName.classList.remove('glitching'); void pvName.offsetWidth; pvName.classList.add('glitching');
}
function showNotFound(name) {
  if (!shownRepo) lastFocus = document.activeElement;
  shownRepo = '__notfound__';
  pvName.textContent = name;
  pvDesc.textContent = 'This repository is not in the live feed (it may be new, a fork, or filtered out). Browse everything on GitHub instead:';
  pvMeta.innerHTML = ''; pvTags.innerHTML = '';
  pvOpen.href = 'https://github.com/neohiro?tab=repositories'; pvOpen.textContent = 'Browse repositories ↗';
  document.body.classList.add('detail'); overlay.setAttribute('aria-hidden', 'false');
  panel.focus({ preventScroll: true });
}
function closeDetail() {
  if (!shownRepo) return; shownRepo = null; lastCardRect = null; missingKey = null;
  document.body.classList.remove('detail'); overlay.setAttribute('aria-hidden', 'true');
  if (lastFocus && lastFocus.focus) { lastFocus.focus({ preventScroll: true }); lastFocus = null; }
}
function routeHash() {
  const m = location.hash.match(/^#\/r\/([^/?#]+)/);
  if (!m) { closeDetail(); return; }
  let key;
  try { key = decodeURIComponent(m[1]).toLowerCase(); }
  catch (e) { showNotFound(m[1]); return; }
  const r = REPOS[key];
  if (r) openDetail(r);
  else if (dataDone) { missingKey = key; showNotFound(key); }
  else pendingName = key;
}
window.addEventListener('hashchange', routeHash);
routeHash();
document.addEventListener('keydown', e => { if (e.key === 'Escape' && shownRepo) location.hash = '#'; });
