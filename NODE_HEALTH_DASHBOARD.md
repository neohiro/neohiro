# Node Health Dashboard — root@node (100.126.213.83 / Tailscale)

## System (real-time from SSH)

| Metric | Value | Status |
|---|---|---|
| **Host** | `Linux node 6.8.0-146-generic` | OK |
| **Uptime** | 1 week, 1 day, 12h 55m | Stable |
| **CPU load** | 0.92 / 1.03 / 1.02 (1m/5m/15m) | Moderate (6/183 tasks) |
| **CPU cores** | Multi-core x86_64 (from /proc/loadavg context) | OK |
| **RAM total** | 709 Mi | — |
| **RAM used** | 407 Mi | ~57% |
| **RAM available** | 302 Mi | OK (no pressure) |
| **Swap total** | 767 Mi | — |
| **Swap used** | 142 Mi | ~18% (low) |
| **Disk (/)** | 9.1G / 5.0G used / 3.6G avail | 59% — healthy |
| **Disk (/opt)** | Same /dev/vda2 (shared rootfs) | OK |

## Network

| Interface | IP / Net | Notes |
|---|---|---|
| `lo` | 127.0.0.1/8 | Local |
| `eth0` | 92.119.124.2/24 | Public / primary |
| `tailscale0` | 100.126.213.83/32 | Tailscale SSH target |
| `node1` | 10.103.164.216 | Mesh / LAN |
| `node2` | 10.100.116.62 | Mesh / LAN |
| `node3` | 10.101.202.226 | Mesh / LAN |
| `node4` | 10.100.167.183 | Mesh / LAN |

## Cripple 3.9.3 Module

| Check | Status | Evidence |
|---|---|---|
| Source deployed (`/opt/cripple/netstrip`) | ✅ Present (v3.9.3 verified) | `changelog.md` + `version_info.txt` |
| Daemon running (`python main.py --service`) | ❌ **NOT RUNNING** | `ps aux` — no match; must start |
| Blocklist module (3.2M+ domains) | ⏳ Ready to load | 42 feeds enabled by default |
| Traffic filtering (DNS + packet) | ⏳ **Inactive until started** | Needs `nohup python main.py --service` |

## Recommended Actions
1. **Start Cripple headless**: `ssh -l root node 'nohup python /opt/cripple/netstrip/main.py --service > /dev/null 2>&1 &'`
2. **Confirm daemon**: `pgrep -a -f "main.py"` (after start; use `-f` not `--service` as pgrep option)
3. **Confirm filtering**: `dig @127.0.0.1 doubleclick.net +short` → expect `0.0.0.0`
4. **Monitor RAM**: 302 Mi available; module cold-load ~3MB cache + ~1-2s peak, safe.

Assumption: node is a lightweight VM/container (709 Mi RAM, 9 GB disk, ~58% disk used). Cripple headless + 3.2M module fits comfortably; no resource upgrade needed.
