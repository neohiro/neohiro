#Requires -Version 5.1
# Push whitelist + DB rules to remote node (PowerShell / Windows execution)
# Assumption: SSH keys configured; remote DB at /root/.netstrip/NetStrip.db
$ErrorActionPreference = "Stop"

$NODE = "node"
$REMOTE_DIR = "/opt/cripple/netstrip"
$REMOTE_DB = "/root/.netstrip/NetStrip.db"
$LOCAL_WL = "$env:USERPROFILE\.NetStrip\lists\whitelist_outlook.txt"

if (-not (Test-Path $LOCAL_WL)) {
    throw "Local whitelist file missing: $LOCAL_WL"
}

Write-Host "=== Pushing whitelist ==="
scp -q $LOCAL_WL "root@$NODE`:$REMOTE_DIR/netstrip/data/lists/whitelist_outlook.txt"

Write-Host "=== Inserting DB rules ==="
$sql = @'
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
'@
ssh -l root $NODE "sqlite3 $REMOTE_DB << 'SQL'`n$sql`nSQL"

Write-Host "=== Remote user_rules count ==="
ssh -l root $NODE "sqlite3 $REMOTE_DB 'SELECT COUNT(*) FROM user_rules;'"

Write-Host "=== Remote stats ==="
ssh -l root $NODE "sqlite3 $REMOTE_DB 'SELECT date, total_queries, total_blocked, total_allowed FROM statistics ORDER BY date DESC LIMIT 3;'"

Write-Host "=== File presence check ==="
ssh -l root $NODE "ls -la $REMOTE_DIR/netstrip/data/lists/whitelist_outlook.txt 2>/dev/null || ls -la $REMOTE_DIR/.NetStrip/lists/whitelist_outlook.txt 2>/dev/null || echo 'File not found at expected paths'"
