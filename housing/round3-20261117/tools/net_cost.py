"""HOUSING-SELECTION-4.0: net monthly cost of living per property.
net_cost = (price*(1+buy) - residual*(1-sell)) / months + recurring
condo residual = price x (area price of stock `hold_years` older / area price of same-age stock)
house residual = land area x land price proxy; never above the purchase price.
Usage: net_cost.py <listing-data.json> <wave0 dir> <policy.json> <out dir>"""
import csv, json, re, statistics as st, sys, unicodedata
from collections import Counter, defaultdict

src, w0, pol_path, out = sys.argv[1:5]
P = json.load(open(pol_path)); H = P['hold_years']; WIN = P['comparison_year_window']; LO, HI = P['comparison_area_ratio']; NMIN = P['min_comparison_groups']
rows = json.load(open(src)); snap_year = int(rows[0]['observed_at'][:4])
norm = lambda s: unicodedata.normalize('NFKC', s or '').replace(' ', '')
def station(r):
    m = re.search(r'「([^」]+)」', r['station_raw'] or ''); return norm(m.group(1)) if m else ''
num = lambda s: float(s) if s else None

# ---- comparison pools, one entry per property-like group (price never part of the key)
condo_pool = {}
for r in rows:
    if r['category'] == 'used_condo' and r['price_jpy'] and r['unit_m2'] and r['built_year'] and r['availability'] not in ('not_found', 'expired'):
        condo_pool.setdefault((norm(r['address']), r['unit_m2'], r['built_year'], norm(r['layout'])), (r['ward'], station(r), int(r['built_year']), float(r['unit_m2']), int(r['price_jpy']) / float(r['unit_m2'])))
condo_pool = list(condo_pool.values())
land_pool = defaultdict(dict)
for r in rows:
    if r['category'] == 'used_house' and r['price_jpy'] and r['land_m2'] and r['built_year'] and int(r['built_year']) <= snap_year - P['old_house_min_age_for_land_proxy'] and float(r['land_m2']) >= 30:
        land_pool[r['ward']].setdefault(((norm(r['address']), r['land_m2'], r['built_year']), station(r)), int(r['price_jpy']) / float(r['land_m2']))

def condo_keep(ward, stn, year, area):
    """Share of today's price that comparable stock `hold_years` older still fetches in the same area.
    Applied to the target's own price, so the unit keeps its premium or discount against its neighbours."""
    size = [p for p in condo_pool if LO * area <= p[3] <= HI * area]
    best = 0
    for level, sel in (('station', [p for p in size if stn and p[1] == stn and p[0] == ward]), ('ward', [p for p in size if p[0] == ward])):
        same = [p[4] for p in sel if abs(p[2] - year) <= WIN]; older = [p[4] for p in sel if abs(p[2] - (year - H)) <= WIN]
        best = max(best, min(len(same), len(older)))
        if len(same) >= NMIN and len(older) >= NMIN: return min(1.0, st.median(older) / st.median(same)), level, min(len(same), len(older))
    return None, 'insufficient_comparables', best
def house_residual(ward, stn, land, own_key):
    """Land value proxy: asking price per land m2 of houses old enough that the building carries little value."""
    for level, v, need in (('station_old_house_land_proxy', [x for (k, s_), x in land_pool[ward].items() if s_ == stn and stn and k != own_key], P['min_land_groups_station']),
                           ('ward_old_house_land_proxy_coarse', [x for (k, s_), x in land_pool[ward].items() if k != own_key], NMIN)):
        if len(v) >= need: return st.median(v) * land, level, len(v)
    return None, 'insufficient_comparables', len(land_pool[ward])

# ---- targets: property table from wave 0
by_url = {r['listing_url']: r for r in rows}
links = defaultdict(list)
for l in csv.DictReader(open(f'{w0}/listing-property-links.csv')): links[l['property_id']].append(by_url[l['listing_url']])
res = []
for p in csv.DictReader(open(f'{w0}/properties.csv')):
    L = links[p['property_id']]; r0 = L[0]; cat = p['category']; price = int(p['price_min_jpy']); year = int(p['built_year']) if p['built_year'] else None
    rights = next((x['advertised_rights'] for x in L if x['advertised_rights']), '')
    queues = {x['selection_queue'] for x in L}; flags = set()
    for x in L: flags |= set(json.loads(x.get('conditional_flags') or '[]')) | set(json.loads(x.get('flags') or '[]'))
    reasons = []
    if queues - {'ORDINARY'}: reasons.append('queue:' + '/'.join(sorted(queues - {'ORDINARY'})))
    if rights and '所有権' not in rights: reasons.append('rights_not_freehold')
    if any('leasehold' in f for f in flags): reasons.append('leasehold_claim')
    if any('terrace' in f for f in flags): reasons.append('terrace_claim')
    if any('rebuild' in f for f in flags): reasons.append('rebuild_claim')
    if year and year <= P['old_seismic_built_year_max']: reasons.append('built_before_1982')
    if p['identity'] != 'ok': reasons.append('identity:' + p['identity'])
    hard = [x for x in reasons if not x.startswith('identity')]
    o = {'property_id': p['property_id'], 'category': cat, 'ward': p['ward'], 'address': p['address'], 'station_raw': p['station_raw'], 'layout': p['layout'], 'built_year': p['built_year'],
         'unit_m2': p['unit_m2'], 'land_m2': p['land_m2'], 'building_m2': p['building_m2'], 'price_jpy': price, 'listing_count': p['listing_count'],
         'gate': 'separate_review' if hard else 'ordinary', 'gate_reasons': ';'.join(reasons), 'url': r0['listing_url']}
    recurring = None; note = []
    if 'condo' in cat:
        area = num(p['unit_m2']); living = area
        keep, basis, n = condo_keep(p['ward'], station(r0), year, area) if year and area else (None, 'missing_year_or_area', 0)
        resid = keep * price if keep is not None else None
        fee = None
        for x in L:
            f = json.loads(x.get('advertised_fees') or '{}'); v = [(f.get(k, {}).get('value') or {}) for k in ('management_fee', 'repair_fee')]
            if all(i.get('amount_jpy') and i.get('period') == 'month' for i in v): fee = sum(i['amount_jpy'] for i in v); break
        recurring = fee; o['recurring_basis'] = 'advertised_management_and_repair_fee' if fee else 'fees_unknown'
    else:
        land, living = num(p['land_m2']), num(p['building_m2'])
        resid, basis, n = house_residual(p['ward'], station(r0), land, (norm(p['address']), p['land_m2'], p['built_year'])) if land else (None, 'missing_land_area', 0)
        recurring = P['house_maintenance_jpy_per_building_m2_month'] * living if living else None; o['recurring_basis'] = 'assumed_maintenance_allowance' if living else 'building_area_unknown'
        if year and snap_year - year >= 25: note.append('renovation_cost_not_included')
        if not year: note.append('new_build_year_unknown')
    o.update(residual_basis=basis, comparison_groups=n, recurring_jpy_month=recurring or '')
    if resid is not None:
        if resid >= price: note.append('residual_capped_at_price')
        resid = min(resid, price); months = H * 12
        cost = lambda rv: (price * (1 + P['buy_cost_rate']) - rv * (1 - P['sell_cost_rate'])) / months
        o.update(residual_jpy=round(resid), keep_ratio=round(resid / price, 3), capital_cost_jpy_month=round(cost(resid)))
        if recurring is not None and living:
            o.update(net_cost_jpy_month=round(cost(resid) + recurring), net_cost_stress_jpy_month=round(cost(resid * P['stress_residual_factor']) + recurring), net_cost_jpy_m2_month=round((cost(resid) + recurring) / living))
    o['notes'] = ';'.join(note); res.append(o)

# ---- bands within each category, ordinary gate only
for cat in {o['category'] for o in res}:
    for o in res:  # a land estimate at or above the asking price cannot be ranked: the proxy is too coarse for that lot
        if o['category'] == cat and 'residual_capped_at_price' in o['notes']: o.pop('net_cost_jpy_m2_month', None); o['residual_basis'] = 'land_estimate_exceeds_price'
    v = sorted(o['net_cost_jpy_m2_month'] for o in res if o['category'] == cat and o['gate'] == 'ordinary' and 'net_cost_jpy_m2_month' in o)
    q = st.quantiles(v, n=4) if len(v) >= 8 else None
    for o in res:
        if o['category'] != cat: continue
        c = o.get('net_cost_jpy_m2_month')
        o['band'] = 'S' if o['gate'] != 'ordinary' else 'U' if c is None or not q else 'A' if c <= q[0] else 'B' if c <= q[1] else 'C' if c <= q[2] else 'D'
cols = ['band', 'category', 'ward', 'address', 'station_raw', 'layout', 'built_year', 'unit_m2', 'land_m2', 'building_m2', 'price_jpy', 'net_cost_jpy_m2_month', 'net_cost_jpy_month', 'net_cost_stress_jpy_month', 'keep_ratio', 'residual_jpy', 'capital_cost_jpy_month', 'recurring_jpy_month', 'recurring_basis', 'residual_basis', 'comparison_groups', 'gate', 'gate_reasons', 'notes', 'listing_count', 'property_id', 'url']
order = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'U': 4, 'S': 5}
res.sort(key=lambda o: (o['category'], order[o['band']], o.get('net_cost_jpy_m2_month', 1e9)))
with open(f'{out}/net-cost.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore'); w.writeheader(); w.writerows(res)
def qs(v): return [round(x) for x in st.quantiles(v, n=4)] if len(v) >= 8 else None
summ = {'policy_version': P['policy_version'], 'price_basis': P['price_basis'], 'properties': len(res), 'comparison_pool': {'used_condo_groups': len(condo_pool), 'old_house_land_groups': sum(len(v) for v in land_pool.values())}, 'by_category': {}}
for cat in sorted({o['category'] for o in res}):
    c = [o for o in res if o['category'] == cat]; k = [o for o in c if o['band'] in 'ABCD']
    summ['by_category'][cat] = {'properties': len(c), 'bands': dict(sorted(Counter(o['band'] for o in c).items())), 'separate_review_reasons': dict(Counter(x for o in c if o['band'] == 'S' for x in o['gate_reasons'].split(';') if not x.startswith('identity')).most_common()),
        'unknown_reasons': dict(Counter((o['residual_basis'] if 'residual_jpy' not in o or o['residual_basis'] == 'land_estimate_exceeds_price' else o['recurring_basis']) for o in c if o['band'] == 'U').most_common()),
        'residual_basis': dict(Counter(o['residual_basis'] for o in k).most_common()),
        'net_cost_jpy_month_quartiles': qs([o['net_cost_jpy_month'] for o in k]), 'net_cost_jpy_m2_month_quartiles': qs([o['net_cost_jpy_m2_month'] for o in k]), 'keep_ratio_quartiles': [round(x, 2) for x in st.quantiles([o['keep_ratio'] for o in k], n=4)] if len(k) >= 8 else None}
json.dump(summ, open(f'{out}/summary.json', 'w'), ensure_ascii=False, indent=1); print(json.dumps(summ, ensure_ascii=False, indent=1))
assert len(res) == sum(1 for _ in open(f'{w0}/properties.csv')) - 1
