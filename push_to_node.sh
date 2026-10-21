#!/usr/bin/env bash
# Push whitelist + rules to remote node /opt/cripple/netstrip
# Assumes SSH key access to root@node (Tailscale 100.126.213.83)
set -euo pipefail

NODE="node"
REMOTE_DIR="/opt/cripple/netstrip"
REMOTE_DB_PATH="/root/.netstrip/NetStrip.db"
LOCAL_WL="${HOME}/.NetStrip/lists/whitelist_outlook.txt"

# Validate local file exists before network call
if [[ ! -f "$LOCAL_WL" ]]; then
    echo "ERROR: Local whitelist file missing: $LOCAL_WL" >&2
    exit 1
fi

# 1. Push file to remote lists directory (adjust target if remote layout differs)
scp -q "$LOCAL_WL" "root@$NODE:$REMOTE_DIR/netstrip/data/lists/whitelist_outlook.txt"

# 2. Insert rules (idempotent) + verify insertion with post-check
ssh -l root "$NODE" bash -s << 'REMOTESQL' -- "${REMOTE_DB_PATH}" "${NODE}"
DB_PATH="$1"
HOST="$2"
sqlite3 "$DB_PATH" << 'SQL'
INSERT OR IGNORE INTO user_rules (pattern, action, scope, app_name, category) VALUES
('outlook.com','allow','global',NULL,'system'),
('outlook.live.com','allow','global',NULL,'system'),
('live.com','allow','global',NULL,'system'),
('login.live.com','allow','global',NULL,'system'),
('login.microsoftonline.com','allow','global',NULL,'system'),
('account.live.com','allow','global',NULL,'system'),
('microsoftonline.com','allow','global',NULL,'system'),
('msftauth.net','allow','global',NULL,'system'),
('office.com','allow','global',NULL,'system');
SQL
REMOTESQL

echo "=== Remote user_rules count (post-push) ==="
ssh -l root "$NODE" "sqlite3 $REMOTE_DB_PATH 'SELECT COUNT(*) FROM user_rules;'"

echo "=== Remote stats (latest 3) ==="
ssh -l root "$NODE" "sqlite3 $REMOTE_DB_PATH 'SELECT date, total_queries, total_blocked, total_allowed FROM statistics ORDER BY date DESC LIMIT 3;'"

echo "=== Remote whitelist file presence ==="
ssh -l root "$NODE" "ls -la $REMOTE_DIR/netstrip/data/lists/whitelist_outlook.txt 2>/dev/null || ls -la $REMOTE_DIR/.NetStrip/lists/whitelist_outlook.txt 2>/dev/null || echo 'WARNING: File not found at expected paths'"
