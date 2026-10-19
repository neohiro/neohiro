---
stars: 0
forks: 0
open_issues: 0
pushed_at: 2026-09-18T05:05:33Z
created_at: 2025-08-10T17:16:47Z
title: LANScan
tagline: "Local-only inventory of every device on your LAN, every USB device, every driver - live dashboard, zero telemetry"
platform: Windows / Linux / macOS
language: Python
category: Network Security
repo_url: https://github.com/neohiro/LANScan
demo_url: https://neohiro.github.io/lanscan/
featured: true
weight: 2
icon: |
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
    <circle cx="12" cy="12" r="2.4" stroke="var(--accent-strong)" stroke-width="1.8"/>
    <circle cx="12" cy="12" r="6.4" stroke="var(--accent-strong)" stroke-width="1.4" opacity=".7"/>
    <circle cx="12" cy="12" r="10.4" stroke="var(--accent-strong)" stroke-width="1.2" opacity=".4"/>
  </svg>
---

**LANScan** maps your network, your USB bus and your driver table, then renders
it as one live dashboard that never leaves your machine.

<div class="tool-links">
  <a href="https://neohiro.github.io/lanscan/" class="tool-link tool-link-secondary" target="_blank" rel="noopener">Open the live dashboard</a>
  <a href="https://github.com/neohiro/LANScan/releases/latest" class="tool-link tool-link-secondary" target="_blank" rel="noopener">Download the app</a>
</div>

The dashboard is a browser view; the scanner is a native service. The page cannot
send ARP or ICMP itself, so it needs the standalone build running on the host
you want to inspect. **Releases:** Windows · macOS · Linux, no Python needed.

This is also the canonical home of the dashboard's source. It used to live in a
separate `neohiro/lanscan.github.io` repository, which existed only to hold it
before the path `/lanscan/` was available on this site; that repository is
retired. GitHub serves a repo named `<name>.github.io` from
`<owner>.github.io/<name>.github.io/`, so it could never have served `/lanscan/`
in the first place — and two copies of a live dashboard is two that drift.

## The dashboard

**<https://neohiro.github.io/lanscan/>**

Ordered by how you actually troubleshoot, broadest blast radius first:

| # | Section | What it answers |
|---|---------|-----------------|
| 1 | **LAN devices** | who is on the network, who is the gateway, who just appeared |
| 2 | **USB devices** | ports, IDs, serials, link speed, bound driver |
| 3 | **Drivers & system drivers** | version, provider, date, signature state |
| 4 | **Host & system resources** | CPU, memory, disks, throughput, uptime |
| 5 | **Tests ran** | every probe this cycle, including the ones that found nothing |

A `fail` in section 5 usually explains a suspiciously short row above it, so the
test log is data rather than noise.

## Copying raw data

Built for pasting into a terminal, a ticket, or a spreadsheet.

| Action | Result |
|--------|--------|
| **Left-click a value** | that value only, with a tooltip naming the class — `IP copied!`, `MAC copied!` |
| **Right-click a row** | the entire record, `key: value` aligned |
| **Shift + left-click** | same as right-click, for trackpads with no second button |

The **EXPORT** button on the bay bar downloads the snapshot as JSON *and* copies
it to the clipboard in one action.

## Privacy

Not a disclaimer, an enforced property:

- **No third-party requests.** No CDN, no webfont, no analytics, no telemetry. CI
  fails the build if any shipped file gains an external reference.
- **Loopback only.** The service binds `127.0.0.1`, so a snapshot is not
  reachable from your LAN or by a guest on the same Wi-Fi.
- **`localStorage` only.** Two keys. That is why a refresh keeps your data and
  why `RESET` genuinely clears it.
- **Self-reported.** Every snapshot carries a `privacy` block naming the hosts
  the process contacted and what it is bound to. The dashboard shows you instead
  of asking you to trust it.

## Install

Download a standalone build from the [Releases](https://github.com/neohiro/LANScan/releases) page — no Python
needed — or run it from source:

```bash
pip install scapy     # optional: needed for active sweeps
python -m lanscan serve
```

```bash
# common flags
python -m lanscan serve --iface eth0 --port 8787 --interval 2
python -m lanscan scan --json          # one snapshot to stdout
python -m lanscan serve --no-update-check
```

## How it finds things

Active ARP sweeps catch everything on the subnet, including hosts that ignore
multicast. Passive capture and mDNS / SSDP / WS-Discovery add devices that never
answer a sweep and, more usefully, give them a name. MAC prefixes are resolved
against an offline OUI table, and PCI / USB identifiers against the `pci.ids`
and `usb.ids` databases — all local lookups, no API calls.

## Related

- [HoneyScan](https://github.com/neohiro/HoneyScan) — passive honeypot on the same network
- [Cripple-NetStrip](https://github.com/neohiro/Cripple-NetStrip) — harden the traffic LANScan is watching
- [SystemMonitor](https://github.com/neohiro/SystemMonitor) — the same idea for a single machine