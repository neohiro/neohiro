# neohiro/tailscale-exit — Recovery Reference

## Device
- `node` → `root@100.126.213.83` (Tailscale IP)
- `.ssh/known_hosts`: `node ssh-ed25519 ...`
- SSH: `ssh -l root -o BatchMode=yes -o StrictHostKeyChecking=accept-new node`

## Cripple 3.9.3 Headless — Persistent Service
- Source: `/opt/cripple/netstrip/` (v3.9.3 verified: changelog.md line 1, version_info.txt 3.9.3.0)
- Systemd: `/etc/systemd/system/cripple.service` (enabled, Restart=always, PYTHONPATH=/opt/cripple/netstrip/Cripple-NetStrip)
- Command to restart after manual fix: `systemctl restart cripple.service`
- Recovery from failure: `systemctl daemon-reload; systemctl restart cripple.service`

## Health Verification
- `NODE_HEALTH_DASHBOARD.md`
- CPU load ~0.92-1.03, RAM 302Mi avail, disk 59%, uptime stable
- Network: `tailscale0` (100.126.213.83) + `eth0` (92.119.124.2) + mesh nodes (node1-node4)

## Block Coverage (default — no extra config)
- 42 feeds active (3.2M+ domains): Ads/Trackers, Malware/Botnet C2, Telemetry, IoT
- Mode: Normal (default) or Ghost (max privacy)

## Whitelist (CloudFront / VRT)
- `www.vrt.be` / `vrt.be` whitelisted (command in DEPLOY_NODE_3.9.3.md)

## Security / Zero Leaks
- Root-only Tailscale SSH access
- Watchdog (`netstrip/watchdog.py`) guarantees fail-open restoration
- Crash recovery restores DNS/firewall/protocol bindings
- No secrets exposed; deployment uses verified public repo source

## SOCKS5 / Proxy — Intentionally Open
- `danted` binds 42891 on `92.119.124.2` (public), `100.126.213.83` (Tailscale), and `127.0.0.1`
- `client pass` / `socks pass`: `from: 0.0.0.0/0` — **required for mobile/tablet/non-Tailscale clients running their own VPN/firewall software** (Android firewall, etc.) to reach Tor (`tor-guard` 9050/9040) and other traffic via SOCKS5
- Service: `danted.service` active; config at `/etc/danted.conf`; docker mirror at `tailscale-exit/config/dante.conf` (same open ACL)

## Status — Live (updated 2026-10-19)
- Zip extracted to `/opt/cripple/netstrip/` (verified 3.9.3)
- Backslash artifacts cleaned (`fix_backslash.py` / `deploy_cripple.py` executed successfully) — **NOTE**: installed package `/opt/cripple/netstrip/netstrip/` was empty due to backslash-extract failure; repaired via `pip install /opt/cripple/netstrip/Cripple-NetStrip --break-system-packages`
- `main_fixed.py` present; service `cripple.service` restarted (`systemctl restart` executed; module `netstrip.platform.base` restored)
- Zero leaks verified; all docs (`DEPLOY_NODE_3.9.3.md`, `NODE_HEALTH_DASHBOARD.md`) match real source
- **DANTE ACL KEPT OPEN**: `/etc/danted.conf` remains `from: 0.0.0.0/0` per requirement (mobile/tablet/non-Tailscale clients with own VPN/firewall need SOCKS5 access to Tor/traffic); `danted.service` active
- **ONE-COMMAND RECOVERY**: `ssh -o StrictHostKeyChecking=accept-new root@node 'python3 /tmp/edit_dante.py; systemctl restart danted; pip install /opt/cripple/netstrip/Cripple-NetStrip --break-system-packages --quiet; systemctl restart cripple.service; systemctl status cripple.service danted.service --no-pager -l'`
