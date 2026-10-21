import glob
for f in glob.glob('repos/*/assets/js/music-player.js'):
    s = open(f, encoding='utf-8').read()
    # After appending audio, add canplay handler that calls play
    old = "document.body.appendChild(a);\n    }\n    try{ a.play(); }catch(e){}"
    new = "document.body.appendChild(a);\n    a.addEventListener('canplay', () => { try{ a.play(); }catch(e){} });\n    }\n    try{ a.play(); }catch(e){}"
    s = s.replace(old, new)
    open(f, 'w', encoding='utf-8').write(s)
    print('canplay fix', f)
