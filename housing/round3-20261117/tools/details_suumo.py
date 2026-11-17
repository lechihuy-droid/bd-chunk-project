#!/usr/bin/env python3
"""SUUMO detail fetch + parse. --parse-only reads cache only. --limit-sample N fetches first N of each type."""
import csv, hashlib, json, os, re, subprocess, sys, time, datetime, unicodedata, fnmatch
from urllib.parse import urlparse
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = f"{BASE}/wave3/targets-suumo.csv"
ROBOTS = f"{BASE}/wave1/robots/suumo.jp.txt"
CACHE = "/tmp/claude-0/-home-user-bd-chunk-project/8a1dfd2a-b2c8-5e83-818a-2a83491f1fc3/scratchpad/wave3/raw-suumo"
LOG = f"{BASE}/wave3/requests-suumo.log"
OUT = f"{BASE}/wave3/data/details-suumo.csv"
SUMMARY = f"{BASE}/wave3/details-suumo-summary.json"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
BUDGET = 520
os.makedirs(CACHE, exist_ok=True)

def robots_rules():
    rules, grp = [], False
    for l in open(ROBOTS, encoding='utf-8'):
        l = l.split('#')[0].strip()
        if l.lower().startswith('user-agent:'):
            grp = l.split(':', 1)[1].strip() == '*'
        elif grp and l.lower().startswith('disallow:'):
            p = l.split(':', 1)[1].strip()
            if p: rules.append(p)
    return rules
RULES = robots_rules()
def allowed(url):
    u = urlparse(url); path = u.path + ('?' + u.query if u.query else '')
    for r in RULES:
        pat = re.escape(r).replace(r'\*', '.*')
        if r.endswith('$'): pat = re.escape(r[:-1]).replace(r'\*', '.*') + '$'
        if re.match(pat, path): return False
    return True

def key(url): return hashlib.sha1(url.encode()).hexdigest()
def cpath(url): return f"{CACHE}/{key(url)}.html"
def cached(url): return os.path.exists(cpath(url)) and os.path.exists(cpath(url)[:-5] + '.meta')
def load(url):
    if not cached(url): return None, None
    meta = json.load(open(cpath(url)[:-5] + '.meta'))
    return meta, open(cpath(url), encoding='utf-8', errors='replace').read()

class Stop(Exception): pass
state = {'requests': 0, 'last': 0.0}
def count_logged():
    return sum(1 for _ in open(LOG)) if os.path.exists(LOG) else 0

def fetch(url):
    if cached(url): return load(url)
    if not allowed(url): raise Stop(f"robots disallow {url}")
    if count_logged() >= BUDGET: raise Stop("budget")
    wait = 3.4 - (time.time() - state['last'])
    if wait > 0: time.sleep(wait)
    r = subprocess.run(['curl', '-sS', '-L', '--compressed', '-A', UA, '-H', 'Accept-Language: ja',
                        '--max-time', '40', '-w', '\n%{http_code} %{url_effective}', url], capture_output=True)
    state['last'] = time.time()
    state['requests'] += 1
    out = r.stdout
    body, _, tail = out.rpartition(b'\n')
    tail = tail.decode().strip().split(' ', 1)
    code = tail[0] or '000'
    final = tail[1] if len(tail) > 1 else url
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    with open(LOG, 'a') as f: f.write(f"{now}\t{code}\t{url}\n")
    if code in ('401', '403', '429') or code.startswith('5'): raise Stop(f"HTTP {code} {url}")
    if code == '000' or r.returncode != 0:
        raise Stop(f"curl error rc={r.returncode} {r.stderr.decode()[:200]} {url}")
    txt = body.decode('utf-8', errors='replace')
    if not txt.strip(): raise Stop(f"empty body {url}")
    if urlparse(final).netloc != 'suumo.jp' or not allowed(final): raise Stop(f"redirected off-host/disallowed {final}")
    if re.search(r'captcha|recaptcha|アクセスが集中|Access Denied|robot check', txt[:6000], re.I) and len(txt) < 20000:
        raise Stop(f"challenge page {url}")
    open(cpath(url), 'w', encoding='utf-8').write(txt)
    meta = {'url': url, 'fetched_at': now, 'http_status': int(code), 'final_url': final}
    json.dump(meta, open(cpath(url)[:-5] + '.meta', 'w'))
    return meta, txt


# ---------------------------------------------------------------- parsing
from bs4 import BeautifulSoup
COLS = ['target_type','url','page_title','project_name','address','station_raw','price_raw','price_min_man','price_max_man',
 'most_common_price_band_raw','units_for_sale','units_total','layout_raw','unit_or_building_area_raw','land_area_raw',
 'management_fee_raw','repair_reserve_raw','repair_fund_lump_raw','other_fees_raw','completion_raw','handover_raw',
 'structure_raw','land_rights_raw','zoning_raw','coverage_far_raw','road_raw','parking_raw','seller_raw','builder_raw',
 'transaction_type_raw','company_raw','status','missing_fields']
ALIASES = {
 'address': ['所在地','住所'],
 'station_raw': ['交通'],
 'price_raw': ['価格','予定価格','販売価格'],
 'most_common_price_band_raw': ['最多価格帯','予定最多価格帯'],
 'units_for_sale': ['販売戸数','今回販売戸数','販売区画数','今回販売区画数'],
 'units_total': ['総戸数','総区画数'],
 'layout_raw': ['間取り'],
 'unit_or_building_area_raw': ['専有面積','建物面積'],
 'land_area_raw': ['土地面積','敷地面積'],
 'management_fee_raw': ['管理費'],
 'repair_reserve_raw': ['修繕積立金'],
 'repair_fund_lump_raw': ['修繕積立基金'],
 'other_fees_raw': ['その他諸経費','諸費用'],
 'completion_raw': ['完成時期','完成時期(築年月)','竣工時期','築年月','完成時期（築年月）'],
 'handover_raw': ['引渡可能時期','入居時期','引渡時期','入居可能時期'],
 'structure_raw': ['構造・工法','構造・階建て','構造・階建','構造・階数','構造'],
 'land_rights_raw': ['土地の権利形態','敷地の権利形態'],
 'zoning_raw': ['用途地域'],
 'coverage_far_raw': ['建ぺい率・容積率','建蔽率・容積率'],
 'road_raw': ['私道負担・道路','接道状況','私道負担','道路'],
 'parking_raw': ['駐車場'],
 'seller_raw': ['売主'],
 'builder_raw': ['施工','施工会社'],
 'transaction_type_raw': ['取引態様'],
 'company_raw': ['会社概要','情報提供会社'],
}
LABEL2COL = {}
for c, ls in ALIASES.items():
    for l in ls: LABEL2COL[unicodedata.normalize('NFKC', l)] = c
CORE = {'new_condo_project': ['address','station_raw','price_raw','units_total','layout_raw','unit_or_building_area_raw','handover_raw'],
        'new_house': ['address','station_raw','price_raw','layout_raw','unit_or_building_area_raw','land_area_raw','completion_raw']}
SKIP_TABLE_CLS = {'formtable','form_table','alert_table','loan','loanbox-body','setloanbox'}

def norm(t):
    t = unicodedata.normalize('NFKC', t or '')
    t = re.sub(r'\s+', ' ', t).strip()
    return t
def clean_label(t):
    t = norm(t); t = t.replace('ヒント', '')
    return re.sub(r'\s+', '', t)
def clean_val(t):
    t = norm(t)
    t = re.sub(r'\s*\[ □ 支払シミュレーション \]', '', t)
    t = re.sub(r'\s*\[ ■ 周辺環境 \]', '', t)
    t = re.sub(r'\s*\[ 乗り換え案内 \]', '', t)
    t = re.sub(r'\s*地図を見る$', '', t)
    t = re.sub(r'(?<=\d)m 2\b', 'm2', t).strip()
    return '' if t in ('-', '－', '―', '') else t

def pairs(soup):
    """label -> first non-empty value, from all label/value rows (th/td alternation) in content tables."""
    out, labels = {}, {}
    for tb in soup.find_all('table'):
        if SKIP_TABLE_CLS & set(tb.get('class') or []): continue
        for tr in tb.find_all('tr'):
            cells = tr.find_all(['th', 'td'], recursive=False)
            i = 0
            while i < len(cells) - 1:
                if cells[i].name == 'th' and cells[i+1].name == 'td':
                    lab = clean_label(cells[i].get_text(' ')); val = clean_val(cells[i+1].get_text(' '))
                    labels[lab] = labels.get(lab, 0) + 1
                    if lab and lab not in out: out[lab] = val
                    elif lab and not out[lab] and val: out[lab] = val
                    i += 2
                else: i += 1
    return out, labels

def parse_price(t):
    t = unicodedata.normalize('NFKC', t or '')
    vals = []
    for m in re.finditer(r'(?:(\d[\d,]*)億(?:(\d[\d,]*)万)?|(\d[\d,]*)万)', t):
        if m.group(3): vals.append(int(m.group(3).replace(',', '')))
        else: vals.append(int(m.group(1).replace(',', '')) * 10000 + (int(m.group(2).replace(',', '')) if m.group(2) else 0))
    return (min(vals), max(vals)) if vals else (None, None)

def text_of(sp): return norm(sp.get_text(' '))

def parse_row(tt, url, pages):
    """pages: list of (meta, html) in priority order. Returns row dict + extras."""
    row = {c: '' for c in COLS}; row['target_type'] = tt; row['url'] = url
    main_meta, main_html = pages[0]
    soups = [BeautifulSoup(h, 'lxml') for _, h in pages]
    ms = soups[0]
    row['page_title'] = norm(ms.title.get_text()) if ms.title else ''
    h1 = ms.find('h1')
    if h1:
        t = h1.find(class_='section_h1-title')
        if t: row['project_name'] = norm(t.get_text())
        else:
            for sp in h1.find_all('span'): sp.decompose()
            n = norm(h1.get_text())
            row['project_name'] = re.sub(r'\s*[\d億万,]+円?台?$', '', n).strip()
    allp, allsets = {}, {}
    for sp in soups:
        p, l = pairs(sp)
        for k, v in p.items():
            if k not in allp or (not allp[k] and v): allp[k] = v
    for lab, val in allp.items():
        col = LABEL2COL.get(unicodedata.normalize('NFKC', lab))
        if col and not row[col] and val: row[col] = val
    # fallbacks / special cases
    texts = [text_of(sp) for sp in soups]
    full = ' '.join(texts)
    if not row['transaction_type_raw']:
        m = re.search(r'取引態様[:：]?\s*(＜[^＞]+＞|<[^>]+>|[^\s　]+)', full)
        if m: row['transaction_type_raw'] = m.group(1)
    if tt == 'new_house' and not row['company_raw']:
        pass
    if tt == 'new_condo_project' and not row['company_raw']:
        names = []
        for sp in soups[:1]:
            for dl in sp.find_all('dl', class_='pipelink'):
                dt = dl.find('dt')
                if dt and '不動産会社提供情報' in dt.get_text():
                    for a in dl.select('li.pipelink_list-item a.pipelink_list-iconlink'):
                        n = norm(a.get_text())
                        if n and n not in names: names.append(n)
        row['company_raw'] = ' | '.join(names)
    row['price_min_man'], row['price_max_man'] = (lambda a: ('' if a[0] is None else a[0], '' if a[1] is None else a[1]))(parse_price(row['price_raw']))
    return row, allp

def status_for(tt, row, pages_meta, has_table):
    miss = [c for c in CORE[tt] if not row[c]]
    return miss

def completion_bucket(txt, today=(2026, 11)):
    if not txt: return 'unknown'
    t = unicodedata.normalize('NFKC', txt)
    m = re.search(r'(\d{4})年\s*(\d{1,2})月', t)
    if re.search(r'完成済|築済|即入居', t) and not m: return 'completed'
    if not m: return 'unknown'
    ym = (int(m.group(1)), int(m.group(2)))
    if ym < today: return 'completed'
    if ym == today: return 'current_month'
    return 'future'

def collect_pages(tt, url, do_fetch):
    """return list of (meta, html) with main first; may fetch."""
    meta, html = fetch(url) if do_fetch else load(url)
    if meta is None: return []
    pages = [(meta, html)]
    if meta['http_status'] != 200: return pages
    if tt == 'new_condo_project':
        sub = url.rstrip('/') + '/property/'
        m2, h2 = fetch(sub) if do_fetch else load(sub)
        if m2: pages.append((m2, h2))
    else:
        if not re.search(r'用途地域|構造・工法|土地の権利形態', html) and 'bukkengaiyo' in html:
            sub = url.rstrip('/') + '/bukkengaiyo/'
            m2, h2 = fetch(sub) if do_fetch else load(sub)
            if m2: pages.append((m2, h2))
    return pages

def main():
    parse_only = '--parse-only' in sys.argv
    sample = None
    stop_reason = ''
    targets = list(csv.DictReader(open(TARGETS, encoding='utf-8')))
    if '--fetch-only' in sys.argv or not parse_only:
        try:
            for r in targets:
                collect_pages(r['target_type'], r['url'], True)
        except Stop as e:
            stop_reason = str(e)
            print('STOP:', stop_reason, file=sys.stderr)
    build_outputs(targets, stop_reason)

def build_outputs(targets, stop_reason):
    rows, stats_labels = [], {}
    buckets = {'completed': 0, 'current_month': 0, 'future': 0, 'unknown': 0}
    for r in targets:
        tt, url = r['target_type'], r['url']
        pages = collect_pages(tt, url, False)
        if not pages:
            row = {c: '' for c in COLS}; row.update(target_type=tt, url=url, status='fetch_failed', missing_fields='all'); rows.append(row); continue
        meta = pages[0][0]
        if meta['http_status'] in (404, 410):
            row = {c: '' for c in COLS}; row.update(target_type=tt, url=url, status='not_found', missing_fields='all'); rows.append(row); continue
        if meta['http_status'] != 200:
            row = {c: '' for c in COLS}; row.update(target_type=tt, url=url, status='fetch_failed', missing_fields='all'); rows.append(row); continue
        row, allp = parse_row(tt, url, pages)
        for lab in allp: stats_labels.setdefault(tt, {}); stats_labels[tt][lab] = stats_labels[tt].get(lab, 0) + 1
        txt = ' '.join(norm(BeautifulSoup(h, 'lxml').get_text(' ')) for _, h in pages)
        if not allp and re.search(r'掲載を終了|掲載終了|ページが見つかりません|お探しの', txt):
            row['status'] = 'not_found'; row['missing_fields'] = 'all'
        else:
            miss = status_for(tt, row, pages, bool(allp))
            row['missing_fields'] = ';'.join(miss)
            row['status'] = 'ok' if not miss else 'parse_partial'
            if tt == 'new_condo_project' and len(pages) < 2: row['status'] = 'parse_partial'; row['missing_fields'] = ';'.join(miss + ['property_subpage_not_fetched'])
        rows.append(row)
    with open(OUT, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, COLS); w.writeheader(); w.writerows(rows)
    # summary
    import collections
    S = {'requests_made_total_logged': count_logged(), 'stop_reason': stop_reason or None, 'rows': len(rows),
         'rows_by_status': {}, 'rows_by_type': collections.Counter(r['target_type'] for r in rows),
         'fill_rate_by_type': {}, 'new_house_completion_buckets': collections.Counter(), 'condo_price_undetermined': 0,
         'condo_price_determined_numeric': 0}
    for tt in ('new_condo_project', 'new_house'):
        rr = [r for r in rows if r['target_type'] == tt]
        S['rows_by_status'][tt] = dict(collections.Counter(r['status'] for r in rr))
        good = [r for r in rr if r['status'] in ('ok', 'parse_partial')]
        S['fill_rate_by_type'][tt] = {'n_parsed_rows': len(good), **{c: round(sum(1 for r in good if r[c] != '') / len(good), 3) if good else None
                                       for c in COLS if c not in ('target_type', 'url', 'status', 'missing_fields')}}
    for r in rows:
        if r['target_type'] == 'new_house' and r['status'] in ('ok', 'parse_partial'):
            S['new_house_completion_buckets'][completion_bucket(r['completion_raw'])] += 1
        if r['target_type'] == 'new_condo_project' and r['status'] in ('ok', 'parse_partial'):
            if re.search(r'未定', r['price_raw']): S['condo_price_undetermined'] += 1
            elif r['price_min_man'] != '': S['condo_price_determined_numeric'] += 1
    S['rows_by_type'] = dict(S['rows_by_type']); S['new_house_completion_buckets'] = dict(S['new_house_completion_buckets'])
    S['note'] = 'completion bucket relative to 2026-11 (today 2026-11-17): completed = before Nov 2026; current_month = Nov 2026; future = after.'
    S['labels_seen'] = stats_labels
    json.dump(S, open(SUMMARY, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in S.items() if k != 'labels_seen'}, ensure_ascii=False, indent=1)[:3000])

if __name__ == '__main__':
    main()
