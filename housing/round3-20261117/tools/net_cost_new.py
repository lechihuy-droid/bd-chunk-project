"""HOUSING-SELECTION-4.0 applied to new builds (SUUMO detail pages, wave 3).
New houses: same formula as net_cost.py; residual = land area x land-price proxy from old houses;
buy cost drops the brokerage fee when the seller sells directly or the page states the fee is waived.
New condos: project-level indicators only (keep ratio of the area, fee per m2, status); no ranking,
because price lists give ranges and do not tie a price to a unit area.
Usage: net_cost_new.py <listing-data.json> <details-suumo.csv> <policy.json> <out dir>"""
import csv, json, re, statistics as st, sys, unicodedata
from collections import Counter, defaultdict

src, det, pol_path, out = sys.argv[1:5]
P = json.load(open(pol_path)); H = P['hold_years']; WIN = P['comparison_year_window']; NMIN = P['min_comparison_groups']; LO, HI = P['comparison_area_ratio']
rows = json.load(open(src)); D = list(csv.DictReader(open(det, encoding='utf-8-sig')))
NOW = (2026, 11)
norm = lambda s: unicodedata.normalize('NFKC', s or '').replace(' ', '')
def station(s):
    m = re.search(r'「([^」]+)」', s or ''); return norm(m.group(1)) if m else ''
ward = lambda a: (re.search(r'大阪市(\S+?区)', a or '') or [None, ''])[1]
def first_m2(s):
    m = re.search(r'([\d.]+)\s*m2', norm(s)); return float(m.group(1)) if m else None
def yen_list(s):
    s = norm(s); out = []
    for m in re.finditer(r'(?:(\d+)万)?(\d[\d,]*)?円', s):
        if m.group(1) or m.group(2): out.append(int(m.group(1) or 0) * 10000 + int((m.group(2) or '0').replace(',', '')))
    return out
def ym(s):
    m = re.search(r'(\d{4})年(\d{1,2})月', s or ''); return (int(m.group(1)), int(m.group(2))) if m else None
def build_status(s):
    v = ym(s)
    if not v: return 'after_contract' if '契約後' in (s or '') else 'unknown'
    return 'completed' if v < NOW else 'completing_this_month' if v == NOW else 'future'
def no_brokerage(r):
    t = r['transaction_type_raw'] + ' ' + r['other_fees_raw']
    if re.search(r'仲介手数料[::]?(無料|不要|なし)', t): return 'fee_waived_stated'
    if '仲介' in r['transaction_type_raw'] or '媒介' in r['transaction_type_raw']: return ''
    if re.search(r'売主|販売提携|代理', r['transaction_type_raw']): return 'direct_or_agent'
    return ''
brokerage = lambda price: (price * 0.03 + 60000) * 1.10

# ---- comparison pools from the 02/11 catalogue (same as net_cost.py)
snap_year = int(rows[0]['observed_at'][:4])
land_pool = defaultdict(dict)
for r in rows:
    if r['category'] == 'used_house' and r['price_jpy'] and r['land_m2'] and r['built_year'] and int(r['built_year']) <= snap_year - P['old_house_min_age_for_land_proxy'] and float(r['land_m2']) >= 30:
        land_pool[r['ward']].setdefault(((norm(r['address']), r['land_m2'], r['built_year']), station(r['station_raw'])), int(r['price_jpy']) / float(r['land_m2']))
condo_pool = {}
for r in rows:
    if r['category'] == 'used_condo' and r['price_jpy'] and r['unit_m2'] and r['built_year'] and r['availability'] not in ('not_found', 'expired'):
        condo_pool.setdefault((norm(r['address']), r['unit_m2'], r['built_year'], norm(r['layout'])), (r['ward'], station(r['station_raw']), int(r['built_year']), float(r['unit_m2']), int(r['price_jpy']) / float(r['unit_m2'])))
condo_pool = list(condo_pool.values())

def land_value(w, stn, land):
    for level, v, need in (('station_old_house_land_proxy', [x for (k, s_), x in land_pool[w].items() if s_ == stn and stn], P['min_land_groups_station']),
                           ('ward_old_house_land_proxy_coarse', list(land_pool[w].values()), NMIN)):
        if len(v) >= need: return st.median(v) * land, level, len(v)
    return None, 'insufficient_comparables', len(land_pool[w])
def condo_keep(w, stn, year, area=None):
    """older (year-H) vs near-new (built within near_new years of `year`) price per m2 in the same area."""
    size = [p for p in condo_pool if area is None or LO * area <= p[3] <= HI * area]
    for level, sel in (('station', [p for p in size if stn and p[1] == stn and p[0] == w]), ('ward', [p for p in size if p[0] == w])):
        new = [p[4] for p in sel if year - P['near_new_condo_max_age_years'] <= p[2]]; old = [p[4] for p in sel if abs(p[2] - (year - H)) <= WIN]
        if len(new) >= NMIN and len(old) >= NMIN: return min(1.0, st.median(old) / st.median(new)), level, min(len(new), len(old))
    return None, 'insufficient_comparables', 0

months = H * 12
# ---- new houses
houses = []
for r in D:
    if r['target_type'] != 'new_house': continue
    w = ward(r['address']); stn = station(r['station_raw']); price_lo = int(r['price_min_man'] or 0) * 10000; price_hi = int(r['price_max_man'] or 0) * 10000
    land = first_m2(r['land_area_raw']); bld = first_m2(r['unit_or_building_area_raw'])
    nb = no_brokerage(r); status = build_status(r['completion_raw'])
    o = {'band': '', 'ward': w, 'address': r['address'], 'project_name': r['project_name'], 'station_raw': r['station_raw'][:80], 'price_jpy': price_lo, 'land_m2': land or '', 'building_m2': bld or '',
         'layout': r['layout_raw'], 'completion_raw': r['completion_raw'], 'build_status': status, 'transaction_type': r['transaction_type_raw'], 'no_brokerage_fee': nb or 'no',
         'land_rights': r['land_rights_raw'], 'road_raw': r['road_raw'][:80], 'gate': 'ordinary', 'gate_reasons': '', 'notes': '', 'url': r['url']}
    reasons = []
    if r['land_rights_raw'] and '所有権' not in r['land_rights_raw']: reasons.append('rights_not_freehold')
    if price_lo != price_hi or re.search(r'[~・]', norm(r['land_area_raw'])): o['notes'] = 'multi_lot_entry'
    if reasons: o.update(gate='separate_review', gate_reasons=';'.join(reasons))
    if price_lo and land and bld and not o['notes']:
        resid, basis, n = land_value(w, stn, land)
        o.update(residual_basis=basis, comparison_groups=n)
        if resid is not None:
            if resid >= price_lo: o['notes'] = 'land_estimate_exceeds_price'
            else:
                buy = price_lo * P['buy_cost_rate'] - (brokerage(price_lo) if nb else 0)
                cap = lambda rv: (price_lo + buy - rv * (1 - P['sell_cost_rate'])) / months
                rec = P['house_maintenance_jpy_per_building_m2_month'] * bld
                o.update(residual_jpy=round(resid), keep_ratio=round(resid / price_lo, 3), buy_cost_jpy=round(buy), recurring_jpy_month=round(rec),
                         net_cost_jpy_month=round(cap(resid) + rec), net_cost_stress_jpy_month=round(cap(resid * P['stress_residual_factor']) + rec), net_cost_jpy_m2_month=round((cap(resid) + rec) / bld))
    houses.append(o)
# one row per house: several brokers often list the same new house (same block, land and building area)
def hkey(o):
    a = re.sub(r'(\d+)(丁目)?$', r'\1', norm(o['address']).replace('大阪府', '')); a = re.sub(r'(\d+)[-番].*', r'\1', a)
    return (a, o['land_m2'], o['building_m2']) if o['land_m2'] and o['building_m2'] and not o['notes'] == 'multi_lot_entry' else ('url', o['url'])
grp = defaultdict(list)
for o in houses: grp[hkey(o)].append(o)
houses = []
for g in grp.values():
    g.sort(key=lambda o: (o['price_jpy'] or 1e12, o['no_brokerage_fee'] == 'no'))
    best = dict(g[0]); best['listing_count'] = len(g); best['other_urls'] = ' '.join(o['url'] for o in g[1:])
    if any(o['no_brokerage_fee'] != 'no' for o in g) and best['no_brokerage_fee'] == 'no': best['notes'] = (best['notes'] + ';cheaper_route_has_no_brokerage_listing').strip(';')
    houses.append(best)
inb = lambda o: o['price_jpy'] and 40000000 <= o['price_jpy'] <= 50000000
v = sorted(o['net_cost_jpy_m2_month'] for o in houses if o['gate'] == 'ordinary' and 'net_cost_jpy_m2_month' in o and inb(o))
q = st.quantiles(v, n=4)
for o in houses:
    c = o.get('net_cost_jpy_m2_month')
    o['band'] = 'S' if o['gate'] != 'ordinary' else 'U' if c is None or not inb(o) else 'A' if c <= q[0] else 'B' if c <= q[1] else 'C' if c <= q[2] else 'D'
order = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'U': 4, 'S': 5}
houses.sort(key=lambda o: (order[o['band']], o.get('net_cost_jpy_m2_month', 1e9)))
hcols = ['band', 'ward', 'address', 'project_name', 'station_raw', 'price_jpy', 'land_m2', 'building_m2', 'layout', 'net_cost_jpy_m2_month', 'net_cost_jpy_month', 'net_cost_stress_jpy_month', 'keep_ratio', 'residual_jpy', 'buy_cost_jpy', 'recurring_jpy_month', 'residual_basis', 'comparison_groups',
         'completion_raw', 'build_status', 'transaction_type', 'no_brokerage_fee', 'land_rights', 'road_raw', 'gate', 'gate_reasons', 'notes', 'listing_count', 'url', 'other_urls']
with open(f'{out}/net-cost-new-house.csv', 'w', newline='', encoding='utf-8') as f:
    w_ = csv.DictWriter(f, fieldnames=hcols, extrasaction='ignore'); w_.writeheader(); w_.writerows(houses)

# ---- new condos
condos = []
for r in D:
    if r['target_type'] != 'new_condo_project': continue
    w = ward(r['address']); stn = station(r['station_raw']); comp = ym(r['completion_raw']); year = comp[0] if comp else None
    unit = '仲介' in r['transaction_type_raw']
    areas = [float(x) for x in re.findall(r'([\d.]+)\s*m2', norm(r['unit_or_building_area_raw']).split('、')[0])]
    mg, rp = yen_list(r['management_fee_raw']), yen_list(r['repair_reserve_raw'])
    fee_lo = (mg[0] + rp[0]) if mg and rp else None; fee_hi = (mg[-1] + rp[-1]) if mg and rp else None
    plo = int(r['price_min_man']) * 10000 if r['price_min_man'] else None; phi = int(r['price_max_man']) * 10000 if r['price_max_man'] else None
    keep, basis, n = condo_keep(w, stn, year, areas[0] if unit and areas else None) if year else (None, 'completion_unknown', 0)
    o = {'kind': 'unsold_unit_via_broker' if unit else 'project', 'ward': w, 'project_name': r['project_name'], 'address': r['address'], 'station_raw': r['station_raw'][:80],
         'price_raw': r['price_raw'][:60], 'price_min_jpy': plo or '', 'price_max_jpy': phi or '', 'area_min_m2': areas[0] if areas else '', 'area_max_m2': areas[-1] if areas else '',
         'fees_month_min_jpy': fee_lo or '', 'fees_month_max_jpy': fee_hi or '', 'fees_jpy_m2_month': round(fee_lo / areas[0]) if fee_lo and areas else '',
         'units_total': r['units_total'], 'completion_raw': r['completion_raw'], 'handover_raw': r['handover_raw'], 'build_status': build_status(r['completion_raw']),
         'area_keep_ratio_20y': round(keep, 3) if keep else '', 'keep_basis': basis, 'keep_groups': n, 'land_rights': r['land_rights_raw'], 'url': r['url']}
    if plo is None: o['watch'] = 'price_undisclosed'
    elif fee_lo is None: o['watch'] = 'fees_undisclosed'
    elif plo <= 50000000 and phi >= 40000000: o['watch'] = 'touches_band'
    else: o['watch'] = 'outside_band'
    if unit and plo and areas and fee_lo and keep:  # a single priced unit can be costed like a used condo
        buy = plo * P['buy_cost_rate']; cap = lambda rv: (plo + buy - rv * (1 - P['sell_cost_rate'])) / months
        o.update(net_cost_jpy_month=round(cap(plo * keep) + fee_lo), net_cost_jpy_m2_month=round((cap(plo * keep) + fee_lo) / areas[0]), net_cost_stress_jpy_month=round(cap(plo * keep * P['stress_residual_factor']) + fee_lo))
    condos.append(o)
wo = {'touches_band': 0, 'price_undisclosed': 1, 'fees_undisclosed': 2, 'outside_band': 3}
condos.sort(key=lambda o: (o['kind'], wo[o['watch']], o['ward'], o['project_name']))
ccols = ['kind', 'watch', 'ward', 'project_name', 'address', 'station_raw', 'price_raw', 'price_min_jpy', 'price_max_jpy', 'area_min_m2', 'area_max_m2', 'fees_month_min_jpy', 'fees_month_max_jpy', 'fees_jpy_m2_month',
         'area_keep_ratio_20y', 'keep_basis', 'keep_groups', 'net_cost_jpy_month', 'net_cost_jpy_m2_month', 'net_cost_stress_jpy_month', 'units_total', 'completion_raw', 'handover_raw', 'build_status', 'land_rights', 'url']
with open(f'{out}/new-condo-projects.csv', 'w', newline='', encoding='utf-8') as f:
    w_ = csv.DictWriter(f, fieldnames=ccols, extrasaction='ignore'); w_.writeheader(); w_.writerows(condos)

qs = lambda v: [round(x) for x in st.quantiles(v, n=4)] if len(v) >= 8 else None
k = [o for o in houses if o['band'] in 'ABCD']
summ = {'new_house': {'listing_rows': len(D) - sum(1 for r in D if r['target_type'] != 'new_house'), 'houses_after_dedup': len(houses), 'bands': dict(sorted(Counter(o['band'] for o in houses).items())),
          'unranked_reasons': dict(Counter((o['notes'] or o.get('residual_basis', 'missing_inputs')) for o in houses if o['band'] == 'U').most_common()),
          'net_cost_jpy_month_quartiles': qs([o['net_cost_jpy_month'] for o in k]), 'net_cost_jpy_m2_month_quartiles': qs([o['net_cost_jpy_m2_month'] for o in k]),
          'keep_ratio_quartiles': [round(x, 2) for x in st.quantiles([o['keep_ratio'] for o in k], n=4)],
          'no_brokerage_fee': dict(Counter(o['no_brokerage_fee'] for o in houses)), 'no_brokerage_by_band': dict(sorted(Counter(o['band'] for o in houses if o['no_brokerage_fee'] != 'no').items())), 'residual_basis_by_band': {b: dict(Counter(o.get('residual_basis') for o in houses if o['band'] == b)) for b in 'ABCD'},
          'build_status': dict(Counter(o['build_status'] for o in houses)), 'band_by_build_status': {b: dict(Counter(o['build_status'] for o in houses if o['band'] == b)) for b in 'ABCD'}},
        'new_condo': {'rows': len(condos), 'kinds': dict(Counter(o['kind'] for o in condos)), 'watch': dict(Counter(o['kind'] + ':' + o['watch'] for o in condos).most_common()),
          'keep_ratio_known_projects': sum(1 for o in condos if o['kind'] == 'project' and o['area_keep_ratio_20y']),
          'project_keep_ratio_quartiles': [round(x, 2) for x in st.quantiles([o['area_keep_ratio_20y'] for o in condos if o['kind'] == 'project' and o['area_keep_ratio_20y']], n=4)] if sum(1 for o in condos if o['kind'] == 'project' and o['area_keep_ratio_20y']) >= 8 else None,
          'project_fee_per_m2_quartiles': qs([o['fees_jpy_m2_month'] for o in condos if o['kind'] == 'project' and o['fees_jpy_m2_month']]),
          'units_costed': sum(1 for o in condos if 'net_cost_jpy_month' in o)}}
json.dump(summ, open(f'{out}/summary-new-builds.json', 'w'), ensure_ascii=False, indent=1); print(json.dumps(summ, ensure_ascii=False, indent=1))
