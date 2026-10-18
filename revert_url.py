import glob
for f in glob.glob('repos/*/assets/js/music-player.js'):
    s = open(f, encoding='utf-8').read()
    s = s.replace('https://github.com/neohiro/dj/releases/download/v1.0/Whats%20in%20the%20box%20%5BBurn2%5D%20-%20rec_20230920-141543%20(hearthis.at).mp3', 'https://hearthis.at/neohiro/rec20230920-141543/listen/?s=wxD')
    open(f, 'w', encoding='utf-8').write(s)
    print('reverted', f)
