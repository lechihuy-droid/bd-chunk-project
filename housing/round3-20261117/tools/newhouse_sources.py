"""New-house source survey: parse saved Osaka-shi list pages of SUUMO and Yahoo (all prices) and cross-match.
Usage: newhouse_sources.py <dir with saved html> <out dir for aggregates> <private dir for per-listing rows>"""
import csv, glob, html, json, os, re, sys, unicodedata
from collections import Counter, defaultdict

src, out, data = sys.argv[1:4]
def load(path):
    s = open(path, 'rb').read().decode('utf-8', errors='replace')
    s = re.sub(r'<(script|style)[\s\S]*?</\1>', ' ', s)
    s = re.sub(r'<a\b[^>]*?href="([^"]+)"[^>]*>', lambda m: f' ⟦{html.unescape(m.group(1))}⟧ ', s)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s)))
def man(s):
    out = []
    for m in re.finditer(r'(?:(\d+)億)?(\d[\d,]*)?万(?:(\d+)円)?', unicodedata.normalize('NFKC', s)):
        if m.group(1) or m.group(2): out.append(int(m.group(1) or 0) * 10000 + int((m.group(2) or '0').replace(',', '')))
    return out
nums = lambda s: [float(x) for x in re.findall(r'([\d.]+)m 2', s)]
def addr(a):
    a = unicodedata.normalize('NFKC', a or '').replace('大阪府', '').replace(' ', '')
    a = re.sub(r'(\d+)丁目.*', r'\1', a); a = re.sub(r'(\d+)[-−ー番].*', r'\1', a); return a
ward = lambda a: (re.search(r'大阪市(\S+?区)', a or '') or [None, ''])[1]
band = lambda lo, hi: lo <= 5000 and hi >= 4000

S = []
for f in sorted(glob.glob(f'{src}/nh_suumo*.html')):
    x = load(f)
    for b in re.split(r'(?=⟦/(?:ikkodate|tochi)/osaka/sc_[a-z]+/nc_\d+/⟧ [^⟦]{0,160}?⟦javascript:void\(0\);⟧ お気に入りに追加する)', x)[1:]:
        u = re.match(r'⟦(/(ikkodate|tochi)/osaka/sc_[a-z]+/nc_\d+/)⟧', b); t = re.sub(r'⟦[^⟧]*⟧ ?', '', b)
        g = lambda pat: (re.search(pat, t) or [None, ''])[1].strip()
        price = g(r'販売価格 (.{0,80}?) (?:建物価格|所在地)'); p = man(price); land = nums(g(r'土地面積 (.{0,80}?) 間取り')); bl = nums(g(r'建物面積 (.{0,80}?) (?:掲載写真|チェック|$)'))
        name = g(r'物件名 (.{0,80}?) 販売価格'); a = g(r'所在地 (\S+)')
        if not p or not a: continue
        lots = re.search(r'全(\d+)(?:区画|邸|棟|戸)', name + t[:200])
        multi = len(p) > 1 or len(land) > 1 or bool(lots and int(lots.group(1)) > 1)
        S.append({'source': 'suumo', 'kind': 'land_with_building_condition' if u.group(2) == 'tochi' else 'house', 'multi_lot': multi, 'lots_total': lots.group(1) if lots else '', 'name': name, 'address': a, 'ward': ward(a),
                  'station_raw': g(r'沿線・駅 (.{0,80}?) 土地面積'), 'price_min': min(p), 'price_max': max(p), 'land_min': min(land) if land else '', 'land_max': max(land) if land else '', 'building_min': min(bl) if bl else '', 'building_max': max(bl) if bl else '',
                  'layout': g(r'間取り (\S+) 建物面積'), 'completion': '', 'url': 'https://suumo.jp' + u.group(1)})
Y = []
for f in sorted(glob.glob(f'{src}/nh_yahoo*.html')):
    x = load(f); x = x[x.find('並び替え'):]
    for m in re.finditer(r'⟦(https://realestate\.yahoo\.co\.jp/new/house/(?:detail_corp|dtl)/\w+/)[^⟧]*⟧ (?:(?!⟦https://realestate\.yahoo\.co\.jp/new/house/(?:detail_corp|dtl)/).){0,1500}?(大阪府大阪市\S+)(?: (\d{4})年(\d+)月\S*)? (\S+?)/(\S+?) 土地 ([\d.]+)m 2(?: ～ ?([\d.]+)m 2)? / 建物 ([\d.]+)m 2(?: ～ ?([\d.]+)m 2)? (?:(?!万円).){0,900}?((?:(?:\d+億)?[\d,]*万円)(?:～(?:\d+億)?[\d,]*万円)?)', x):
        p = man(m.group(11))  # a card may show a range (multi-lot project): land/building/price are then min～max
        if not p: continue
        lots = bool(m.group(8) or m.group(10) or len(p) > 1)
        Y.append({'source': 'yahoo', 'kind': 'house', 'multi_lot': lots, 'lots_total': '', 'name': '', 'address': m.group(2), 'ward': ward(m.group(2)), 'station_raw': '', 'price_min': min(p), 'price_max': max(p),
                  'land_min': float(m.group(7)), 'land_max': float(m.group(8) or m.group(7)), 'building_min': float(m.group(9)), 'building_max': float(m.group(10) or m.group(9)), 'layout': m.group(5), 'completion': f'{m.group(3)}-{int(m.group(4)):02d}' if m.group(3) else '', 'url': m.group(1)})
def dedup(rows):
    seen = {}
    for r in rows: seen.setdefault(r['url'], r)
    return list(seen.values())
S, Y = dedup(S), dedup(Y)

# ---- property-like groups inside each source (same block, same land and building area)
key = lambda r: (addr(r['address']), r['land_min'], r['building_min'])
def groups(rows):
    g = defaultdict(list)
    for r in rows: g[key(r) if not r['multi_lot'] else ('multi', r['url'])].append(r)
    return g
gs, gy = groups([r for r in S if r['kind'] == 'house']), groups(Y)
s_units = {k for k in gs if k[0] != 'multi'}; s_multi = [v[0] for k, v in gs.items() if k[0] == 'multi']
def in_project(r):  # a Yahoo unit that falls inside a SUUMO multi-lot entry on the same block
    for p in s_multi:
        if addr(p['address']) == addr(r['address']) and p['land_min'] != '' and p['land_min'] - 0.01 <= r['land_min'] <= p['land_max'] + 0.01 and p['price_min'] <= r['price_min'] <= p['price_max']: return True
    return False
ward_area = {(r['ward'], r['land_min'], r['building_min']) for r in S if r['kind'] == 'house' and not r['multi_lot']}
for k, v in gy.items():
    st = 'in_suumo' if k in s_units else 'in_suumo_project' if in_project(v[0]) else 'in_suumo_probable' if (v[0]['ward'], v[0]['land_min'], v[0]['building_min']) in ward_area else 'not_in_suumo'
    for r in v: r['match'] = st
y_keys = set(gy); y_ward_area = {(r['ward'], r['land_min'], r['building_min']) for r in Y}
for k, v in gs.items():
    r = v[0]
    if k[0] == 'multi':
        hit = any(addr(q['address']) == addr(r['address']) and r['land_min'] != '' and r['land_min'] - 0.01 <= q['land_min'] <= r['land_max'] + 0.01 for q in Y)
        st = 'in_yahoo' if hit else 'not_in_yahoo'
    else: st = 'in_yahoo' if k in y_keys else 'in_yahoo_probable' if (r['ward'], r['land_min'], r['building_min']) in y_ward_area else 'not_in_yahoo'
    for q in v: q['match'] = st
for r in S:
    if r['kind'] != 'house': r['match'] = 'not_compared'

cols = ['source', 'kind', 'multi_lot', 'lots_total', 'match', 'ward', 'address', 'name', 'price_min', 'price_max', 'land_min', 'land_max', 'building_min', 'building_max', 'layout', 'completion', 'station_raw', 'url']
with open(f'{data}/newhouse-listings.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(sorted(S + Y, key=lambda r: (r['source'], r['kind'], r['ward'], r['address'])))

inb = lambda r: band(r['price_min'], r['price_max'])
def grp_stats(g, pred=lambda r: True):
    sel = [v[0] for v in g.values() if pred(v[0])]; return {'groups': len(sel), 'by_match': dict(sorted(Counter(r['match'] for r in sel).items()))}
summ = {
 'suumo': {'listing_urls': len(S), 'houses': sum(r['kind'] == 'house' for r in S), 'land_with_building_condition': sum(r['kind'] != 'house' for r in S),
           'house_single_unit_groups': len(s_units), 'house_multi_lot_entries': len(s_multi), 'multi_lot_with_stated_total': sum(1 for r in s_multi if r['lots_total']), 'lots_in_stated_totals': sum(int(r['lots_total']) for r in s_multi if r['lots_total']),
           'land_condition_multi_lot_entries': sum(1 for r in S if r['kind'] != 'house' and r['multi_lot'])},
 'yahoo': {'listing_urls': len(Y), 'unit_groups': len(gy), 'with_completion_month': sum(1 for v in gy.values() if v[0]['completion'])},
 'yahoo_units_vs_suumo': {'all_prices': grp_stats(gy), 'band_4000_5000': grp_stats(gy, inb)},
 'suumo_houses_vs_yahoo': {'all_prices': grp_stats(gs), 'band_4000_5000': grp_stats(gs, inb), 'multi_lot_all_prices': grp_stats(gs, lambda r: r['multi_lot']), 'multi_lot_band': grp_stats(gs, lambda r: r['multi_lot'] and inb(r))},
 'band_4000_5000_counts': {'suumo_house_groups': sum(1 for v in gs.values() if inb(v[0])), 'suumo_multi_lot': sum(1 for r in s_multi if inb(r)), 'suumo_land_condition_entries': sum(1 for r in S if r['kind'] != 'house' and inb(r)), 'yahoo_unit_groups': sum(1 for v in gy.values() if inb(v[0]))},
 'yahoo_completion_years': dict(sorted(Counter(v[0]['completion'][:4] or 'not_stated' for v in gy.values()).items())),
 'suumo_house_wards': dict(Counter(v[0]['ward'] for v in gs.values()).most_common())}
json.dump(summ, open(f'{out}/newhouse-source-coverage.json', 'w'), ensure_ascii=False, indent=1); print(json.dumps(summ, ensure_ascii=False, indent=1))
