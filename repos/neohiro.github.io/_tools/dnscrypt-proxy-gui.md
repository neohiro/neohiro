---
name: dnscrypt-proxy-gui
stars: 29
forks: 1
open_issues: 1
pushed_at: 2026-09-18T06:23:09Z
created_at: 2025-09-11T10:22:19Z
title: dnscrypt-proxy-gui
tagline: "Cross-platform GUI for dnscrypt-proxy — encrypted DNS, anonymizing relays, exact DNS restore, tray-resident, zero telemetry"
platform: Windows / macOS / Linux
language: Python (Tkinter)
category: Privacy Tools
repo_url: https://github.com/neohiro/dnscrypt-proxy-gui
featured: true
weight: 1
icon: |
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
    <circle cx="12" cy="12" r="10"/>
    <path d="M12 6v6l4 2" stroke="var(--blue)" stroke-width="2"/>
    <path d="M8 18h8" stroke="var(--blue)" stroke-width="2"/>
    <path d="M12 14v4" stroke="var(--blue)" stroke-width="2"/>
  </svg>
---

**dnscrypt-proxy-gui** is a cross-platform desktop front-end for the official
[`dnscrypt-proxy`](https://github.com/DNSCrypt/dnscrypt-proxy) daemon. It turns a
daemon that is powerful but config-file-driven into something you can operate by
click: pick resolvers, flip DNS over, and put everything back exactly as it was.

## Features

- **Browse & sort servers** — pulls the current public DNSCrypt resolver list into a sortable table.
- **Multi-server activation** — run several resolvers at once for redundancy and speed.
- **Anonymizing relays** — route through relays for an extra anonymity layer, no config surgery.
- **Live status indicator** — ACTIVE / INACTIVE at a glance, straight from the running service.
- **Exact DNS backup & restore** — current DNS settings are captured verbatim before any change and
  restored on deactivation or exit; a crashed session is repaired on the next launch.
- **System tray integration** — minimize to the tray and run unobtrusively in the background.
- **Run at startup** — one checkbox to launch on login.
- **Visual configuration** — manage `dnscrypt-proxy.toml` from a dedicated tab.
- **Server requirements** — enforce DNSSEC, no-log and no-filter policies per server.
- **IPv6 blocking** — one click to block AAAA lookups.
- **Cache tuning** — cache size and TTL are adjustable.
- **Instant apply** — changes restart the service seamlessly, no manual reload.
- **Session persistence** — last servers and settings are remembered and can re-activate on launch.
- **Automatic privilege elevation** — requests admin/sudo only when network settings demand it.

## Install

### Standalone release (recommended)

Pre-built executables exist for Windows, macOS and Linux — no Python needed.

1. Download the archive for your OS from the
   [Releases page](https://github.com/neohiro/dnscrypt-proxy-gui/releases), e.g.
   `dnscrypt-proxy-gui-1.2.1-Windows-x64.zip`.
2. Extract it into **its own dedicated folder** — never loose into `Program Files`.
3. Fetch the official `dnscrypt-proxy` binary for your OS from the
   [DNSCrypt releases page](https://github.com/DNSCrypt/dnscrypt-proxy/releases)
   and place it in that same folder (or point at it in *Configuration → System Paths*).
4. Launch it. It asks for administrator/sudo rights only when required.

> macOS: the app is not codesigned. On first launch use right-click → **Open**, or allow it under
> *System Settings → Privacy & Security*.

### From source

Requires **Python 3.11+** and the Tk bindings for your distro:

```bash
# Debian / Ubuntu
sudo apt install python3-tk
# Fedora
sudo dnf install python3-tkinter
# Arch
sudo pacman -S tk
```

Then:

```bash
git clone https://github.com/neohiro/dnscrypt-proxy-gui.git
cd dnscrypt-proxy-gui
pip install -r requirements.txt
python dnscrypt-proxy-gui.PY
```

On Linux `dnscrypt-proxy` is usually already available from your distro
(`sudo apt install dnscrypt-proxy`); the GUI looks for `/usr/bin/dnscrypt-proxy` by default.

## Related

- [dnscrypt-proxy](https://github.com/DNSCrypt/dnscrypt-proxy) — the core daemon this wraps
- [Cripple-NetStrip](https://github.com/neohiro/Cripple-NetStrip) — network hardening + DNS sinkhole
- [linux](https://github.com/neohiro/linux) — cross-distro guide that includes DNSCrypt setup