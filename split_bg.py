"""Split monolithic BlackGlass.py into the blackglass package."""
import os, io

SRC = r"repos\BlackGlass\BlackGlass.py"
OUT = r"repos\BlackGlass"
PKG = os.path.join(OUT, "blackglass")
UI = os.path.join(PKG, "ui")

src = open(SRC, encoding="utf-8").read()
lines = src.splitlines(keepends=True)

def slice_lines(ranges):
    return "".join("".join(lines[a-1:b]) for a, b in ranges)

# (path, [(start,end)...], extra_header_lines_after_docstring)
MODULES = [
    ("lltypes.py", [(74, 245), (407, 432)],
     ["import struct", "", ""]),
    ("codec.py", [(246, 405), (476, 488)],
     ["import struct", "",
      "from .lltypes import (IPAddr, IPPort, LLUUID, fixed, null, quaternion,",
      "                      variable, vector3, vector3d, vector4)", "", ""]),
    ("messages.py", [(490, 1011)],
     ["import struct", "",
      "from .codec import baseTypes, typeLengths, llDecodeType, llEncodeType", "", ""]),
    ("packet.py", [(1019, 1161)],
     ["import struct", "",
      "from .codec import zerocode_decode, zerocode_encode",
      "from .messages import getMessageByID", "", ""]),
    ("network.py", [(433, 475), (1166, 1992), (1994, 2079)],
     ["import socket", "import threading", "import time", "import hashlib",
      "import xmlrpc.client",
      "from uuid import UUID, getnode as get_mac", "",
      "from .codec import packetErrorTrace",
      "from .lltypes import LLUUID, quaternion, variable, vector3",
      "from .messages import getMessageByName",
      "from .packet import Packet", "", ""]),
    ("agent.py", [(2081, 3661)],
     ["import threading", "import time", "import sys", "",
      "from .imaging import PIL_AVAILABLE",
      "from .lltypes import LLUUID, const, variable",
      "from .messages import getMessageByName",
      "from .network import (RegionClient, SL_USER_AGENT, login_to_simulator,",
      "                      parse_llsd_xml, render_llsd_xml, safe_decode_llvariable)",
      "", ""]),
    ("credentials.py", [(3667, 3745)],
     ["import base64", "import json", "import os", "", ""]),
    (os.path.join("ui", "widgets.py"), [(40, 72)],
     ["import tkinter as tk", "from tkinter import scrolledtext", "", ""]),
    (os.path.join("ui", "theme.py"), [(3752, 4439)],
     ["import os", "import urllib.request",
      "import tkinter as tk",
      "from tkinter import Toplevel, ttk",
      "from io import BytesIO", "",
      "from ..imaging import PIL_AVAILABLE, Image, ImageTk",
      "from ..network import SL_USER_AGENT", "", ""]),
    (os.path.join("ui", "minimap.py"), [(4441, 4661)],
     ["import math", "import time",
      "import tkinter as tk", "from tkinter import ttk", "",
      "from ..imaging import PIL_AVAILABLE, Image, ImageTk",
      "from ..lltypes import vector3", "", ""]),
    (os.path.join("ui", "chat.py"), [(4663, 5891)],
     ["import re", "import time", "import html as html_parser", "import urllib.request",
      "import tkinter as tk",
      "from tkinter import ttk",
      "from io import BytesIO", "",
      "from ..imaging import PIL_AVAILABLE, Image, ImageTk",
      "from .minimap import MinimapCanvas",
      "from .theme import (ThemedAskString, ThemedChoiceDialog, ThemedGroupDialog,",
      "                    ThemedMessageBox, ThemedParcelDialog, ThemedProfileDialog)",
      "from .widgets import LimitedScrolledText", "", ""]),
    (os.path.join("ui", "login.py"), [(5894, 6092)],
     ["import tkinter as tk", "from tkinter import ttk", "",
      "from ..credentials import load_credentials, save_credentials", "", ""]),
    (os.path.join("ui", "app.py"), [(6096, 6330)],
     ["import os",
      "import tkinter as tk", "from tkinter import ttk", "",
      "from ..agent import SecondLifeAgent",
      "from ..credentials import CREDENTIALS_FILE",
      "from .chat import ChatTab",
      "from .login import LoginPanel",
      "from .theme import ThemedMessageBox", "", ""]),
]

DOCS = {
    "lltypes.py": "Core Second Life wire-format data types.",
    "codec.py": "Encoding/decoding utilities: typed values, zerocoding, hex dumps.",
    "messages.py": "Second Life UDP message templates and the message registry.",
    "packet.py": "Low-level UDP packet framing (acking, zerocoding, reliability).",
    "network.py": "Authentication, LLSD helpers and the RegionClient circuit layer.",
    "agent.py": "SecondLifeAgent: high-level agent behaviour driving a region session.",
    "credentials.py": "Local credential storage (XOR-obfuscated profile file).",
}

os.makedirs(UI, exist_ok=True)

written = []
for rel, ranges, extra in MODULES:
    path = os.path.join(PKG, rel)
    body = slice_lines(ranges)
    name = os.path.basename(rel)
    header = [
        '"""{}"""'.format(DOCS.get(name, "")),
        "",
    ] + extra
    content = "\n".join(header) + "\n" + body
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    written.append((rel, len(body.splitlines())))

# imaging.py - optional Pillow support flag shared across UI + agent
with open(os.path.join(PKG, "imaging.py"), "w", encoding="utf-8") as f:
    f.write('''"""Optional Pillow support. Map/avatar imagery degrades gracefully without it."""
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    Image = None
    ImageTk = None
    PIL_AVAILABLE = False
    print("Warning: Pillow (PIL) not found. Map tiles will display a colored placeholder.")
''')

# package __init__
with open(os.path.join(PKG, "__init__.py"), "w", encoding="utf-8") as f:
    f.write('''"""BlackGlass - multi-client chat viewer for Second Life.

The implementation is organised as:

- ``lltypes`` / ``codec`` / ``messages`` / ``packet`` : protocol stack
- ``network``   : login, circuits and LLSD helpers
- ``agent``     : high-level SecondLifeAgent
- ``credentials``: local credential storage
- ``ui``        : themed widgets, chat tabs, login panel and the main app
"""

__version__ = "1.5"
''')

with open(os.path.join(UI, "__init__.py"), "w", encoding="utf-8") as f:
    f.write('"""User interface layer for BlackGlass."""\n')

# thin launcher replacing the monolith
launcher = '''#!/usr/bin/env python3
"""BlackGlass - multi-client chat viewer for Second Life.

This file is a thin launcher; the implementation lives in the
``blackglass`` package (see its __init__.py for a module map).
"""
from blackglass.app import main

if __name__ == "__main__":
    main()
'''
open(os.path.join(OUT, "BlackGlass.py.new"), "w", encoding="utf-8", newline="").write(launcher)

# reconciliation: every original non-blank line must appear in some slice
covered = set()
for rel, ranges, extra in MODULES:
    for a, b in ranges:
        for i in range(a, b + 1):
            covered.add(i)
lost = [i for i in range(1, len(lines) + 1)
        if i not in covered and lines[i-1].strip()]
print(f"Wrote {len(written)+4} files")
print(f"Original lines: {len(lines)}; covered: {len(covered)}; lost NON-BLANK: {len(lost)}")
for i in lost[:20]:
    print(f"  LOST {i}: {lines[i-1].rstrip()[:90]}")
