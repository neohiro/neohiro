"""credentials.py: Windows DPAPI whole-file protection; app.py: Lists tab wiring."""
import ast

def patch(path, pairs):
    src = open(path, encoding="utf-8").read()
    changed = False
    for old, new in pairs:
        if old in src:
            src = src.replace(old, new, 1)
            changed = True
        elif new in src:
            continue
        else:
            raise AssertionError(f"anchor missing in {path}:\n{old[:140]}")
    open(path, "w", encoding="utf-8", newline="").write(src)
    ast.parse(open(path, encoding="utf-8").read())
    print(f"patched OK: {path} (changed={changed})")

# ================================================== credentials.py — DPAPI
patch(r"repos\BlackGlass\blackglass\credentials.py", [
    ('''"""Local credential storage (XOR-obfuscated profile file)."""

import base64
import json
import os


_SECRET_KEY = b"sl_chat_key_v1"
CREDENTIALS_FILE = "sl_credentials.json"
''',
     '''"""Local credential storage.

On Windows the entire credential JSON is additionally sealed with DPAPI
(CryptProtectData, user scope) - the strongest storage available without
extra dependencies. Other platforms use per-password XOR obfuscation.
Files written by older versions are upgraded automatically on load.
"""

import base64
import json
import os
import sys


_SECRET_KEY = b"sl_chat_key_v1"
CREDENTIALS_FILE = "sl_credentials.json"
_DPAPI_MAGIC = b"DPAPI1:"


def _dpapi_protect(data):
    """Seal *data* (bytes) with CryptProtectData; returns DPAPI1:-prefixed blob."""
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD),
                    ("pbData", ctypes.POINTER(ctypes.c_char))]

    buf = ctypes.create_string_buffer(data, len(data))
    bin_blob = DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    out = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(bin_blob), None, None, None, None, 0, ctypes.byref(out)):
        raise OSError("CryptProtectData failed")
    try:
        sealed = ctypes.string_at(out.pbData, out.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(out.pbData)
    return _DPAPI_MAGIC + base64.b64encode(sealed)


def _dpapi_unprotect(blob):
    """Open a DPAPI1:-prefixed blob; returns original bytes."""
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD),
                    ("pbData", ctypes.POINTER(ctypes.c_char))]

    raw = base64.b64decode(blob[len(_DPAPI_MAGIC):])
    buf = ctypes.create_string_buffer(raw, len(raw))
    bin_blob = DATA_BLOB(len(raw), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    out = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(bin_blob), None, None, None, None, 0, ctypes.byref(out)):
        raise OSError("CryptUnprotectData failed")
    try:
        return ctypes.string_at(out.pbData, out.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(out.pbData)
'''),
    # save: seal on Windows + restrictive permissions elsewhere
    ('''        data.append(new_entry)

        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump(data, f, indent=4)
            
        return True''',
     '''        data.append(new_entry)

        payload = json.dumps(data, indent=4).encode("utf-8")
        if sys.platform == "win32":
            payload = _dpapi_protect(payload)

        with open(CREDENTIALS_FILE, "wb") as f:
            f.write(payload)
        if os.name == "posix":
            try:
                os.chmod(CREDENTIALS_FILE, 0o600)
            except Exception:
                pass

        return True'''),
    # load: transparently read both formats
    ('''    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            data = json.load(f)''',
     '''    try:
        with open(CREDENTIALS_FILE, "rb") as f:
            raw = f.read()
        if raw.startswith(_DPAPI_MAGIC):
            data = json.loads(_dpapi_unprotect(raw).decode("utf-8"))
        else:
            data = json.loads(raw.decode("utf-8"))'''),
])

# ================================================== app.py — Lists tab
patch(r"repos\BlackGlass\blackglass\ui\app.py", [
    ('''from .chat import ChatTab
from .login import LoginPanel
from .theme import ThemedMessageBox''',
     '''from .chat import ChatTab
from .lists import ListsTab
from .login import LoginPanel
from .theme import ThemedMessageBox'''),
    ('''        chat_tab = ChatTab(self.notebook, agent, first, last, self)
        tab_name = f"{first} {last}".replace(" Resident", "")
        
        # 2. Add to notebook and select it
        self.notebook.add(chat_tab, text=tab_name)
        self.notebook.select(chat_tab)''',
     '''        chat_tab = ChatTab(self.notebook, agent, first, last, self)
        tab_name = f"{first} {last}".replace(" Resident", "")
        
        # 2. Add to notebook and select it (+ per-user Lists tab)
        self.notebook.add(chat_tab, text=tab_name)
        lists_tab = ListsTab(self.notebook, chat_tab, self)
        self.notebook.insert(chat_tab, lists_tab, text=f"\u2637 {tab_name}")
        chat_tab.lists_tab = lists_tab
        self.notebook.select(chat_tab)'''),
    ('''        if full_name in self.active_agents:
            # The agent is already stopped by the ChatTab.on_closing logic, 
            # but ensure it's removed from the dictionary.
            del self.active_agents[full_name]
            self.notebook.forget(chat_tab_instance)''',
     '''        if full_name in self.active_agents:
            # The agent is already stopped by the ChatTab.on_closing logic, 
            # but ensure it's removed from the dictionary.
            del self.active_agents[full_name]
            lists_tab = getattr(chat_tab_instance, "lists_tab", None)
            if lists_tab is not None:
                try:
                    lists_tab.cancel_refresh()
                except Exception:
                    pass
                try:
                    self.notebook.forget(lists_tab)
                    lists_tab.destroy()
                except Exception:
                    pass
            self.notebook.forget(chat_tab_instance)'''),
])
print("ALL PATCHES APPLIED")
