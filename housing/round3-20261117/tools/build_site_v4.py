"""Build the static site version housing-selection-v4-<date> from round 3 outputs.
Usage: build_site_v4.py <housing dir> <version name>"""
import csv, hashlib, json, os, re, shutil, sys, unicodedata
from collections import Counter

H, VER = sys.argv[1], sys.argv[2]
R = os.path.join(H, 'round3-20261117'); OUT = os.path.join(H, VER); os.makedirs(OUT, exist_ok=True)
rd = lambda p: list(csv.DictReader(open(os.path.join(R, p), encoding='utf-8-sig')))
norm = lambda s: unicodedata.normalize('NFKC', s or '')
def walk(s):
    v = [int(x) for x in re.findall(r'(?:徒歩|歩)\s*(\d+)\s*分', norm(s))]; return min(v) if v else None
num = lambda s: float(s) if s not in (None, '') else None
def intn(s):
    try: return int(float(s))
    except (TypeError, ValueError): return None
ward = lambda a: (re.search(r'大阪市(\S+?区)', a or '') or [None, ''])[1]
rows = []
def add(**k):
    k['walk_minutes'] = walk(k.get('station_raw')); rows.append({x: y for x, y in k.items() if y not in (None, '')})

for r in rd('selection4/net-cost.csv'):  # 02/11 snapshot; new houses come from the fresher 17/11 detail run below
    if r['category'] == 'new_house': continue
    add(id=r['property_id'], source='suumo', snapshot='2026-11-02', category=r['category'], band=r['band'], ward=r['ward'], address=r['address'], station_raw=r['station_raw'], layout=r['layout'],
        built=r['built_year'], unit_m2=num(r['unit_m2']), land_m2=num(r['land_m2']), building_m2=num(r['building_m2']), price_min=intn(r['price_jpy']), price_max=intn(r['price_jpy']),
        net_m2=intn(r['net_cost_jpy_m2_month']), net_month=intn(r['net_cost_jpy_month']), net_stress=intn(r['net_cost_stress_jpy_month']), keep=num(r['keep_ratio']), recurring=intn(r['recurring_jpy_month']),
        recurring_basis=r['recurring_basis'], residual_basis=r['residual_basis'], groups=intn(r['comparison_groups']), reasons=';'.join(x for x in (r['gate_reasons'], r['notes']) if x), listing_count=intn(r['listing_count']), url=r['url'])
for r in rd('selection4/net-cost-new-house.csv'):
    add(id='nh_' + hashlib.sha1(r['url'].encode()).hexdigest()[:10], source='suumo', snapshot='2026-11-17', category='new_house', band=r['band'], ward=r['ward'], address=r['address'], name=r['project_name'], station_raw=r['station_raw'],
        layout=r['layout'], built=r['completion_raw'], build_status=r['build_status'], land_m2=num(r['land_m2']), building_m2=num(r['building_m2']), price_min=intn(r['price_jpy']), price_max=intn(r['price_jpy']),
        net_m2=intn(r['net_cost_jpy_m2_month']), net_month=intn(r['net_cost_jpy_month']), net_stress=intn(r['net_cost_stress_jpy_month']), keep=num(r['keep_ratio']), recurring=intn(r['recurring_jpy_month']),
        residual_basis=r['residual_basis'], groups=intn(r['comparison_groups']), seller=r['transaction_type'], no_brokerage=r['no_brokerage_fee'] != 'no', reasons=';'.join(x for x in (r['gate_reasons'], r['notes']) if x),
        listing_count=intn(r['listing_count']), url=r['url'], other_urls=r['other_urls'])
for r in rd('selection4/new-condo-projects.csv'):
    proj = r['kind'] == 'project'
    add(id='nc_' + hashlib.sha1(r['url'].encode()).hexdigest()[:10], source='suumo', snapshot='2026-11-17', category='new_condo_project' if proj else 'new_condo_unit', band='P' if proj else 'U', ward=r['ward'], address=r['address'],
        name=r['project_name'], station_raw=r['station_raw'], price_raw=r['price_raw'], price_min=intn(r['price_min_jpy']), price_max=intn(r['price_max_jpy']), unit_m2=num(r['area_min_m2']), unit_m2_max=num(r['area_max_m2']),
        fees_m2=intn(r['fees_jpy_m2_month']), fees_min=intn(r['fees_month_min_jpy']), fees_max=intn(r['fees_month_max_jpy']), keep=num(r['area_keep_ratio_20y']), residual_basis=r['keep_basis'],
        net_month=intn(r['net_cost_jpy_month']), net_m2=intn(r['net_cost_jpy_m2_month']), net_stress=intn(r['net_cost_stress_jpy_month']),
        units_total=r['units_total'], built=r['completion_raw'], handover=r['handover_raw'], build_status=r['build_status'], watch=r['watch'], url=r['url'])
for r in rd('wave3/data/details-yahoo.csv'):
    proj = r['target_type'] == 'new_condo_project'
    add(id='y_' + hashlib.sha1(r['url'].encode()).hexdigest()[:10], source='yahoo', snapshot='2026-11-17', category='new_condo_project' if proj else 'new_house', band='P' if proj else 'N', ward=ward(r['address']), address=r['address'],
        name=r['project_name'], station_raw=r['station_raw'], price_raw=r['price_raw'][:80], price_min=intn(r['price_min_man']) and intn(r['price_min_man']) * 10000, price_max=intn(r['price_max_man']) and intn(r['price_max_man']) * 10000,
        layout=r['layout_raw'], built=r['completion_raw'], handover=r['handover_raw'], seller=r['transaction_type_raw'], units_total=r['units_total'],
        watch=('price_undisclosed' if not r['price_min_man'] else 'fees_undisclosed' if proj and not r['management_fee_raw'] else ''), url=r['url'])
seen_y = {r['url'] for r in rows if r['source'] == 'yahoo'}
for r in rd('wave2/data/new-properties.csv'):
    urls = r['urls'].split(); u = urls[0]
    if u in seen_y: continue
    add(id='x_' + hashlib.sha1(u.encode()).hexdigest()[:10], source=r['sources'], snapshot='2026-11-17', category=r['category'], band='N', ward=r['ward'], address=r['address'], name=r['building_name'], station_raw=r['station_raw'],
        layout=r['layout'], built=r['built_year'], floor=r['floor'], unit_m2=num(r['unit_m2']), land_m2=num(r['land_m2']), building_m2=num(r['building_m2']), price_min=intn(r['price_min_jpy']), price_max=intn(r['price_max_jpy']),
        suumo_status=r['suumo_status'], suumo_prices=r['suumo_prices'], listing_count=intn(r['listing_count']), url=u, other_urls=' '.join(urls[1:]))

json.dump({'version': VER, 'policy_version': 'HOUSING-SELECTION-4.0', 'rows': rows}, open(os.path.join(OUT, 'listing-data.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
summary = {'rows': len(rows), 'by_category_band': {c: dict(sorted(Counter(r['band'] for r in rows if r['category'] == c).items())) for c in sorted({r['category'] for r in rows})}, 'by_source': dict(Counter(r['source'] for r in rows))}
for f in ('index.html', 'view.js', 'downloads.html'): shutil.copy(os.path.join(R, 'tools', 'site_v4', f), os.path.join(OUT, f))
files = {}
for root, _, fs in os.walk(OUT):
    for f in sorted(fs):
        if f == 'MANIFEST.json': continue
        p = os.path.join(root, f); b = open(p, 'rb').read(); files[os.path.relpath(p, OUT)] = {'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}
json.dump({'version': VER, 'summary': summary, 'files': files}, open(os.path.join(OUT, 'MANIFEST.json'), 'w'), ensure_ascii=False, indent=1)
print(json.dumps(summary, ensure_ascii=False, indent=1))
