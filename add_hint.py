import glob
for f in glob.glob('repos/*/assets/js/music-player.js'):
    s = open(f, encoding='utf-8').read()
    # Add keyboard hint title if not present
    if 'Space/Enter' not in s:
        s = s.replace('playBtn.setAttribute(\'aria-label\', \'Play music\');', 'playBtn.setAttribute(\'aria-label\', \'Play music\');\n    playBtn.setAttribute(\'title\', \'Play / Pause (Space or Enter)\');')
        open(f, 'w', encoding='utf-8').write(s)
        print('polish title', f)
    else:
        print('already', f)
