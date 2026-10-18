import os, re
for root, dirs, files in os.walk('pages-site'):
    for f in files:
        if f.endswith('.html'):
            p = os.path.join(root, f)
            content = open(p, encoding='utf-8', errors='ignore').read()
            m = re.findall(r'title=""', content)
            if m:
                print(p, len(m))
