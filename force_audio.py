import glob
start_direct = """  function startAudio() {
    if(typeof cleanupAudio === 'function') try{cleanupAudio();}catch(e){}
    let a = document.getElementById('ul-hack-audio');
    if(!a){
      a = document.createElement('audio');
      a.id = 'ul-hack-audio';
      a.crossOrigin = 'anonymous';
      a.preload = 'metadata';
      a.style.display = 'none';
      a.src = 'https://hearthis.at/neohiro/rec20230920-141543/listen/?s=wxD';
      document.body.appendChild(a);
    }
    try{ a.play(); }catch(e){}
    isPlaying = true;
    playBtn.textContent = '⏸';
    playBtn.setAttribute('aria-label', 'Pause music');
    statusDot.classList.add('playing');
    if(typeof animationId !== 'undefined' && animationId) cancelAnimationFrame(animationId);
    if(typeof drawWaveform === 'function') animationId = requestAnimationFrame(drawWaveform);
  }"""
stop_direct = """  function stopAudio() {
    if(typeof cleanupAudio === 'function') try{cleanupAudio();}catch(e){}
    const a = document.getElementById('ul-hack-audio');
    if(a){ try{ a.pause(); a.currentTime = 0; }catch(e){} }
    isPlaying = false;
    playBtn.textContent = '▶';
    playBtn.setAttribute('aria-label', 'Play music');
    statusDot.classList.remove('playing');
    if(typeof animationId !== 'undefined' && animationId) cancelAnimationFrame(animationId);
    if(typeof clearCanvas === 'function') clearCanvas();
  }"""
for f in glob.glob('repos/neohiro.github.io/assets/js/music-player.js') + glob.glob('repos/frenzypenguin-media.github.io/assets/js/music-player.js') + glob.glob('repos/transhumanists.github.io/assets/js/music-player.js') + glob.glob('repos/openstageisland.github.io/assets/js/music-player.js'):
    s = open(f, encoding='utf-8').read()
    # Replace startAudio block
    import re
    s = re.sub(r"  function startAudio\(\) \{.*?\n  \}\n(?=\n  function startSynthFallback)", lambda m: start_direct + "\n", s, flags=re.DOTALL)
    s = re.sub(r"  function stopAudio\(\) \{.*?\n  \}\n(?=\n  function drawVisualizer)", lambda m: stop_direct + "\n", s, flags=re.DOTALL)
    # Fix listener if broken
    s = s.replace("  playBtn.addEventListener('click', () => {\n    if (typeof isPlaying !== 'undefined' && isPlaying) {\n      if (typeof window.stopAudio === 'function') window.stopAudio();\n    } else {\n      if (typeof window.startAudio === 'function') window.startAudio();\n    }\n  });", "  playBtn.addEventListener('click', () => {\n    if (isPlaying) stopAudio();\n    else startAudio();\n  });")
    open(f, 'w', encoding='utf-8').write(s)
    print('direct audio', f)
