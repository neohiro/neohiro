import os, glob
old = '<span class="ul-player-label">HEARTHIS.AT / NEOHIRO</span>'
new = '<a class="ul-player-label" href="https://hearthis.at/neohiro" target="_blank" rel="noopener noreferrer" aria-label="Link to hearthis.at/neohiro">HEARTHIS.AT / NEOHIRO</a>'
paths = glob.glob('repos/*/_includes/music-player.html') + ['transhumanists.github.io/_includes/music-player.html', 'repos/neohiro.github.io/_includes/music-player.html', 'repos/frenzypenguin-media.github.io/_includes/music-player.html']
for path in paths:
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            s = f.read()
        if old in s:
            s = s.replace(old, new)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(s)
            print('Updated', path)
        else:
            print('Skip', path)
