import re, glob, os
files = glob.glob('repos/*/assets/js/music-player.js') + ['transhumanists.github.io/assets/js/music-player.js']
for path in files:
    if not os.path.exists(path):
        continue
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        s = f.read()
    # Remove synth fallback function
    s = re.sub(r'\n  function startSynthFallback\(track\) \{.*?\n  \}\n', '\n', s, flags=re.DOTALL)
    # Replace audioCtx/variables block with just audioCtx if needed, but simpler: just delete synth-related lines
    s = s.replace('    if (osc1) { try { osc1.stop(); osc1.disconnect(); } catch(e) {} osc1 = null; }\n', '')
    s = s.replace('    if (osc2) { try { osc2.stop(); osc2.disconnect(); } catch(e) {} osc2 = null; }\n', '')
    s = s.replace('    if (filter) { try { filter.disconnect(); } catch(e) {} filter = null; }\n', '')
    s = s.replace('    if (masterGain) { try { masterGain.disconnect(); } catch(e) {} masterGain = null; }\n', '')
    s = s.replace('    if (analyser) { try { analyser.disconnect(); } catch(e) {} analyser = null; }\n', '')
    s = s.replace('    if (audioCtx && audioCtx.state !== \'closed\') {\n      try { audioCtx.close(); } catch(e) {}\n      audioCtx = null;\n    }\n', '')
    s = s.replace('    usingSynth = false;\n', '')
    s = s.replace("    a.onerror = () => { startSynthFallback(track); };\n", "")
    s = s.replace("if(typeof drawWaveform === 'function') animationId = requestAnimationFrame(drawWaveform);", "if(typeof drawVisualizer === 'function') animationId = requestAnimationFrame(drawVisualizer);")
    s = s.replace('  let usingSynth = false;\n', '')
    s = s.replace('  let playPromise = null; // Track in-flight play() promise\n', '')
    s = s.replace('  let audioCtx = null;\n  let masterGain = null;\n  let analyser = null;\n  let osc1 = null, osc2 = null, filter = null;', '  let audioCtx = null;')
    s = s.replace('  // Try real stream first; fall back to synth on error', '  // Lazy-load direct MP3 stream from neohiro/dj releases')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(s)
    print('Processed', path)
