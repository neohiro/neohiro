existing = set()
content = open('repos/neohiro.github.io/_data/repos.yml', encoding='utf-8').read()
for line in content.splitlines():
    if '  - name:' in line:
        part = line.split('name:')[1].strip()
        part = part.strip('"').strip("'")
        existing.add(part.lower())
import os
for d in os.listdir('repos'):
    p = os.path.join('repos', d)
    skip = {'neohiro.github.io', 'frenzypenguin-media.github.io', 'openstageisland.github.io',
            'transhumanists.github.io', 'frenzypenguin-media-site', 'fp-repo-workflow',
            'tests', 'scaffold', 'shared', 'templates', 'batchA', 'batchA_fix',
            'batchF', 'batchG_readmes', 'batchH', 'batchI', 'batch_privacy_staged',
            'batch_c_gen', 'data', 'repos'}
    if os.path.isdir(p) and d.lower() not in existing and d not in skip:
        print('TRULY MISSING:', d)
