import json, subprocess
q = {"query": 'query { repository(owner:"neohiro", name:"BlackGlass") { id discussionCategories(first:10){ nodes { id name } } } }'}
p = subprocess.run(["gh", "api", "graphql"], input=json.dumps(q),
                   capture_output=True, text=True, encoding="utf-8")
print("rc:", p.returncode)
print(p.stdout[:500])
print("ERR:", p.stderr[:300])
