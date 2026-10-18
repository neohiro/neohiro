import glob, re
new_start = """  function startAudio() {
    if(typeof cleanupAudio === 'function') try{cleanupAudio();}catch(e){}
    let f = document.getElementById('ht-player-iframe');
    if(!f){
      f = document.createElement('iframe');
      f.id = 'ht-player-iframe';
      f.src = 'https://app.hearthis.at/embed/10124598/transparent_black/?autoplay=1';
      f.style.cssText = 'position:absolute;left:-9999px;width:1px;height:1px;border:0;opacity:0;pointer-events:none;';
      f.setAttribute('allow','autoplay');
      document.body.appendChild(f);
    } else {
      f.src = f.src.replace(/autoplay=\\d/, 'autoplay=1');
    }
    isPlaying = true;
    playBtn.textContent = '‖';
    statusDot.classList.add('playing');
    drawVisualizer();
  }"""
new_stop = """  function stopAudio() {
    if(typeof cleanupAudio === 'function') try{cleanupAudio();}catch(e){}
    const f = document.getElementById('ht-player-iframe');
    if(f) f.src = f.src.replace(/autoplay=\\d/, 'autoplay=0');
    isPlaying = false;
    playBtn.textContent = '▶';
    playBtn.setAttribute('aria-label', 'Play music');
    statusDot.classList.remove('playing');
    try { localStorage.setItem(STORAGE_PREFIX + 'playing', 'false'); } catch(e){}
    if(typeof animationId !== 'undefined' && animationId) cancelAnimationFrame(animationId);
  }"""
for f in glob.glob('repos/transhumanists.github.io/assets/js/music-player.js') + glob.glob('repos/openstageisland.github.io/assets/js/music-player.js'):
    s = open(f, encoding='utf-8').read()
    # Replace startAudio block
    s = re.sub(r"  function startAudio\(\) \{.*?\n  \}\n(?=\n  function startSynthFallback)", lambda m: new_start + "\n", s, flags=re.DOTALL)
    # Replace stopAudio block
    s = re.sub(r"  function stopAudio\(\) \{.*?\n  \}\n(?=\n  function drawVisualizer)", lambda m: new_stop + "\n", s, flags=re.DOTALL)
    # Fix listener
    s = s.replace("  playBtn.addEventListener('click', () => {\n    if (typeof isPlaying !== 'undefined' && isPlaying) {\n      if (typeof window.stopAudio === 'function') window.stopAudio();\n    } else {\n      if (typeof window.startAudio === 'function') window.startAudio();\n    }\n  });", "  playBtn.addEventListener('click', () => {\n    if (isPlaying) stopAudio();\n    else startAudio();\n  });")
    open(f, 'w', encoding='utf-8').write(s)
    print('done', f)
