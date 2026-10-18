import glob
for f in glob.glob('repos/*/assets/js/music-player.js'):
    s = open(f, encoding='utf-8').read()
    if "addEventListener('click', () => {" not in s:
        s = s.replace("playBtn.addEventListener('keydown', (e) => { if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); if (isPlaying) stopAudio(); else startAudio(); } });",
                      "playBtn.addEventListener('click', () => {\n    if (isPlaying) stopAudio();\n    else startAudio();\n  });\n  playBtn.addEventListener('keydown', (e) => { if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); if (isPlaying) stopAudio(); else startAudio(); } });")
        open(f, 'w', encoding='utf-8').write(s)
        print('fixed', f)
    else:
        print('ok', f)
