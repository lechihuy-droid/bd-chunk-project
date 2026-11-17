"""Match non-SUUMO listings against the SUUMO property table and the full SUUMO catalogue.
Usage: merge_sources.py <suumo listing-data.json> <workdir with listings-*.csv> <out summary.json>
Writes <workdir>/merged-listings.csv and <workdir>/new-properties.csv (kept out of git)."""
import csv, glob, json, os, re, sys, unicodedata
from collections import Counter, defaultdict

def addr(a):
    a = unicodedata.normalize('NFKC', a or '').replace('大阪府', '').replace(' ', '')
    a = re.sub(r'(\d+)丁目.*', r'\1', a); return re.sub(r'(\d+)[-−ー].*', r'\1', a)
f2 = lambda s: f'{float(s):.2f}' if s else ''
kind = lambda c: 'condo' if 'condo' in c else 'house'
def base(r):  # identity without price and without floor
    return (kind(r['category']), addr(r['address'])) + ((f2(r['unit_m2']),) if kind(r['category']) == 'condo' else (f2(r['land_m2']), f2(r['building_m2'])))
def loose(r):  # ward + exact areas + year, for sources that print the address at a different precision
    return (kind(r['category']), r['ward']) + base(r)[2:] + (str(r['built_year'] or ''),)

suumo = json.load(open(sys.argv[1])); work = sys.argv[2]
in_scope = [r for r in suumo if r['scope_status'] == 'in_scope']
idx_in = {base(r) for r in in_scope}; idx_in_loose = {loose(r) for r in in_scope if r['built_year']}
others = [r for r in suumo if r['scope_status'] != 'in_scope' and r['price_jpy']]
idx_out = defaultdict(set)
for r in others: idx_out[base(r)].add(r['price_raw'])

rows = []
for f in sorted(glob.glob(os.path.join(work, 'listings-*.csv'))): rows += list(csv.DictReader(open(f, encoding='utf-8')))
for r in rows:
    b = base(r)
    if b in idx_in: r['suumo_status'] = 'in_suumo_band'
    elif r['built_year'] and loose(r) in idx_in_loose: r['suumo_status'] = 'in_suumo_band_probable'
    elif b in idx_out: r['suumo_status'] = 'in_suumo_other_price'; r['suumo_prices'] = '/'.join(sorted(idx_out[b])[:4])
    else: r['suumo_status'] = 'not_in_suumo'
    r.setdefault('suumo_prices', '')

# property groups across the non-SUUMO sources (floor splits a group only when every member states one)
groups = defaultdict(list)
for r in rows: groups[base(r)].append(r)
props = []
for b, g in groups.items():
    floors = {r['floor'] for r in g}
    parts = defaultdict(list)
    for r in g: parts[r['floor'] if '' not in floors else ''].append(r)
    for fl, m in parts.items():
        st = Counter(r['suumo_status'] for r in m).most_common(1)[0][0]; prices = sorted({int(r['price_jpy']) for r in m}); r = m[0]
        props.append({'kind': b[0], 'category': r['category'], 'ward': r['ward'], 'address': r['address'], 'building_name': next((x['building_name'] for x in m if x['building_name']), ''), 'floor': fl,
            'unit_m2': r['unit_m2'], 'land_m2': r['land_m2'], 'building_m2': r['building_m2'], 'layout': r['layout'], 'built_year': r['built_year'], 'station_raw': next((x['station_raw'] for x in m if x['station_raw']), ''),
            'price_min_jpy': prices[0], 'price_max_jpy': prices[-1], 'sources': '+'.join(sorted({x['source'] for x in m})), 'listing_count': len(m), 'suumo_status': st, 'suumo_prices': r['suumo_prices'], 'urls': ' '.join(x['listing_url'] for x in m)})

def dump(name, data):
    with open(os.path.join(work, name), 'w', newline='', encoding='utf-8') as o:
        w = csv.DictWriter(o, fieldnames=list(data[0])); w.writeheader(); w.writerows(data)
dump('merged-listings.csv', rows)
new = sorted([p for p in props if p['suumo_status'] in ('not_in_suumo', 'in_suumo_other_price')], key=lambda p: (p['suumo_status'], p['category'], p['ward'], p['price_min_jpy']))
dump('new-properties.csv', new)

tab = lambda items, key: {k: dict(sorted(Counter(i['suumo_status'] for i in items if key(i) == k).items())) for k in sorted({key(i) for i in items})}
summary = {'suumo_in_scope_listings': len(in_scope), 'non_suumo_listings': len(rows), 'non_suumo_properties': len(props),
    'properties_by_status': dict(sorted(Counter(p['suumo_status'] for p in props).items())),
    'properties_by_kind': tab(props, lambda p: p['category']),
    'listings_by_source': tab(rows, lambda r: r['source']),
    'properties_seen_by_n_sources': dict(sorted(Counter(len(p['sources'].split('+')) for p in props).items())),
    'new_properties_by_ward': dict(Counter(p['ward'] for p in new if p['suumo_status'] == 'not_in_suumo').most_common())}
json.dump(summary, open(sys.argv[3], 'w'), ensure_ascii=False, indent=1); print(json.dumps(summary, ensure_ascii=False, indent=1))
