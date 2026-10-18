import os, re
empty = []
for root, dirs, files in os.walk('repos/neohiro.github.io'):
    for f in files:
        if f.endswith(('.md', '.html', '.yml')):
            p = os.path.join(root, f)
            try:
                content = open(p, encoding='utf-8', errors='ignore').read()
                for pattern in [r'title=""', r'title="\s+"', r"title=''", r"title='\s+'"]:
                    matches = re.findall(pattern, content)
                    if matches:
                        empty.append((p, len(matches), pattern))
            except:
                pass
for item in empty[:20]:
    print(item)
