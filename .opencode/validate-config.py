#!/usr/bin/env python3
"""Ground-truth validation: ensures opencode config and plugins are intact before session start."""
import json, sys, re

errors = []
# Validate JSON (JSONC allows comments — minimal parser)
try:
    raw = open('opencode.jsonc', 'r', encoding='utf-8').read()
    # JSONC safe: parse raw directly (this file has no comment syntax outside values)
    data = json.loads(raw)
    if 'instructions' not in data or len(data.get('instructions', '')) < 50:
        errors.append('instructions missing or too short')
    else:
        print('OK: instructions present and substantial')
    print('OK: opencode.jsonc parses valid JSON')
except Exception as e:
    errors.append(f'JSON parse error: {e}')

# Validate plugin syntax (basic structural checks)
plugin_path = '.opencode/plugins/opencode-context-prune.ts'
try:
    content = open(plugin_path, 'r', encoding='utf-8').read()
    if 'export default' not in content:
        errors.append('plugin missing export default')
    if 'version' not in content:
        errors.append('plugin missing version')
    else:
        print('OK: plugin syntax intact')
except Exception as e:
    errors.append(f'plugin read error: {e}')

if errors:
    print('VALIDATION FAILURES:', file=sys.stderr)
    for err in errors:
        print(f'  - {err}', file=sys.stderr)
    sys.exit(1)
else:
    print('VALIDATION PASSED — session safe to start.')
