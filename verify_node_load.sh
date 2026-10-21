#!/usr/bin/env bash
# Remote verification: full domain load on node /opt/cripple/netstrip
set -euo pipefail
NODE="node"
REMOTEDIR="/opt/cripple/netstrip"
echo "=== Remote node domain load check ==="
ssh -l root "$NODE" "cd $REMOTEDIR && python3 -c '
import sys, os
sys.path.insert(0, \"netstrip\")
from netstrip.data.blocklist_manager import BlocklistManager
bl = BlocklistManager(lists_dir=\"netstrip/data/lists\", async_load=False)
count = len(bl.domain_map) if hasattr(bl, \"domain_map\") else 0
stats = bl.get_stats()
feed_cats = len(bl.sources_metadata)
print(\"Domains loaded:\", count)
print(\"Stats categories loaded:\", feed_cats)
print(\"Category counts:\", {k.value: v for k,v in stats.items() if v > 0})
'"
echo "=== Remote feed file count ==="
ssh -l root "$NODE" "ls $REMOTEDIR/netstrip/data/lists/*.txt 2>/dev/null | wc -l || echo 'No .txt feeds at expected path'; ls $REMOTEDIR/.NetStrip/lists/*.txt 2>/dev/null | wc -l || echo 'No .txt feeds at alt path'"
echo "=== Remote DB user_rules count ==="
ssh -l root "$NODE" "sqlite3 /root/.netstrip/NetStrip.db 'SELECT COUNT(*) FROM user_rules;'"
