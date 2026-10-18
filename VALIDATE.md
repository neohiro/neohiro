# Release Validation — Quick Checks

Run these to verify state after any MCP change:

- `python -c "import json; s=json.load(open('opencode.jsonc'))['mcp']['servers']; [print(k, s[k]['disabled']) for k in s]"`
- `python -c "import orjson; print('orjson ok')"` (whitelist check)
- `python -c "from scrapling.fetchers import Fetcher; print('scrapling lib ok')"` (library only; server removed)
- `python -m mcp_server_git --help` (git init check)

Skipped risk items:
- mcp v2 conflict with mcp-server-* (would require downgrading core lib; skipped)
- Full browser automation test for playwright (requires external browser install)
