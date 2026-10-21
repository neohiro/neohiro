import glob
for f in glob.glob('repos/*/assets/js/music-player.js'):
    s = open(f, encoding='utf-8').read()
    if 'a.load()' not in s:
        s = s.replace('document.body.appendChild(a);', 'a.load();\n      document.body.appendChild(a);')
        open(f, 'w', encoding='utf-8').write(s)
        print('load fix', f)
    else:
        print('already', f)
