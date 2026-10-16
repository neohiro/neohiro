"""Comprehensive BlackGlass patch: modals, teleport links, leaks, DPAPI, Lists tab."""
import ast

def patch(path, pairs, must=True):
    src = open(path, encoding="utf-8").read()
    changed = False
    for old, new in pairs:
        if old in src:
            src = src.replace(old, new, 1)
            changed = True
        elif new in src:
            continue  # already applied by a previous run
        elif must:
            raise AssertionError(f"anchor missing in {path}:\n{old[:120]}")
    open(path, "w", encoding="utf-8", newline="").write(src)
    ast.parse(open(path, encoding="utf-8").read())
    print(f"patched OK: {path} (changed={changed})")

# ============================================================ ui/theme.py
patch(r"repos\BlackGlass\blackglass\ui\theme.py", [
    # parcel modal: in-session teleport with automatic relog failover
    ('''            self.chat_tab.sl_agent.hard_teleport(r, x, y, z)
            self.on_close()''',
     '''            self.chat_tab.sl_agent.soft_teleport(r, x, y, z)
            self.on_close()'''),
    # cross-platform link opening (os.startfile is Windows-only)
    ("txt.tag_bind(tag_name, '<Button-1>', lambda e, u=link_url: os.startfile(u))",
     "txt.tag_bind(tag_name, '<Button-1>', lambda e, u=link_url: __import__('webbrowser').open(u))"),
    ('link.bind("<Button-1>", lambda e: os.startfile(url))',
     'link.bind("<Button-1>", lambda e: __import__(\'webbrowser\').open(url))'),
])

# ============================================================ agent.py
src = open(r"repos\BlackGlass\blackglass\agent.py", encoding="utf-8").read()

bounded = '''class BoundedDict(dict):
    """FIFO-bounded dict used for long-running session caches.

    Long sessions previously grew these dictionaries without limit; entries
    are evicted oldest-first once *maxsize* is exceeded.
    """
    def __init__(self, maxsize=2000):
        super().__init__()
        self._max = maxsize

    def __setitem__(self, key, value):
        if len(self) >= self._max and key not in self:
            try:
                self.pop(next(iter(self)))
            except Exception:
                pass
        dict.__setitem__(self, key, value)


'''
anchor = "class SecondLifeAgent:"
assert anchor in src
src = src.replace(anchor, bounded + anchor, 1)

cache_swaps = [
    ("        self.display_name_cache = {} # UUID -> DisplayName",
     "        self.display_name_cache = BoundedDict(2000) # UUID -> DisplayName"),
    ("        self.username_cache = {}     # UUID -> Username (e.g. 'sarahlionheart')",
     "        self.username_cache = BoundedDict(2000)   # UUID -> Username (e.g. 'sarahlionheart')"),
    ("        self.group_name_cache = {}   # UUID -> group name string",
     "        self.group_name_cache = BoundedDict(1000)  # UUID -> group name string"),
    ("        self.group_data_cache = {}   # UUID -> full group data dict",
     "        self.group_data_cache = BoundedDict(500)   # UUID -> full group data dict"),
    ("        self.parcel_name_cache = {}   # UUID -> parcel name string",
     "        self.parcel_name_cache = BoundedDict(1000) # UUID -> parcel name string"),
    ("        self.parcel_data_cache = {}  # UUID -> full parcel data dict",
     "        self.parcel_data_cache = BoundedDict(500)  # UUID -> full parcel data dict"),
]
for old, new in cache_swaps:
    assert old in src, old
    src = src.replace(old, new, 1)

# periodic hygiene sweep inside the event loop (inserted before reliable resend block)
old_loop = '''            # --- Resend Reliable Packets ---
            if self.client.handshake_complete:'''
new_loop = '''            # --- Periodic cache hygiene (long-session memory control) -------
            if current_time - getattr(self, "_last_cache_sweep", 0) > 60.0:
                self._last_cache_sweep = current_time
                try:
                    if self.client:
                        ta = self.client.tracked_avatars
                        now_ts = time.time()
                        stale = [u for u, info in list(ta.items())
                                 if now_ts - info.get("last_seen", 0) > 900]
                        for u in stale:
                            ta.pop(u, None)
                        if len(ta) > 500:  # hard cap: drop oldest sightings
                            for u in sorted(ta, key=lambda k: ta[k].get("last_seen", 0))[:len(ta) - 500]:
                                ta.pop(u, None)
                except Exception:
                    pass
                for fetch_set in (self.fetching_names, self.pending_profile_fetches,
                                  getattr(self, "fetching_groups", set()),
                                  getattr(self, "fetching_parcels", set())):
                    if len(fetch_set) > 800:
                        fetch_set.clear()

            # --- Resend Reliable Packets ---
            if self.client.handshake_complete:'''
assert old_loop in src
src = src.replace(old_loop, new_loop, 1)

# deterministic prune instead of random sampling
old_prune = '''            if len(self.client.reliable_packets) > 0:
                 # Check periodically (every 5 seconds roughly, based on iteration count or just random)
                 if random.random() < 0.05: 
                     cutoff = current_time - 60.0'''
new_prune = '''            if len(self.client.reliable_packets) > 0:
                 if current_time - getattr(self, "_last_packet_prune", 0) > 10.0:
                     self._last_packet_prune = current_time
                     cutoff = current_time - 60.0'''
assert old_prune in src
src = src.replace(old_prune, new_prune, 1)

open(r"repos\BlackGlass\blackglass\agent.py", "w", encoding="utf-8", newline="").write(src)
ast.parse(open(r"repos\BlackGlass\blackglass\agent.py", encoding="utf-8").read())
print("patched OK: agent.py")

# ============================================================ ui/chat.py — clickable teleport links
patch(r"repos\BlackGlass\blackglass\ui\chat.py", [
    # add TP regex next to URL regex
    ("    _SENTINEL_RE = re.compile(r'\\x02R:(agent|group|parcel):([0-9a-f\\-]{36})\\x03')",
     "    _SENTINEL_RE = re.compile(r'\\x02R:(agent|group|parcel):([0-9a-f\\-]{36})\\x03')\n"
     "    _TP_RE = re.compile(r'\\[Teleport to:\\s*([^\\]]+)\\]', re.I)"),
])
src = open(r"repos\BlackGlass\blackglass\ui\chat.py", encoding="utf-8").read()
old_insert = '''        segments = self._URL_RE.split(chunk)
        urls = self._URL_RE.findall(chunk)

        for idx, seg in enumerate(segments):
            if seg:
                self.chat_display.insert(tk.END, seg, base_tags)
            if idx < len(urls):'''
new_insert = '''        # Teleport spans first so their text is not treated as plain content
        tp_parts = self._TP_RE.split(chunk)
        if len(tp_parts) > 1:
            i = 0
            while i < len(tp_parts):
                if tp_parts[i]:
                    self._insert_chunk_with_links_plain(tp_parts[i], base_tags)
                i += 1
                if i < len(tp_parts):
                    self._insert_teleport_span(tp_parts[i], base_tags)
                    i += 1
            return
        self._insert_chunk_with_links_plain(chunk, base_tags)

    def _insert_teleport_span(self, spec, base_tags):
        """Render '[Teleport to: Region (X/Y/Z)]' as a clickable in-session TP."""
        spec = spec.strip()
        m = re.match(r"^(.*?)\\s*\\((\\d+)[/,]\\s*(\\d+)[/,]\\s*(\\d+)\\)$", spec)
        if m:
            region = m.group(1).strip()
            coords = tuple(int(m.group(n)) for n in (2, 3, 4))
        else:
            region, coords = spec, (128, 128, 25)
        self._link_counter += 1
        tag = f'tplink_{self._link_counter}'
        self.chat_display.tag_config(tag, foreground='#00FFAA', underline=True)
        self.chat_display.tag_bind(
            tag, '<Button-1>',
            lambda e, r=region, c=coords: self._click_teleport(r, c))
        self.chat_display.tag_bind(tag, '<Enter>',
                                    lambda e: self.chat_display.config(cursor='hand2'))
        self.chat_display.tag_bind(tag, '<Leave>',
                                   lambda e: self.chat_display.config(cursor=''))
        self.chat_display.insert(tk.END, f"[Teleport to: {spec}]",
                                 (tag, 'hyperlink') + base_tags)

    def _click_teleport(self, region, coords):
        def worker():
            try:
                self.sl_agent.soft_teleport(region, *coords)
            except Exception as exc:
                self.update_ui("notification", f"[ERROR] Teleport failed: {exc}")
        threading.Thread(target=worker, daemon=True).start()

    def _insert_chunk_with_links_plain(self, chunk, base_tags):
        segments = self._URL_RE.split(chunk)
        urls = self._URL_RE.findall(chunk)

        for idx, seg in enumerate(segments):
            if seg:
                self.chat_display.insert(tk.END, seg, base_tags)
            if idx < len(urls):'''
assert old_insert in src
src = src.replace(old_insert, new_insert, 1)
open(r"repos\BlackGlass\blackglass\ui\chat.py", "w", encoding="utf-8", newline="").write(src)
ast.parse(open(r"repos\BlackGlass\blackglass\ui\chat.py", encoding="utf-8").read())
print("patched OK: chat.py")

print("ALL PATCHES APPLIED")
