"""New-condo source survey: extract Osaka-shi project lists from saved list pages of four sources and cross-match them.
Usage: newcondo_sources.py <dir with saved html> <out dir for aggregates> [<private dir for per-project rows>]"""
import csv, html, json, re, sys, unicodedata
from collections import Counter, defaultdict

src, out = sys.argv[1], sys.argv[2]; data = sys.argv[3] if len(sys.argv) > 3 else out  # per-project rows go to `data`, aggregates to `out`
def load(name):
    s = open(f'{src}/{name}.html', 'rb').read().decode('utf-8', errors='replace')
    s = re.sub(r'<(script|style)[\s\S]*?</\1>', ' ', s)
    s = re.sub(r'<a\b[^>]*?href="([^"]+)"[^>]*>', lambda m: f' ⟦{html.unescape(m.group(1))}⟧ ', s)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s)))
def nname(n):
    n = unicodedata.normalize('NFKC', n).upper()
    n = re.sub(r'[\(（]仮称[\)）]|【[^】]*】|[\s・･\-‐―ー\(\)（）「」『』,、.。]', '', n)
    return n
def naddr(a):
    a = unicodedata.normalize('NFKC', a or '').replace('大阪府', '').replace(' ', '')
    m = re.match(r'(大阪市\S+?区)([^\d]+?)(\d+)?(?:丁目|[-−ー番]|$|\D)', a + ' ')
    return (m.group(1), m.group(2).strip(), m.group(3) or '') if m else None
def ym(d):
    m = re.search(r'(\d{4})年0?(\d+)月', d or ''); return (m.group(1), m.group(2)) if m else None
ward = lambda a: (re.search(r'大阪市(\S+?区)', a or '') or [None, ''])[1]
def prices(s):
    s = unicodedata.normalize('NFKC', s or ''); n = []
    for a, b in re.findall(r'(\d+)億(?:([\d,]+)万)?', s): n.append(int(a) * 10000 + int((b or '0').replace(',', '')))
    n += [int(x.replace(',', '')) for x in re.findall(r'([\d,]+)万円', re.sub(r'\d+億(?:[\d,]+万)?円?台?', '', s))]
    return (min(n), max(n)) if n else None

P = []  # one row per (source, project page)
# Yahoo
for f in ('nc_yahoo', 'nc_yahoo2', 'nc_yahoo3'):
    x = load(f); x = x[x.find('件を表示'):]
    for b in re.split(r'(?=⟦/new/mansion/dtl/\d+/(?:\?sc_shouhin=[^⟧]*)?⟧ (?!購入者|[^⟦]{0,40}をもっと見る))', x)[1:]:
        m = re.match(r'⟦(/new/mansion/dtl/\d+/)[^⟧]*⟧ ([^⟦]{2,80}?) (?:新発表|更新|第|先着|価格|駅徒歩|NEW|最終|販売|[\d億,]+万|タワー|子育て|大規模)', b)
        a = re.search(r'(大阪府大阪市\S+)', b)
        if not m or not a: continue
        g = lambda pat: (re.search(pat, b) or [None, ''])[1]
        P.append({'source': 'yahoo', 'name': m.group(2).strip(), 'address': a.group(1), 'url': 'https://realestate.yahoo.co.jp' + m.group(1), 'delivery': g(r'入居時期 (\S+)'), 'units_total': g(r'総戸数 (\d+)戸'), 'seller': g(r'不動産会社 (\S+)'), 'price_text': g(r'販売期 価格 間取り 専有面積 (.{0,160}?) 資料をもらう')[:120] or b[len(m.group(0)) - 6:][:80]})
# SUUMO
for f in ('nc_suumo_p1', 'nc_suumo_p2'):
    x = load(f); x = x[x.find('まとめて資料請求する'):]
    for b in re.split(r'(?=⟦/ms/shinchiku/osaka/sc_[a-z]+/nc_\d+/⟧ [^⟦]{2,80}? ⟦javascript:void\(0\);⟧ 追加)', x)[1:]:
        m = re.match(r'⟦((/ms/shinchiku/osaka/sc_[a-z]+/nc_\d+/))⟧ ([^⟦]{2,80}?) ⟦javascript', b)
        b = re.sub(r'⟦[^⟧]*⟧ ?', '', b)
        a = re.search(r'所在地 (\S+)', b)
        if not m or not a: continue
        g = lambda pat: (re.search(pat, b) or [None, ''])[1]
        seg = g(r'引渡時期 (.{0,400}?) (?:見学予約可能な日程|詳細表示する|資料請求する)')
        cut = re.search(r'(?:\d+億)?[\d,]*万円|価格未定', seg); deliv = seg[:cut.start()].strip() if cut else seg.strip(); price = seg[cut.start():] if cut else ''
        unit = bool(price) and not re.search(r'～|・|タイプ|期|先着順|未定|予定', price)
        P.append({'source': 'suumo', 'name': m.group(3).strip(), 'address': a.group(1), 'url': 'https://suumo.jp' + m.group(2), 'delivery': deliv[:40], 'units_total': '', 'seller': '', 'price_text': price[:300], 'kind': 'unsold_unit_resale' if unit else 'project'})
# Major7
x = load('nc_major7_27')
for b in re.split(r'(?=⟦https://www\.major7\.net/Bukkendetail/\d+⟧ [^⟦]{1,60}? あとで見る )', x[x.find('件 見つかりました'):])[1:]:
    u = re.match(r'⟦(https://www\.major7\.net/Bukkendetail/\d+)⟧', b); b = re.sub(r'⟦[^⟧]*⟧ ?', '', b)
    m = re.match(r'(\S.{1,60}?) あとで見る 価格 (.{0,60}?) 所在地 (\S+)', b)
    if m and '大阪府大阪市' in m.group(3):
        s = re.search(r'売主:(\S+?)のマンション一覧', b)
        P.append({'source': 'major7', 'name': m.group(1).strip(), 'address': m.group(3), 'url': u.group(1) if u else '', 'delivery': '', 'units_total': '', 'seller': s.group(1) if s else '', 'price_text': m.group(2)})
# Sumai-Surfin (prefecture-wide list; keep Osaka-shi)
for f in ['nc_surfin_new'] + [f'nc_surfin_p{i}' for i in range(2, 22)]:
    x = load(f)
    for b in re.split(r'(?=チェック 新築 )', x)[1:]:
        u = re.search(r'⟦(/re/\d+/)⟧', b); b = re.sub(r'⟦[^⟧]*⟧ ?', '', b)
        m = re.match(r'チェック 新築 (.{1,70}?) [\d.\-]+ 点', b); a = re.search(r'(大阪府\S+)', b)
        if not m or not a or not a.group(1).startswith('大阪府大阪市'): continue
        g = lambda pat: (re.search(pat, b) or [None, ''])[1]
        P.append({'source': 'surfin', 'name': m.group(1).strip(), 'address': a.group(1), 'url': ('https://www.sumai-surfin.com' + u.group(1)) if u else '', 'delivery': '', 'units_total': g(r'総戸数 (\d+)'), 'seller': '', 'price_text': (g(r'実販売価格 (.{0,40}?) (?:部屋ごと|間取り)') + ' | 分譲開始 ' + g(r'分譲開始 (\S+)'))[:120]})

# ---- cluster projects across sources: same normalised name, or one name contains the other, or same ward+town+chome with a shared name stem
for p in P: p.setdefault('kind', 'project')
for p in P: p['_n'] = nname(p['name']); p['_a'] = naddr(p['address']); p['ward'] = ward(p['address'])
clusters = []
def same(p, c):
    for q in c:
        a, b = p['_n'], q['_n']
        if a == b or (min(len(a), len(b)) >= 6 and (a in b or b in a)): return True
        if p['_a'] and q['_a'] and p['_a'][:2] == q['_a'][:2] and (not p['_a'][2] or not q['_a'][2] or p['_a'][2] == q['_a'][2]):
            if ym(p['delivery']) and ym(p['delivery']) == ym(q['delivery']): return True  # same block, same handover month: one project under two names
            if len(set(re.findall(r'[ァ-ヶA-Z一-龥]{2}', a)) & set(re.findall(r'[ァ-ヶA-Z一-龥]{2}', b))) >= 2 or a[:4] == b[:4]: return True
    return False
for p in sorted(P, key=lambda p: (-len(p['_n']), p['source'])):
    for c in clusters:
        if same(p, c): c.append(p); break
    else: clusters.append([p])

SRC = ['yahoo', 'suumo', 'major7', 'surfin']; rows = []
for c in clusters:
    srcs = {p['source'] for p in c}; best = sorted(c, key=lambda p: SRC.index(p['source']))[0]
    rng = [prices(p['price_text']) for p in c if prices(p['price_text'])]
    lo = min(r[0] for r in rng) if rng else None; hi = max(r[1] for r in rng) if rng else None
    kind = 'project' if any(p['kind'] == 'project' for p in c) else 'unsold_unit_resale'
    rows.append({'project': best['name'], 'kind': kind, 'ward': best['ward'], 'address': best['address'], **{s: 'x' if s in srcs else '' for s in SRC}, 'source_count': len(srcs),
        'delivery': next((p['delivery'] for p in c if p['delivery']), ''), 'units_total': next((p['units_total'] for p in c if p['units_total']), ''), 'seller': next((p['seller'] for p in c if p['seller']), ''),
        'price_min_man': lo or '', 'price_max_man': hi or '', 'price_status': 'undisclosed' if not rng else 'touches_4000_5000' if lo <= 5000 and hi >= 4000 else 'above_5000' if lo > 5000 else 'below_4000',
        'price_text': ' / '.join(dict.fromkeys(p['price_text'] for p in c if p['price_text']))[:200], 'urls': ' '.join(dict.fromkeys(p['url'] for p in c if p['url']))})
rows.sort(key=lambda r: (r['ward'], r['project']))
with open(f'{data}/projects-by-source.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
all_rows = rows; rows = [r for r in rows if r['kind'] == 'project']; tot = len(rows)
summ = {'source_rows': dict(Counter(p['source'] for p in P)), 'clusters_total': len(all_rows), 'unsold_unit_resale_only_clusters': len(all_rows) - tot, 'projects_total': tot,
    'projects_per_source': {s: sum(1 for r in rows if r[s]) for s in SRC},
    'only_in_one_source': {s: sum(1 for r in rows if r[s] and r['source_count'] == 1) for s in SRC},
    'by_source_count': dict(sorted(Counter(r['source_count'] for r in rows).items())),
    'yahoo_or_suumo': sum(1 for r in rows if r['yahoo'] or r['suumo']), 'missing_from_yahoo': sum(1 for r in rows if not r['yahoo']), 'missing_from_suumo': sum(1 for r in rows if not r['suumo']),
    'price_status': dict(Counter(r['price_status'] for r in rows)),
    'price_status_by_presence': {k: dict(Counter(r['price_status'] for r in rows if (bool(r['yahoo']), bool(r['suumo'])) == v)) for k, v in {'both': (True, True), 'yahoo_only': (True, False), 'suumo_only': (False, True), 'neither': (False, False)}.items()},
    'wards': dict(Counter(r['ward'] for r in rows).most_common())}
json.dump(summ, open(f'{out}/source-coverage.json', 'w'), ensure_ascii=False, indent=1); print(json.dumps(summ, ensure_ascii=False, indent=1))
