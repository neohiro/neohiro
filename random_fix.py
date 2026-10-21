import glob
old_str = "      a.src = 'https://github.com/neohiro/dj/releases/download/v1.0/Whats%20in%20the%20box%20%5BBurn2%5D%20-%20rec_20230920-141543%20(hearthis.at).mp3';"
new_str = "      const tracks = [\"https://github.com/neohiro/dj/releases/download/v1.0/Little%20Mistake%20-%20rec_20250803-185930%20(hearthis.at).mp3\",\"https://github.com/neohiro/dj/releases/download/v1.0/Neo%20at%20Open%20Stage%20Island%20-%20rec_20250403-131400%20(hearthis.at).mp3\",\"https://github.com/neohiro/dj/releases/download/v1.0/Whats%20in%20the%20box%20%5BBurn2%5D%20-%20rec_20230920-141543%20(hearthis.at).mp3\"];\n      a.src = tracks[Math.floor(Math.random() * tracks.length)];"
for f in glob.glob('repos/*/assets/js/music-player.js'):
    s = open(f, encoding='utf-8').read()
    if old_str in s:
        s = s.replace(old_str, new_str)
        open(f, 'w', encoding='utf-8').write(s)
        print('updated', f)
    else:
        print('already done or different', f)
