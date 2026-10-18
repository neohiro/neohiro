import glob
for f in glob.glob('repos/*/assets/js/music-player.js'):
    s = open(f, encoding='utf-8').read()
    s = s.replace("a.preload = 'metadata';", "a.preload = 'auto'; a.title = 'Neohiro DJ Mix';")
    open(f, 'w', encoding='utf-8').write(s)
    print('polish', f)
