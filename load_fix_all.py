import glob
for f in glob.glob('repos/*/assets/js/music-player.js'):
    s = open(f, encoding='utf-8').read()
    if "a.load();" in s and "a.addEventListener('canplay'" not in s:
        s = s.replace("a.load();\n      document.body.appendChild(a);", "try{ a.load(); }catch(e){}\n      document.body.appendChild(a);\n      a.addEventListener('canplay', () => { try{ a.play(); }catch(e){} });\n      setTimeout(() => { try{ a.play(); }catch(e){}; }, 500);")
        open(f, 'w', encoding='utf-8').write(s)
        print('fixed', f)
    else:
        print('ok', f)
