import glob
insert = """  // Play button toggle
  playBtn.addEventListener('click', () => {
    if (isPlaying) stopAudio();
    else startAudio();
  });

  // Collapse HUD when not playing on load
  const hud = document.getElementById('ul-player');
  if (hud && !isPlaying) {
    hud.classList.add('collapsed');
    hud.style.transform = 'translateY(-100%)';
  }

"""
for f in glob.glob('repos/frenzypenguin-media.github.io/assets/js/music-player.js') + glob.glob('repos/transhumanists.github.io/assets/js/music-player.js') + glob.glob('repos/openstageisland.github.io/assets/js/music-player.js'):
    s = open(f, encoding='utf-8').read()
    # Truncate leftover after })();
    idx = s.rfind('})();')
    if idx != -1:
        s = s[:idx+4]
    # Insert listener before autoPlay block if present
    s = s.replace("  if (autoPlay) {\n    const resumeOnInteract = () => {\n      startAudio();", insert + "  if (autoPlay) {\n    const resumeOnInteract = () => {\n      startAudio();")
    open(f, 'w', encoding='utf-8').write(s)
    print('cleaned', f)
