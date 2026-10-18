import glob
start_new = """  function startAudio() {
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
stop_new = """  function stopAudio() {
    if(typeof cleanupAudio === 'function') try{cleanupAudio();}catch(e){}
    const f = document.getElementById('ht-player-iframe');
    if(f) f.src = f.src.replace(/autoplay=\\d/, 'autoplay=0');
    isPlaying = false;
    playBtn.textContent = '▶';
    statusDot.classList.remove('playing');
    if(typeof animationId !== 'undefined' && animationId) cancelAnimationFrame(animationId);
  }"""
for f in glob.glob('repos/frenzypenguin-media.github.io/assets/js/music-player.js') + glob.glob('repos/transhumanists.github.io/assets/js/music-player.js') + glob.glob('repos/openstageisland.github.io/assets/js/music-player.js'):
    s = open(f, encoding='utf-8').read()
    # Replace startAudio using a flexible regex: find from "  function startAudio() {" until next "  function " at same indentation
    import re
    # Simple: replace the block from startAudio to the line before startSynthFallback by matching startAudio opening and the closing brace before startSynthFallback
    # Instead, just replace using known pre/post markers
    # We know the original startAudio starts with "  function startAudio() {" and ends with a line "  }" followed by "\n\n  function startSynthFallback"
    s = re.sub(r"  function startAudio\(\) \{.*?\n  \}\n(?=\n  function startSynthFallback)", start_new + "\n", s, flags=re.DOTALL)
    # Replace stopAudio similarly: from "  function stopAudio() {" to line before drawVisualizer or similar
    s = re.sub(r"  function stopAudio\(\) \{.*?\n  \}\n(?=\n  function drawVisualizer)", stop_new + "\n", s, flags=re.DOTALL)
    # Also fix listener if broken
    s = s.replace("  playBtn.addEventListener('click', () => {\n    if (typeof isPlaying !== 'undefined' && isPlaying) {\n      if (typeof window.stopAudio === 'function') window.stopAudio();\n    } else {\n      if (typeof window.startAudio === 'function') window.startAudio();\n    }\n  });", "  playBtn.addEventListener('click', () => {\n    if (isPlaying) stopAudio();\n    else startAudio();\n  });")
    open(f, 'w', encoding='utf-8').write(s)
    print('fixed', f)
