---
stars: 3
forks: 0
open_issues: 1
pushed_at: 2026-08-29T08:53:49Z
created_at: 2026-07-22T01:33:11Z
title: Cripple-NetStrip
tagline: "Network hardening · DNS sinkhole · Encrypted DNS · Firewall · Traffic classification"
platform: Windows / macOS / Linux / Android
language: Python
repo_url: https://github.com/neohiro/Cripple-NetStrip
featured: true
weight: 2
category: Network Security
icon: |
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
    <circle cx="12" cy="12" r="10"/>
    <path d="M12 6v6l4 2" stroke="var(--red)" stroke-width="2"/>
    <path d="M8 16h8" stroke="var(--red)" stroke-width="2"/>
  </svg>
---
Network visibility and control. See everything. Control everything. Trust nothing.

## Platforms

Builds ship for **Windows, macOS, Linux and Android** (APK), plus a headless mode for
Raspberry Pi, NUC and home-server deployments that protect a whole LAN.

- **Windows / macOS / Linux** — desktop builds with live dashboard, tray control and native OS firewall sync
- **Android** — on-device APK build, same kernel-level packet filtering
- **Headless / LAN** — run it on the gateway and every device on the network is covered

## Three layers, at once

1. **DNS sinkhole** — 3.2M+ blocked domains across 49 threat feeds, resolved to `0.0.0.0`
2. **Encrypted-DNS interception** — DoH/DoT tunnels are caught, not trusted
3. **Packet-level firewall** — hardcoded IPs and stealthy IPv6 broadcasts never leave the machine

Works alongside dnscrypt-proxy, torifier, YogaDNS, NextDNS and antivirus/VPN suites without
DNS loops or conflicts.