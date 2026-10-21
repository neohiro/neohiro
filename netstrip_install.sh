#!/usr/bin/env bash
set -uo pipefail
echo "=== NETSTRIP INSTALL (headless) ==="
cd /tmp
pip3 uninstall -y netstrip Cripple-NetStrip 2>/dev/null || true
rm -rf /opt/netstrip /var/lib/netstrip 2>/dev/null || true
pip3 install cryptography psutil python-nmap dnspython 2>&1 | tail -4
rm -rf /tmp/Cripple-NetStrip
git clone https://github.com/neohiro/Cripple-NetStrip.git /tmp/Cripple-NetStrip 2>&1 | tail -3
cd /tmp/Cripple-NetStrip
pip3 install -e . --no-deps 2>&1 | tail -5 || pip3 install -e . 2>&1 | tail -8
echo "=== import test ==="
python3 -c "from netstrip.core.engine import NetStripEngine; print('engine OK')" 2>&1
python3 -c "from netstrip.core.crypto_utils import QuantumFernet; print('crypto OK')" 2>&1
python3 -c "from netstrip.core.classifier import TrafficClassifier; print('classifier OK')" 2>&1
echo "=== domain db ==="
ls -la /tmp/Cripple-NetStrip/netstrip/data/ 2>&1 || echo "(no data dir)"
python3 -c "
import glob, sqlite3, os
found=0
for pat in glob.glob('/tmp/Cripple-NetStrip/netstrip/data/*.sqlite') + glob.glob('/tmp/Cripple-NetStrip/netstrip/data/*.db'):
    con = sqlite3.connect(pat); cur = con.cursor()
    for r in cur.execute('SELECT name FROM sqlite_master WHERE type=\'table\''):
        t=r[0]; n=cur.execute('SELECT COUNT(*) FROM '+t).fetchone()[0]
        print('  '+os.path.basename(pat)+' / '+t+': '+str(n)); found=1
if not found: print('  (no sqlite tables found)')
"
echo "=== classification smoke ==="
python3 -c "from netstrip.core.classifier import TrafficClassifier; print('  classifier class OK')" 2>&1
echo "__NS_INSTALL_DONE__"