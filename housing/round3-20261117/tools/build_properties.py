"""Wave 0A: group in-scope SUUMO listings (snapshot ver2.0-20261102) into property candidates.
Key never uses price. Groups whose listings disagree on price are flagged, not split."""
import csv, hashlib, json, sys, unicodedata
from collections import defaultdict

src, out = sys.argv[1], sys.argv[2]
norm = lambda s: unicodedata.normalize('NFKC', s or '').replace(' ', '').strip()
num = lambda s: f'{float(s):.2f}' if s else ''

def key(r):
    base = (r['category'], norm(r['address']), r['built_year'], norm(r['layout']))
    if 'condo' in r['category']:
        return base + (num(r['unit_m2']), norm(r['advertised_structure']))
    return base + (num(r['land_m2']), num(r['building_m2']))

def weak(r):  # too few distinguishing fields to trust a merge
    if not r['address'] or not r['layout']: return True
    if 'condo' in r['category']: return not r['unit_m2']
    return not (r['land_m2'] and r['building_m2'])

rows = [r for r in json.load(open(src)) if r['scope_status'] == 'in_scope']
groups = defaultdict(list)
for r in rows:
    k = key(r)
    groups[k + ((r['listing_url'],) if weak(r) else ())].append(r)

props, links = [], []
for k, g in sorted(groups.items(), key=lambda x: str(x[0])):
    pid = 'p_' + hashlib.sha1('|'.join(k).encode()).hexdigest()[:12]
    prices = sorted({int(r['price_jpy']) for r in g})
    r = g[0]
    props.append({'property_id': pid, 'category': r['category'], 'ward': r['ward'], 'address': r['address'],
        'unit_m2': r['unit_m2'], 'land_m2': r['land_m2'], 'building_m2': r['building_m2'], 'layout': r['layout'],
        'built_year': r['built_year'], 'structure': r['advertised_structure'], 'station_raw': r['station_raw'],
        'listing_count': len(g), 'price_min_jpy': prices[0], 'price_max_jpy': prices[-1],
        'identity': 'weak_key_not_merged' if weak(r) else ('price_conflict' if len(prices) > 1 else 'ok'),
        'sources': 'suumo'})
    links += [{'property_id': pid, 'source': 'suumo', 'listing_url': x['listing_url'], 'price_jpy': x['price_jpy']} for x in g]

for name, data in (('properties.csv', props), ('listing-property-links.csv', links)):
    with open(f'{out}/{name}', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(data[0])); w.writeheader(); w.writerows(data)

from collections import Counter
summary = {'listings': len(rows), 'properties': len(props),
    'by_category': {c: {'listings': sum(1 for r in rows if r['category'] == c), 'properties': sum(1 for p in props if p['category'] == c)} for c in sorted({r['category'] for r in rows})},
    'identity': dict(Counter(p['identity'] for p in props)),
    'listing_count_distribution': dict(sorted(Counter(min(p['listing_count'], 5) for p in props).items()))}
json.dump(summary, open(f'{out}/summary.json', 'w'), indent=1, ensure_ascii=False); print(json.dumps(summary, ensure_ascii=False, indent=1))
assert len(links) == len(rows) == sum(p['listing_count'] for p in props)
