"""Add RoundedShell futuristic card tiles to SystemMonitor."""
P = r"repos\SystemMonitor\SystemMonitor.PY"
src = open(P, encoding="utf-8").read()

# 1) RoundedShell class right after WidgetPersistence
anchor = "class SensorTrackerApp:"
shell_cls = '''class RoundedShell(tk.Canvas):
    """Futuristic rounded card: paints the shell; widgets live in .inner."""

    PAD_X = 14
    PAD_Y = 10

    def __init__(self, master, radius=16, **kw):
        try:
            outer = master.cget("bg")
        except Exception:
            outer = "#0B0E12"
        super().__init__(master, highlightthickness=0, bd=0, bg=outer, **kw)
        self.outer_bg = outer
        self.radius = radius
        self.card_bg = "#10161D"
        self.outline = "#24313D"
        self.glow = "#18222C"
        self.inner = tk.Frame(self, bg=self.card_bg, bd=0, relief="flat",
                              highlightthickness=0)
        self.create_window(self.PAD_X, self.PAD_Y, anchor="nw", window=self.inner)
        self.inner.bind("<Configure>", lambda e: self._fit())
        self.bind("<Configure>", lambda e: self._paint())
        self._fit()
        self._paint()

    @staticmethod
    def _round_pts(x1, y1, x2, y2, r):
        r = max(2, min(r, int((x2 - x1) // 2), int((y2 - y1) // 2)))
        return [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
                x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
                x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]

    def _fit(self):
        w = self.inner.winfo_reqwidth() + 2 * self.PAD_X
        h = self.inner.winfo_reqheight() + 2 * self.PAD_Y
        if w > 4 and h > 4:
            self.configure(width=w, height=h)

    def set_palette(self, outer=None, card=None, outline=None, glow=None):
        if outer:
            self.outer_bg = outer
            self.configure(bg=outer)
        if card:
            self.card_bg = card
            self.inner.configure(bg=card)
        if outline:
            self.outline = outline
        if glow:
            self.glow = glow
        self._paint()

    def _paint(self):
        self.delete("card")
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 8 or h <= 8:
            return
        glow_pts = self._round_pts(1, 1, w - 1, h - 1, self.radius + 3)
        self.create_polygon(glow_pts, fill="", outline=self.glow, width=5,
                            smooth=True, tags=("card",))
        pts = self._round_pts(3, 3, w - 3, h - 3, self.radius)
        self.create_polygon(pts, fill=self.card_bg, outline=self.outline,
                            width=2, smooth=True, tags=("card",))
        self.tag_lower("card")


'''
src = src.replace(anchor, shell_cls + anchor, 1)

# 2) register shells dict next to sensor_frames
src = src.replace("self.sensor_frames = {}",
                  "self.sensor_frames = {}\n        self.sensor_shells = {}", 1)

# 3) group frame creation -> shell-backed
old_head = '''    def _create_sensor_group_frame(self, parent, title_text):
        frame = tk.Frame(parent, bd=0, relief="flat", highlightthickness=1, padx=8, pady=3)
'''
new_head = '''    def _create_sensor_group_frame(self, parent, title_text):
        shell = RoundedShell(parent)
        self.sensor_shells[title_text] = shell
        frame = shell.inner
'''
assert old_head in src
src = src.replace(old_head, new_head, 1)

# 4) repack uses shells
old_repack = '''        for i, device_name in enumerate(self.ordered_devices):
            if device_name in self.sensor_frames:
                frame = self.sensor_frames[device_name]
                row = i // new_columns
                column = i % new_columns
                frame.grid(row=row, column=column, padx=8, pady=8, sticky="nsew")'''
new_repack = '''        for i, device_name in enumerate(self.ordered_devices):
            if device_name in self.sensor_shells:
                shell = self.sensor_shells[device_name]
                row = i // new_columns
                column = i % new_columns
                shell.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")'''
assert old_repack in src
src = src.replace(old_repack, new_repack, 1)

# 5) theme: derive futuristic palette and push into shells
old_theme = '''        self.bg_frame = self.bg_main
'''
new_theme = '''        # Card palette: deep glass panel slightly lifted from the background
        self.bg_frame = self._mix_hex(self.bg_main, "#FFFFFF", 0.06)
        card_glow = self._mix_hex(self.accent_color, self.bg_main, 0.82)
'''
assert old_theme in src
src = src.replace(old_theme, new_theme, 1)

old_push = '''        for device_frame in self.sensor_frames.values():'''
new_push = '''        for shell in getattr(self, "sensor_shells", {}).values():
            shell.set_palette(outer=self.bg_main, card=self.bg_frame,
                              outline=self.highlight_color, glow=card_glow)

        for device_frame in self.sensor_frames.values():'''
assert old_push in src
src = src.replace(old_push, new_push, 1)

# 6) _mix_hex helper before _apply_theme
helper = '''    @staticmethod
    def _mix_hex(hex_color, other, t):
        """Blend two hex colours; t = share of `other`."""
        def ch(c):
            c = c.lstrip("#")
            return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
        r1, g1, b1 = ch(hex_color)
        r2, g2, b2 = ch(other)
        mix = lambda a, b: max(0, min(255, int(a + (b - a) * t)))
        return "#{:02X}{:02X}{:02X}".format(mix(r1, r2), mix(g1, g2), mix(b1, b2))

    def _apply_theme(self):'''
src = src.replace("    def _apply_theme(self):", helper, 1)

open(P, "w", encoding="utf-8", newline="").write(src)

import ast
ast.parse(open(P, encoding="utf-8").read())
print("RoundedShell integrated; syntax OK")
