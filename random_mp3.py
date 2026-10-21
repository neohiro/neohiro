import glob
urls = [
    "https://github.com/neohiro/dj/releases/download/v1.0/Little%20Mistake%20-%20rec_20250803-185930%20(hearthis.at).mp3",
    "https://github.com/neohiro/dj/releases/download/v1.0/Neo%20at%20Open%20Stage%20Island%20-%20rec_20250403-131400%20(hearthis.at).mp3",
    "https://github.com/neohiro/dj/releases/download/v1.0/Whats%20in%20the%20box%20%5BBurn2%5D%20-%20rec_20230920-141543%20(hearthis.at).mp3"
]
for f in glob.glob('repos/*/assets/js/music-player.js'):
    s = open(f, encoding='utf-8').read()
    old_line = "      a.src = 'https://hearthis.at/neohiro/rec20230920-141543/listen/?s=wxD';"
    # Replace with random selection
    new_block = "      const tracks = [\"" + '\",\"'.join(urls) + '\"];\n      const randomUrl = tracks[Math.floor(Math.random() * tracks.length)];\n      a.src = randomUrl;'
    s = s.replace(old_line, new_block)
    open(f, 'w', encoding='utf-8').write(s)
    print('randomized', f)
