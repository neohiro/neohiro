import glob
for f in glob.glob('repos/*/assets/js/music-player.js'):
    s = open(f, encoding='utf-8').read()
    # Add aria-live to the HUD initialization area (after playBtn event or near statusDot setup)
    # Find the line after statusDot setup or before drawVisualizer
    if 'aria-live' not in s:
        s = s.replace('statusDot.classList.add(\'playing\');', "statusDot.classList.add('playing');\n    document.getElementById('ul-player').setAttribute('aria-live', 'polite');")
        open(f, 'w', encoding='utf-8').write(s)
        print('aria-live', f)
