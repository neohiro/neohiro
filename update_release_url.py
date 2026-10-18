import glob
new_url = 'https://github.com/neohiro/dj/releases/download/v1.0/mix.mp3'
for f in glob.glob('repos/*/assets/js/music-player.js'):
    s = open(f, encoding='utf-8').read()
    s = s.replace("a.src = 'https://hearthis.at/neohiro/rec20230920-141543/listen/?s=wxD';", "a.src = '" + new_url + "';")
    open(f, 'w', encoding='utf-8').write(s)
    print('updated', f)
