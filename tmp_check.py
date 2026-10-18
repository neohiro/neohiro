content = open('pages-site/index.html', encoding='utf-8').read()
print('Cards:', content.count('<div class="card"'))
print('Stars:', content.count('class="stars"'))
import json
j = json.load(open('repos/neohiro.github.io/assets/data/repos.json'))
repos = j.get('repos', [])
print('Repos in JSON:', len(repos))
featured = [r for r in repos if r.get('featured')]
print('Featured repos:', len(featured))
for r in featured:
    print(' -', r['name'], 'stars:', r.get('stars'))
