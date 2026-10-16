import re
d = open('README.md', encoding='utf-8').read()
d = re.sub(r'\?style=flat[^)\"]+', '?style=flat', d)
open('README.md', 'w', encoding='utf-8').write(d)
count = d.count('?style=flat)')
print('Fixed badges count:', count)
