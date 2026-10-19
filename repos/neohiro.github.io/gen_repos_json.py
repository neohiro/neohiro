import yaml
import json
from datetime import datetime

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

with open('_data/repos.yml') as f:
    data = yaml.safe_load(f)

# Sort by weight
data['repos'].sort(key=lambda x: x.get('weight', 99))

# Write to assets/data/repos.json
with open('assets/data/repos.json', 'w') as f:
    json.dump(data, f, indent=2, cls=DateTimeEncoder)

print("Generated assets/data/repos.json")