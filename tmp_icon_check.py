import yaml
with open('repos/neohiro.github.io/_data/repos.yml', encoding='utf-8') as f:
    data = yaml.safe_load(f)
for r in data['repos']:
    cat = r['category']
    # Check which condition catches it
    conditions = []
    if 'Network' in cat or 'Security' in cat or 'Hardening' in cat:
        conditions.append('security')
    elif 'Cryptography' in cat:
        conditions.append('crypto')
    elif 'Games' in cat:
        conditions.append('games')
    elif 'Developer' in cat or 'Utilities' in cat or 'System Utilities' in cat:
        conditions.append('dev/util')
    elif 'Communication' in cat or 'Media' in cat:
        conditions.append('comm/media')
    elif 'Information' in cat or 'Health' in cat:
        conditions.append('info/health')
    elif 'Privacy' in cat:
        conditions.append('privacy')
    else:
        conditions.append('else/default')
    print(f"{r['name']:20} | {cat:30} -> {conditions[0]}")
