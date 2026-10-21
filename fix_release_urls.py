import glob
urls = [
    "https://github.com/neohiro/dj/releases/download/v1.0/Little.Mistake.-.rec_20250803-185930.hearthis.at.mp3",
    "https://github.com/neohiro/dj/releases/download/v1.0/Neo.at.Open.Stage.Island.-.rec_20250403-131400.hearthis.at.mp3",
    "https://github.com/neohiro/dj/releases/download/v1.0/Whats.in.the.box.Burn2.-.rec_20230920-141543.hearthis.at.mp3"
]
old = "const tracks = [\"https://github.com/neohiro/dj/releases/download/v1.0/Little%20Mistake%20-%20rec_20250803-185930%20(hearthis.at).mp3\",\"https://github.com/neohiro/dj/releases/download/v1.0/Neo%20at%20Open%20Stage%20Island%20-%20rec_20250403-131400%20(hearthis.at).mp3\",\"https://github.com/neohiro/dj/releases/download/v1.0/Whats%20in%20the%20box%20%5BBurn2%5D%20-%20rec_20230920-141543%20(hearthis.at).mp3\"];"
new = "const tracks = [\"" + "\",\"".join(urls) + "\"];"
for f in glob.glob('repos/*/assets/js/music-player.js'):
    s = open(f, encoding='utf-8').read()
    s = s.replace(old, new)
    open(f, 'w', encoding='utf-8').write(s)
    print('fixed url', f)
