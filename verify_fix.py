import glob
for f in glob.glob('repos/*/assets/js/music-player.js'):
    s = open(f, encoding='utf-8').read()
    has_click = "addEventListener('click'" in s
    has_keydown = "addEventListener('keydown'" in s
    if not has_click:
        s = s.replace("  playBtn.addEventListener('keydown',", "  playBtn.addEventListener('click', () => {\n    if (isPlaying) stopAudio();\n    else startAudio();\n  });\n  playBtn.addEventListener('keydown',")
        open(f, 'w', encoding='utf-8').write(s)
        print('fixed click', f)
    else:
        print('click ok', f)
    print('keydown', 'ok' if has_keydown else 'MISSING', f)
