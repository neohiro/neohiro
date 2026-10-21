import glob
for p in glob.glob('repos/*/assets/js/music-player.js') + ['transhumanists.github.io/assets/js/music-player.js']:
    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
        s = f.read()
    s = s.replace("a.preload = 'auto';", "a.preload = 'none';")
    with open(p, 'w', encoding='utf-8') as f:
        f.write(s)
    print('Lazy preload', p)
