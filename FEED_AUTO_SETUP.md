# Feed / Load Auto-Setup — Headless Cripple Deploy

Problem on node: only 124 domains loaded; 3.2M module requires downloaded feeds (`netstrip/data/lists/*.txt` + `.pkl` cache). Feeds missing after backslash-artifact extraction.

Automatic mechanism for future headless installs:

1. Pre-start download (add to `cripple.service` or run before `systemctl start`):
   ```bash
   ssh root@node 'cd /opt/cripple/netstrip && python3 main_fixed.py --update-blocklists'
   ```
   Per `DEPLOY_NODE_3.9.3.md` line 220 and README: `python main.py --update-blocklists` forces feed refresh/download.

2. Systemd convenience (optional — add `ExecStartPre` to `/etc/systemd/system/cripple.service`):
   ```ini
   [Service]
   ExecStartPre=/usr/bin/python3 /opt/cripple/netstrip/main_fixed.py --update-blocklists
   ```
   Then: `systemctl daemon-reload; systemctl restart cripple.service`

3. Verify after start:
   ```bash
   ssh root@node 'PYTHONPATH=/opt/cripple/netstrip python3 -c "from netstrip.data.blocklist_manager import BlocklistManager; bl=BlocklistManager(lists_dir=\"netstrip/data/lists\",async_load=False); print(\"Domains:\",len(bl.domain_map))"'
   ```
   Target: ~3,236,262+ (per README / changelog v3.9.3).

4. If feeds still missing after `--update-blocklists`: check network access to feed URLs (GitHub raw / AdGuard / OISD / URLhaus) — some require `curl -L -o ...` alternate if Python fetch blocked by proxy/firewall.

Note: `customtkinter` also needed for full daemon start (`pip install customtkinter` — separate from feed issue).
