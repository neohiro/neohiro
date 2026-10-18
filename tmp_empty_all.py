import os, re
results = []
for root, dirs, files in os.walk('repos/neohiro.github.io'):
    # Skip assets/css/js/minified
    dirs[:] = [d for d in dirs if d not in ['assets', '.git', '.github']]
    for f in files:
        if f.endswith(('.md', '.html', '.yml')):
            p = os.path.join(root, f)
            try:
                content = open(p, encoding='utf-8', errors='ignore').read()
                for pat in [r'title=""', r'title="\s+"', r"title=''", r"title='\s+'"]:
                    for m in re.finditer(pat, content):
                        line = content[:m.start()].count('\n') + 1
                        results.append((p, pat, line))
            except:
                pass
if results:
    for r in results[:20]:
        print(r)
else:
    print("No empty title attributes found across site source.")
