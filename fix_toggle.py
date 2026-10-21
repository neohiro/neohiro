import glob
old_block = "  toggle.addEventListener('click', () => {\n    isCollapsed = !isCollapsed;\n    player.classList.toggle('collapsed', isCollapsed);\n    try { localStorage.setItem(STORAGE_PREFIX + 'collapsed', isCollapsed); } catch(e){}\n  });"
new_block = "  toggle.addEventListener('click', () => {\n    isCollapsed = !isCollapsed;\n    player.classList.toggle('collapsed', isCollapsed);\n    toggle.setAttribute('aria-expanded', String(!isCollapsed));\n    if (isCollapsed) {\n      player.style.transform = 'translateY(-100%)';\n      player.style.pointerEvents = 'none';\n    } else {\n      player.style.transform = '';\n      player.style.pointerEvents = 'auto';\n    }\n    try { localStorage.setItem(STORAGE_PREFIX + 'collapsed', isCollapsed); } catch(e){}\n  });"
for p in glob.glob('repos/*/assets/js/music-player.js') + ['transhumanists.github.io/assets/js/music-player.js']:
    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
        s = f.read()
    if old_block in s:
        s = s.replace(old_block, new_block)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(s)
        print('Fixed toggle', p)
    else:
        print('Toggle block not found', p)
