import json

with open('data/hifld_primary_raw.json', 'r') as f:
    hifld = json.load(f)
    for feat in hifld:
        attrs = feat.get('attributes', {})
        if 'BEAUMONT' in str(attrs.get('NAME', '')).upper():
            print("HIFLD:", attrs.get('NAME'), attrs.get('WEBSITE'))

with open('data/bop_raw.json', 'r') as f:
    bop = json.load(f).get('Locations', [])
    for b in bop:
        if 'BEAUMONT' in str(b.get('name', '')).upper() or 'BEAUMONT' in str(b.get('nameTitle', '')).upper():
            print("BOP:", b.get('code'), b.get('nameTitle'), b.get('url'))
