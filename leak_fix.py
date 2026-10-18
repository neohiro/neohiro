import glob
for f in glob.glob('repos/*/assets/js/music-player.js'):
    s = open(f, encoding='utf-8').read()
    old = "    if(a){ try{ a.pause(); a.currentTime = 0; }catch(e){} }"
    new = "    if(a){ try{ a.pause(); a.currentTime = 0; }catch(e){}; a.remove(); }"
    if old in s:
        s = s.replace(old, new)
        open(f, 'w', encoding='utf-8').write(s)
        print('fixed leak', f)
    else:
        print('skipped', f)
