import json

with open('data/hifld_primary_raw.json', 'r') as f:
    data = json.load(f)

for feat in data:
    attrs = feat.get('attributes', {})
    if attrs.get('NAME') == 'FULTON COUNTY JAIL':
        print('Raw FULTON COUNTY JAIL:', attrs.get('CAPACITY'), attrs.get('POPULATION'))
