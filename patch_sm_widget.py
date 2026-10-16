"""Replace top-most widget behaviour with true desktop-level embedding."""
import io, re

P = r"repos\SystemMonitor\SystemMonitor.PY"
src = open(P, encoding="utf-8").read()

start = src.index("class WidgetPersistence:")
end = src.index("class SensorTrackerApp:")
new_class = '''class WidgetPersistence:
    """Desktop-level widget placement that persists everywhere.

    The monitor lives ON THE DESKTOP LAYER - never on top of other windows:

    - Windows: embedded into the shell's WorkerW layer (the same trick
      Rainmeter uses), i.e. between the wallpaper and everything else.
      Survives Show Desktop (Win+D), Win+M and virtual-desktop switches;
      Explorer restarts are detected and re-embedded automatically.
    - Linux/X11: _NET_WM_WINDOW_TYPE_DESKTOP where supported, otherwise
      sticky + below + skip-taskbar via wmctrl.
    - macOS: normal (non-floating) window kept off the taskbar queue as far
      as Tk allows; joining all Spaces needs PyObjC (best-effort only).
    """

    POLL_MS = 1500

    def __init__(self, root):
        self.root = root
        self.enabled = False
        self._job = None
        self._hwnd = None
        self._workerw = None

    # ---- public API ----------------------------------------------------
    def enable(self):
        if self.enabled:
            return True
        self.enabled = True
        try:
            self.root.attributes("-topmost", False)
        except Exception:
            pass
        self._apply_platform_style()
        self._poll()
        return True

    def disable(self):
        if not self.enabled:
            return False
        self.enabled = False
        if self._job:
            try:
                self.root.after_cancel(self._job)
            except Exception:
                pass
            self._job = None
        self._restore_platform_style()
        return False

    def toggle(self):
        return self.disable() if self.enabled else self.enable()

    # ---- Windows desktop embedding --------------------------------------
    @staticmethod
    def _find_desktop_workerw():
        """Return the WorkerW handle that hosts the wallpaper (behind icons)."""
        import ctypes
        user32 = ctypes.windll.user32
        progman = user32.FindWindowW("Progman", None)
        if not progman:
            return None
        # Ask the shell to spawn the wallpaper WorkerW layer (0x052C)
        user32.SendMessageTimeoutW(progman, 0x052C, 0, None, 0, 1000, None)

        def enum_cb(hwnd, lparam):
            nonlocal defview_host
            # A WorkerW hosting SHELLDLL_DefView marks the icon layer;
            # the *next* WorkerW sibling is the wallpaper host we want.
            if user32.FindWindowExW(hwnd, None, "SHELLDLL_DefView", None):
                defview_host = hwnd
            return True

        CMPFUNC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        defview_host = None
        cb = CMPFUNC(enum_cb)
        user32.EnumWindows(cb, 0)
        if defview_host:
            workerw = user32.FindWindowExW(None, defview_host, "WorkerW", None)
            if workerw:
                return workerw
        return progman  # fallback: parent to Progman itself

    # ---- platform styling ------------------------------------------------
    def _apply_platform_style(self):
        if sys.platform == "win32":
            try:
                import ctypes
                user32 = ctypes.windll.user32
                hwnd = user32.GetParent(self.root.winfo_id()) or self.root.winfo_id()
                GWL_EXSTYLE = -20
                WS_EX_TOOLWINDOW = 0x00000080
                WS_EX_NOACTIVATE = 0x08000000
                style = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
                user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE,
                                         style | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE)
                self._hwnd = hwnd
                workerw = self._find_desktop_workerw()
                if workerw:
                    x, y = self.root.winfo_rootx(), self.root.winfo_rooty()
                    w = max(self.root.winfo_width(), 1)
                    h = max(self.root.winfo_height(), 1)
                    if user32.SetParent(hwnd, workerw):
                        self._workerw = workerw
                        user32.MoveWindow(hwnd, x, y, w, h, True)
            except Exception:
                pass
        elif sys.platform.startswith("linux"):
            try:
                # Desktop type = behind windows, part of the workspace itself.
                self.root.attributes("-type", "desktop")
            except Exception:
                pass
            try:
                import shutil
                if shutil.which("wmctrl"):
                    subprocess.Popen(
                        ["wmctrl", "-i", "-r", hex(self.root.winfo_id()),
                         "-b", "add,sticky,below,skip_taskbar"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        else:  # macOS: plain window; desktop-layer needs PyObjC (optional)
            pass

    def _restore_platform_style(self):
        if sys.platform == "win32":
            try:
                import ctypes
                user32 = ctypes.windll.user32
                if self._hwnd:
                    if self._workerw:
                        user32.SetParent(self._hwnd, None)
                    GWL_EXSTYLE = -20
                    WS_EX_TOOLWINDOW = 0x00000080
                    WS_EX_NOACTIVATE = 0x08000000
                    style = user32.GetWindowLongPtrW(self._hwnd, GWL_EXSTYLE)
                    user32.SetWindowLongPtrW(self._hwnd, GWL_EXSTYLE,
                                             style & ~(WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE))
            except Exception:
                pass
            self._hwnd = None
            self._workerw = None

    # ---- health poll -------------------------------------------------------
    def _poll(self):
        if not self.enabled:
            return
        try:
            if sys.platform == "win32" and self._hwnd:
                import ctypes
                user32 = ctypes.windll.user32
                expected = self._workerw
                # Re-embed after an Explorer restart lost our parent
                if expected and user32.GetParent(self._hwnd) != expected:
                    workerw = self._find_desktop_workerw()
                    if workerw:
                        user32.SetParent(self._hwnd, workerw)
                        self._workerw = workerw
                if user32.IsIconic(self._hwnd) or not user32.IsWindowVisible(self._hwnd):
                    SW_SHOWNOACTIVATE = 4
                    SWP_NOSIZE = 0x1; SWP_NOMOVE = 0x2
                    SWP_NOACTIVATE = 0x10; SWP_SHOWWINDOW = 0x40
                    HWND_BOTTOM = 1
                    user32.ShowWindow(self._hwnd, SW_SHOWNOACTIVATE)
                    user32.SetWindowPos(self._hwnd, HWND_BOTTOM, 0, 0, 0, 0,
                                        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW)
            state = ""
            try:
                state = self.root.state()
            except Exception:
                pass
            if state in ("iconic", "icon", "withdrawn"):
                self.root.deiconify()
                self.root.lower()
        except Exception:
            pass
        self._job = self.root.after(self.POLL_MS, self._poll)


'''

src = src[:start] + new_class + src[end:]
open(P, "w", encoding="utf-8", newline="").write(src)

import ast
ast.parse(open(P, encoding="utf-8").read())
print("WidgetPersistence replaced; syntax OK")
