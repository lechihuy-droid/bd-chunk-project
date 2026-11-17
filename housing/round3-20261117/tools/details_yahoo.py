#!/usr/bin/env python3
"""Yahoo!不動産 detail fetch + parse (allowed main page only). --parse-only reads cache only. --fetch-only N: fetch first N targets."""
import csv, hashlib, json, os, re, subprocess, sys, time, datetime, html, unicodedata
from urllib.parse import urlparse
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = f"{BASE}/wave3/targets-yahoo.csv"
ROBOTS = f"{BASE}/wave1/robots/realestate.yahoo.co.jp.txt"
CACHE = "/tmp/claude-0/-home-user-bd-chunk-project/8a1dfd2a-b2c8-5e83-818a-2a83491f1fc3/scratchpad/wave3/raw-yahoo"
LOG = f"{BASE}/wave3/requests-yahoo.log"
OUT = f"{BASE}/wave3/data/details-yahoo.csv"
HOST = 'realestate.yahoo.co.jp'
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
BUDGET = 40
os.makedirs(CACHE, exist_ok=True); os.makedirs(os.path.dirname(OUT), exist_ok=True)

def robots_rules():
    rules, grp = [], False
    for l in open(ROBOTS, encoding='utf-8'):
        l = l.split('#')[0].strip()
        if l.lower().startswith('user-agent:'): grp = l.split(':', 1)[1].strip() == '*'
        elif grp and l.lower().startswith(('disallow:', 'allow:')):
            k, p = l.split(':', 1); p = p.strip()
            if p: rules.append((k.lower(), p))
    return rules
RULES = robots_rules()
def _m(p, path):
    end = p.endswith('$'); pat = re.escape(p[:-1] if end else p).replace(r'\*', '.*')
    return re.match(pat + ('$' if end else ''), path) is not None
def allowed(url):
    u = urlparse(url); path = u.path + ('?' + u.query if u.query else '')
    best = None  # longest matching rule wins, Allow wins ties
    for k, p in RULES:
        if _m(p, path):
            if best is None or len(p) > len(best[1]) or (len(p) == len(best[1]) and k == 'allow'): best = (k, p)
    return best is None or best[0] == 'allow'

def key(url): return hashlib.sha1(url.encode()).hexdigest()
def cpath(url): return f"{CACHE}/{key(url)}.html"
def cached(url): return os.path.exists(cpath(url)) and os.path.exists(cpath(url)[:-5] + '.meta')
def load(url):
    if not cached(url): return None, None
    return json.load(open(cpath(url)[:-5] + '.meta')), open(cpath(url), encoding='utf-8', errors='replace').read()

class Stop(Exception): pass
state = {'last': 0.0}
def count_logged(): return sum(1 for _ in open(LOG)) if os.path.exists(LOG) else 0

def fetch(url):
    if cached(url): return load(url)
    if urlparse(url).netloc != HOST: raise Stop(f"off-host {url}")
    if not allowed(url): raise Stop(f"robots disallow {url}")
    if count_logged() >= BUDGET: raise Stop("budget")
    wait = 3.4 - (time.time() - state['last'])
    if wait > 0: time.sleep(wait)
    r = subprocess.run(['curl', '-sS', '-L', '--compressed', '-A', UA, '-H', 'Accept-Language: ja', '--max-time', '40',
                        '-w', '\n%{http_code} %{url_effective}', url], capture_output=True)
    state['last'] = time.time()
    body, _, tail = r.stdout.rpartition(b'\n')
    tail = tail.decode().strip().split(' ', 1); code = tail[0] or '000'; final = tail[1] if len(tail) > 1 else url
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    with open(LOG, 'a') as f: f.write(f"{now}\t{code}\t{url}\n")
    if code in ('401', '403', '429') or code.startswith('5'): raise Stop(f"HTTP {code} {url}")
    if code == '000' or r.returncode != 0: raise Stop(f"curl error rc={r.returncode} {r.stderr.decode()[:200]} {url}")
    txt = body.decode('utf-8', errors='replace')
    if not txt.strip(): raise Stop(f"empty body {url}")
    if urlparse(final).netloc != HOST: raise Stop(f"redirected off-host {final}")
    if not allowed(final): raise Stop(f"redirected to robots-disallowed {final}")
    if re.search(r'captcha|recaptcha|アクセスが集中|Access Denied|robot check', txt[:6000], re.I) and len(txt) < 20000: raise Stop(f"challenge page {url}")
    open(cpath(url), 'w', encoding='utf-8').write(txt)
    json.dump({'url': url, 'fetched_at': now, 'http_status': int(code), 'final_url': final}, open(cpath(url)[:-5] + '.meta', 'w'))
    return {'url': url}, txt

def targets(): return list(csv.DictReader(open(TARGETS, encoding='utf-8')))


COLS = ['target_type', 'url', 'page_title', 'project_name', 'address', 'station_raw', 'price_raw', 'price_min_man', 'price_max_man', 'most_common_price_band_raw',
        'units_for_sale', 'units_total', 'layout_raw', 'unit_or_building_area_raw', 'land_area_raw', 'management_fee_raw', 'repair_reserve_raw', 'repair_fund_lump_raw',
        'other_fees_raw', 'completion_raw', 'handover_raw', 'structure_raw', 'land_rights_raw', 'zoning_raw', 'coverage_far_raw', 'road_raw', 'parking_raw', 'seller_raw',
        'builder_raw', 'transaction_type_raw', 'company_raw', 'status', 'missing_fields']
EXPECT = {  # fields the allowed main page can normally show, per target type
    'new_house': ['address', 'station_raw', 'price_raw', 'layout_raw', 'unit_or_building_area_raw', 'land_area_raw', 'completion_raw', 'handover_raw', 'structure_raw', 'land_rights_raw',
                  'zoning_raw', 'coverage_far_raw', 'road_raw', 'parking_raw', 'transaction_type_raw', 'company_raw'],
    'new_condo_project': ['project_name', 'address', 'station_raw', 'price_raw', 'units_for_sale', 'layout_raw', 'unit_or_building_area_raw', 'completion_raw', 'handover_raw',
                          'management_fee_raw', 'repair_reserve_raw', 'repair_fund_lump_raw', 'structure_raw', 'land_rights_raw', 'zoning_raw', 'builder_raw', 'seller_raw', 'company_raw'],
}
NOISE = re.compile(r'住宅ローン返済額の目安を見る|変更になったら通知する|設定済み（ 変更する ）|決まったら通知する|資料請求して最新の価格を知る|追加・更新になったら通知する|地図を見る|行き方を調べる|詳細を見る|会社ページが充実！'
                   r'|\[ 地図を確認 \]|他の交通を見る|間取り図が欲しい 無料|初期費用が知りたい 無料|月々の支払い目安を見る')

def flat(x):
    x = re.sub(r'<(script|style)[\s\S]*?</\1>', ' ', x)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '\n', x)))
def clean(v):
    v = NOISE.sub(' ', v); v = re.sub(r'm 2\b', 'm²', v)
    v = re.sub(r'\s+', ' ', v).strip()
    return '' if v in ('-', '－', '—') else v
def labelled(text, labels):
    """Split 'L1 v1 L2 v2 ...' text by the known labels (in order of appearance); first occurrence of a label wins."""
    pat = re.compile(r'(?:(?<= )|^)(' + '|'.join(re.escape(l) for l in sorted(labels, key=len, reverse=True)) + r') ')
    ms = list(pat.finditer(text)); out = {}
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        out.setdefault(m.group(1), clean(text[m.end():end]))
    return out
def man(s):
    v = []
    for m in re.finditer(r'(?:(\d+)億)?\s*([\d,]+)?万円', unicodedata.normalize('NFKC', s)):
        if m.group(1) or m.group(2): v.append(int(m.group(1) or 0) * 10000 + int((m.group(2) or '0').replace(',', '')))
    return v

HOUSE_L = ['所在地', '交通', '間取り', '土地面積', '建物面積', '建ぺい率/容積率', '完成時期', '引き渡し可能時期', '接道', '私道負担', '建物階', '建物状況', '建物現況', '用途地域', '構造・工法', '土地権利形態', '駐車場・車庫']
MAN_HEAD_L = ['価格', '所在地', '交通', '間取り', '専有面積', '入居時期', 'モデルルーム', '会社/ブランド情報']
MAN_SALES_L = ['価格', '最多価格帯', '専有面積', 'バルコニー面積', '販売戸数', '所在階', '間取り', '管理費（月額）', '修繕積立金（月額）', '修繕積立基金（一括）', 'その他', '販売スケジュール']
MAN_OVER_L = ['所在地', '交通', '総戸数', '構造、建物階数', '敷地面積', '用途地域', '敷地の権利形態', '完成時期', '入居可能時期', '施工会社', '管理会社', '管理形態', '管理員の勤務形態', 'その他']

def parse(t, x):
    r = {c: '' for c in COLS}; r['target_type'] = t['target_type']; r['url'] = t['url']
    m = re.search(r'<title>([^<]*)</title>', x); r['page_title'] = html.unescape(m.group(1)).strip() if m else ''
    f = flat(x)
    if t['target_type'] == 'new_house':
        i = f.find(' 価格 ')
        j = f.find(' 所在地 ', i)
        if i < 0 or j < 0: r['status'] = 'parse_failed'; return r
        r['price_raw'] = clean(f[i + 4:j])
        k = f.find('各項目の詳細', j); i2 = f.rfind(' 所在地 ', 0, k)
        d = labelled(f[i2 + 1:k], HOUSE_L)
        r['address'] = d.get('所在地', ''); r['station_raw'] = d.get('交通', ''); r['layout_raw'] = d.get('間取り', '')
        r['land_area_raw'] = d.get('土地面積', ''); r['unit_or_building_area_raw'] = d.get('建物面積', ''); r['coverage_far_raw'] = d.get('建ぺい率/容積率', '')
        r['completion_raw'] = d.get('完成時期', ''); r['handover_raw'] = d.get('引き渡し可能時期', ''); r['road_raw'] = d.get('接道', '')
        r['zoning_raw'] = d.get('用途地域', ''); r['structure_raw'] = d.get('構造・工法', ''); r['land_rights_raw'] = d.get('土地権利形態', ''); r['parking_raw'] = d.get('駐車場・車庫', '')
        c = f.find('この物件を取り扱う不動産会社'); seg = f[c + len('この物件を取り扱う不動産会社'):c + 700]
        e = seg.find(' 住所 ')
        name = re.sub(r'(?:ゴールド|シルバー|ブロンズ)?推奨店|[\d.-]+ 不動産会社レビュー\d+件|おすすめ|成約でもらえる|オンライン対応可|現地見学会開催中|元付', ' ', seg[:e] if e > 0 else '')
        r['company_raw'] = re.sub(r'\s+', ' ', name).strip()
        m = re.search(r'取引態様 (\S+)', seg); r['transaction_type_raw'] = m.group(1) if m else ''
    else:
        m = re.search(r'<h1[^>]*>([\s\S]*?)</h1>', x); r['project_name'] = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', m.group(1)))).strip() if m else ''
        i = f.find(' 価格 '); j = f.find('更新通知 …', i)
        if i < 0 or j < 0: r['status'] = 'parse_failed'; return r
        h = labelled(f[i + 1:j], MAN_HEAD_L)
        r['price_raw'] = h.get('価格', ''); r['address'] = h.get('所在地', ''); r['station_raw'] = h.get('交通', ''); r['layout_raw'] = h.get('間取り', '')
        r['unit_or_building_area_raw'] = h.get('専有面積', ''); r['handover_raw'] = h.get('入居時期', ''); r['company_raw'] = h.get('会社/ブランド情報', '')
        s0 = f.find(' 販売概要 ')
        if s0 > 0:
            s1 = min([p for p in (f.find('問い合わせ先', s0), f.find(' 物件概要 ', s0)) if p > 0] or [len(f)])
            sec = f[s0:s1]
            if ' 価格 専有面積 間取り 販売戸数 ' in sec:  # table form: one or more rows, units are the last cell of each row
                tb = sec[sec.find('販売戸数 ') + 5:]; tb = tb[:tb.find('モデルルーム')] if 'モデルルーム' in tb else tb
                u = re.findall(r'(?:^|(?<= ))(\d+戸(?:（[^）]*）)?)(?= |$)', tb)
                r['units_for_sale'] = ' / '.join(u) if u else ('未定' if re.search(r'未定\s*$', tb) else '')
            else:
                sd = labelled(sec[sec.find(' 価格 ') + 1:], MAN_SALES_L)
                r['units_for_sale'] = sd.get('販売戸数', ''); r['most_common_price_band_raw'] = sd.get('最多価格帯', '')
                r['management_fee_raw'] = sd.get('管理費（月額）', ''); r['repair_reserve_raw'] = sd.get('修繕積立金（月額）', ''); r['repair_fund_lump_raw'] = sd.get('修繕積立基金（一括）', '')
                r['other_fees_raw'] = sd.get('その他', '')
        o0 = f.find(' 物件概要 所在地 ')
        if o0 > 0:
            o1 = f.find(' 会社情報 ', o0); od = labelled(f[o0 + 6:o1], MAN_OVER_L)
            r['units_total'] = od.get('総戸数', ''); r['structure_raw'] = od.get('構造、建物階数', ''); r['land_area_raw'] = od.get('敷地面積', ''); r['zoning_raw'] = od.get('用途地域', '')
            r['land_rights_raw'] = od.get('敷地の権利形態', ''); r['completion_raw'] = od.get('完成時期', ''); r['builder_raw'] = od.get('施工会社', '')
            if od.get('入居可能時期'): r['handover_raw'] = od['入居可能時期']
            ci = f[o1:o1 + 3000]
            m = re.search(r'［売主］\s*(.+?)\s*〒', ci)
            if m: r['seller_raw'] = m.group(1)
            m = re.search(r'［販売提携（代理）］\s*(.+?)\s*〒', ci)
            if m and not r['company_raw']: r['company_raw'] = m.group(1)
    p = man(r['price_raw'])
    if p: r['price_min_man'], r['price_max_man'] = min(p), max(p)
    miss = [c for c in EXPECT[t['target_type']] if not r[c]]
    r['missing_fields'] = ';'.join(miss)
    r['status'] = 'ok' if r['price_min_man'] != '' else ('ok_price_undisclosed' if r['price_raw'] else 'ok_no_price')
    return r

def main():
    rows = []
    parse_only = '--parse-only' in sys.argv
    for t in targets():
        try:
            meta, x = (load(t['url']) if parse_only else fetch(t['url']))
        except Stop as e:
            print('STOP', e); meta, x = None, None
            if not parse_only: break
        if x is None:
            r = {c: '' for c in COLS}; r.update(target_type=t['target_type'], url=t['url'], status='not_fetched'); rows.append(r); continue
        rows.append(parse(t, x))
    with open(OUT, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); w.writerows(rows)
    print(f'{len(rows)} rows -> {OUT}; requests logged: {count_logged()}')

if __name__ == '__main__' and '--fetch-only' in sys.argv:
    n = int(sys.argv[sys.argv.index('--fetch-only') + 1])
    for t in targets()[:n]:
        try: fetch(t['url']); print('ok', t['url'])
        except Stop as e: print('STOP', e); break
    sys.exit()

if __name__ == '__main__': main()
