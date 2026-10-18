import glob
old = """        const enclosures = Array.from(doc.querySelectorAll('enclosure[url]'));
        if (enclosures.length) {
          const best = enclosures[0].getAttribute('url');
          if (best && best.includes('.mp3')) {
            track.streamUrl = best;
            track.name = 'Neohiro Mix — Portfolio';
            trackTitle.textContent = track.name;
          }
        }"""
new = """        const items = Array.from(doc.querySelectorAll('item'));
        for (const item of items) {
          const enc = item.querySelector('enclosure[url]');
          if (enc) {
            const url = enc.getAttribute('url');
            if (url && url.includes('.mp3')) {
              track.streamUrl = url;
              const titleEl = item.querySelector('title');
              const realName = titleEl ? titleEl.textContent.trim() : 'Neohiro Mix';
              track.name = realName;
              trackTitle.textContent = realName;
              break;
            }
          }
        }"""
for f in glob.glob('repos/transhumanists.github.io/assets/js/music-player.js') + glob.glob('repos/openstageisland.github.io/assets/js/music-player.js'):
    s = open(f, encoding='utf-8').read()
    s = s.replace(old, new)
    open(f, 'w', encoding='utf-8').write(s)
    print('fixed', f)
