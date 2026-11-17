"""Wave 2: list-page crawl of non-SUUMO sources, Osaka-shi, 4,000-5,000万.
One process per site, one request at a time, >=3s apart, stops on 401/403/429 or a challenge page.
Usage: crawl_wave2.py <site> <workdir> [--parse-only]"""
import csv, html, json, os, re, subprocess, sys, time, hashlib, datetime

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
WARDS = {102:'都島区',103:'福島区',104:'此花区',106:'西区',107:'港区',108:'大正区',109:'天王寺区',111:'浪速区',113:'西淀川区',114:'東淀川区',115:'東成区',116:'生野区',117:'旭区',118:'城東区',119:'阿倍野区',120:'住吉区',121:'東住吉区',122:'西成区',123:'淀川区',124:'鶴見区',125:'住之江区',126:'平野区',127:'北区',128:'中央区'}
LO, HI = 4000, 5000
FIELDS = ['source','listing_url','observed_at','category','price_jpy','price_raw','address','ward','building_name','floor','floors_total','direction','unit_m2','land_m2','building_m2','layout','built_year','built_month','station_raw','units_total','seller_type','company']

class Stop(Exception): pass

class Fetcher:
    def __init__(s, site, work, parse_only, limit):
        s.dir = os.path.join(work, 'raw', site); os.makedirs(s.dir, exist_ok=True)
        s.log = open(os.path.join(work, f'requests-{site}.log'), 'a'); s.n = 0; s.parse_only = parse_only; s.limit = limit
    def get(s, url, enc='utf-8'):
        path = os.path.join(s.dir, hashlib.sha1(url.encode()).hexdigest()[:16] + '.html')
        if not os.path.exists(path):
            if s.parse_only: return None, None
            if s.n >= s.limit: raise Stop(f'request limit {s.limit} reached')
            time.sleep(3.2); s.n += 1
            r = subprocess.run(['curl','-sS','-L','-m','40','--compressed','-A',UA,'-H','Accept-Language: ja','-o',path+'.tmp','-w','%{http_code}',url], capture_output=True, text=True)
            code = r.stdout.strip()[-3:]; ts = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            s.log.write(f'{ts} {code} {url}\n'); s.log.flush()
            if code in ('401','403','429') or code == '000': raise Stop(f'HTTP {code} at {url}')
            if code == '404': open(path, 'w').write(''); os.remove(path+'.tmp')
            else: os.rename(path+'.tmp', path)
            open(path+'.meta','w').write(json.dumps({'url':url,'fetched_at':ts,'status':code}))
        raw = open(path,'rb').read().decode(enc, errors='replace')
        if '認証中' in raw[:3000] or (0 < len(raw) < 500): raise Stop(f'challenge/empty page at {url}')
        return raw, json.load(open(path+'.meta'))['fetched_at']

def text(raw):
    raw = re.sub(r'<(script|style)[\s\S]*?</\1>', ' ', raw)
    raw = re.sub(r'<a\b[^>]*?href="([^"]+)"[^>]*>', lambda m: f' ⟦{html.unescape(m.group(1))}⟧ ', raw)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', raw)))
def man(s):
    s = s.replace(',', '').replace(' ', ''); m = re.match(r'(?:(\d+)億)?(\d*)', s)
    return int(m.group(1) or 0) * 10000 + int(m.group(2) or 0)
def ward_of(a):
    m = re.search(r'大阪市(\S+?区)', a or ''); return m.group(1) if m else ''
def row(source, url, at, cat, price_man, addr, **k):
    r = dict.fromkeys(FIELDS, ''); r.update(source=source, listing_url=url, observed_at=at, category=cat, price_jpy=price_man*10000, price_raw=f'{price_man}万円', address=addr, ward=ward_of(addr)); r.update({a: b for a, b in k.items() if b is not None}); return r
inband = lambda p: LO <= p <= HI
PRICE = r'((?:\d+ ?億 ?)?[\d,]*)'

# ---------- per-site: yields (rows, cards_seen, expected_total) per page ----------
def yahoo(f):
    for path, cat in (('used/mansion','used_condo'),('used/house','used_house'),('new/house','new_house')):
        page = 1; seen_ids = set()
        while True:
            url = f'https://realestate.yahoo.co.jp/{path}/search/06/27/271/?p_from={LO}0000&p_to={HI}0000' + (f'&page={page}' if page > 1 else '')
            raw, at = f.get(url)
            if raw is None: break
            x = text(raw); x = x[x.find('並び替え'):]; rows = []
            tot = re.search(r'([\d,]+) 件 並び替え', text(raw)); tot = int(tot.group(1).replace(',','')) if tot else None
            if cat == 'used_condo':
                for b in re.split(r'(?=大阪府大阪市\S+区\S* \d{4}年\d+月（築)', x)[1:]:
                    h = re.match(r'(大阪府大阪市\S+) (\d{4})年(\d+)月（築\d+年） (?:総戸数 (\d+)戸 / )?(?:地上(\d+)階建)?', b)
                    for u in re.finditer(r'⟦(https://realestate\.yahoo\.co\.jp/used/mansion/detail_corp/b\d+/)[^⟧]*⟧ (?:(?!⟦https://realestate\.yahoo\.co\.jp/used/mansion/detail_corp).){0,400}?(\d+)階 / (\S*?) ?/ ([\d.]+)m 2 / (\S+) (?:(?!万円).){0,120}?([\d,]+)万円', b):
                        p = man(u.group(6))
                        if inband(p): rows.append(row('yahoo', u.group(1), at, cat, p, h.group(1), built_year=h.group(2), built_month=h.group(3), units_total=h.group(4), floors_total=h.group(5), floor=u.group(2), direction=u.group(3), unit_m2=u.group(4), layout=u.group(5)))
            else:
                for m in re.finditer(r'⟦(https://realestate\.yahoo\.co\.jp/(?:used|new)/house/detail_corp/b\d+/)[^⟧]*⟧ (?:(?!⟦https://realestate\.yahoo\.co\.jp/(?:used|new)/house/detail_corp).){0,1500}?(大阪府大阪市\S+)(?: (\d{4})年(\d+)月\S*)? (\S+?)/(?:地上)?(\d+)階\S* 土地 ([\d.]+)m 2 / 建物 ([\d.]+)m 2 (?:(?!万円).){0,900}?([\d,]+)万円', x):
                    p = man(m.group(9))
                    if inband(p): rows.append(row('yahoo', m.group(1), at, cat, p, m.group(2), built_year=m.group(3), built_month=m.group(4), layout=m.group(5), floors_total=m.group(6), land_m2=m.group(7), building_m2=m.group(8)))
            ids = set(re.findall(r'/detail_corp/b\d+/', x))
            yield rows, len(ids), tot, url
            if not ids or ids <= seen_ids or page >= 8: break  # no pager links in static HTML: walk pages until nothing new
            seen_ids |= ids; page += 1

def stepon(f):
    for kind, cat in (('mansion','used_condo'),('kodate','used_house')):
        for w in WARDS:
            page = 1
            while True:
                url = f'https://www.stepon.co.jp/{kind}/area_27/list_27_{w}/?hanbaiKakakuMin={LO}&hanbaiKakakuMax={HI}' + (f'&page={page}' if page > 1 else '')
                raw, at = f.get(url, 'cp932')
                if not raw: break
                x = text(raw); tot = re.search(r'該当件数 (\d+) 件', x); tot = int(tot.group(1)) if tot else 0; rows = []
                if kind == 'mansion':
                    for m in re.finditer(r'⟦(https://www\.stepon\.co\.jp/mansion/detail_\w+/)⟧ ([^⟦]{1,80}?) PRICE 万円 (大阪府大阪市\S+) ([^⟦]{0,300}?) (\S+) / ([\d.]+) ㎡ / (\d{4})年(\d+)月築 / (\d+)階部分（(\S*?)）/ 地上(\d+)階建'.replace('PRICE', PRICE), x):
                        p = man(m.group(3))
                        if inband(p): rows.append(row('stepon', m.group(1), at, cat, p, m.group(4), building_name=m.group(2).strip(), station_raw=m.group(5).strip()[:160], layout=m.group(6), unit_m2=m.group(7), built_year=m.group(8), built_month=m.group(9), floor=m.group(10), direction=m.group(11), floors_total=m.group(12)))
                else:
                    for m in re.finditer(r'⟦(https://www\.stepon\.co\.jp/kodate/detail_\w+/)⟧ ([^⟦]{1,80}?) PRICE 万円 (大阪府大阪市\S+) ([^⟦]{0,300}?) (\S+) / 建物([\d.]+) ㎡ / 土地([\d.]+) ㎡ / (\d{4})年(\d+)月築'.replace('PRICE', PRICE), x):
                        p = man(m.group(3))
                        if inband(p): rows.append(row('stepon', m.group(1), at, cat, p, m.group(4), station_raw=m.group(5).strip()[:160], layout=m.group(6), building_m2=m.group(7), land_m2=m.group(8), built_year=m.group(9), built_month=m.group(10)))
                yield rows, len(set(re.findall(r'/%s/detail_\w+/' % kind, raw))), tot, url
                if tot <= page * 30 or f'page={page+1}' not in raw: break
                page += 1

def nomu(f):
    for kind, cat in (('mansion','used_condo'),('house','used_house'),('house_n','new_house')):
        page = 1
        while True:
            url = f'https://www.nomu.com/{kind}/area_osaka/271/?price_from={LO}&price_to={HI}' + (f'&pager_page={page}' if page > 1 else '')
            raw, at = f.get(url)
            if not raw: break
            x = text(raw); tot = re.search(r'([\d,]+) 件', x); tot = int(tot.group(1).replace(',','')) if tot else 0; rows = []
            if kind == 'mansion':
                for m in re.finditer(r'⟦(/mansion/id/\w+/)[^⟧]*⟧ (?:(?!⟦/mansion/id/).)*?((?:大阪府)?大阪市\S+区\S+) ((?:(?!万円).){0,200}?駅 \S+分(?:(?!万円).){0,80}?) (?:新価格 )?([\d,億]+) 万円 ([\d.]+)m 2 (\S+) (\S+) (\d{4})年(\d+)月 (\d+)階 / (\d+)階建 (?:(\d+)戸)?', x):
                    p = man(m.group(4))
                    if inband(p): rows.append(row('nomu', 'https://www.nomu.com'+m.group(1), at, cat, p, m.group(2), station_raw=m.group(3).strip()[:160], unit_m2=m.group(5), layout=m.group(6), direction=m.group(7), built_year=m.group(8), built_month=m.group(9), floor=m.group(10), floors_total=m.group(11), units_total=m.group(12)))
            else:
                for m in re.finditer(r'⟦(/%s/id/\w+/)[^⟧]*⟧ (?:(?!⟦/%s/id/).)*?((?:大阪府)?大阪市\S+区\S+) ((?:(?!万円).){0,260}?) ([\d,億]+) 万円 ([\d.]+)m 2 ([\d.]+)m 2 (?:(\d{4})年(\d+)月|\S+) (\S+)' % (kind, kind), x):
                    p = man(m.group(4))
                    if inband(p): rows.append(row('nomu', 'https://www.nomu.com'+m.group(1), at, cat, p, m.group(2), station_raw=m.group(3).strip()[:160], building_m2=m.group(5), land_m2=m.group(6), built_year=m.group(7), built_month=m.group(8), layout=m.group(9)))
            yield rows, len(set(re.findall(r'/%s/id/\w+/' % kind, raw))), tot, url
            if f'pager_page={page+1}' not in raw: break
            page += 1

def livable(f):
    for kind, cat in (('chuko-mansion','used_condo'),('chuko-kodate','used_house'),('shinchiku-kodate','new_house')):
        for w in WARDS:
            page = 1
            while True:
                url = f'https://www.livable.co.jp/kounyu/{kind}/osaka/a27{w}/?sort=price-asc' + (f'&page={page}' if page > 1 else '')
                raw, at = f.get(url)
                if not raw: break
                m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', raw, re.S)
                if not m: break
                pp = json.loads(m.group(1))['props']['pageProps']; pl = pp.get('propertyList') or []; rows = []; prices = []
                for it in pl:
                    p = (it.get('priceModel') or {}).get('price') or 0; prices.append(p)
                    if not inband(p // 10000): continue
                    d = ' '.join(re.sub(r'<[^>]+>', '', s) for s in it.get('propertyDetail') or [])
                    g = lambda pat: (re.search(pat, d) or [None, None])[1]
                    rows.append(row('livable', 'https://www.livable.co.jp' + it.get('detailUrl',''), at, cat, p // 10000, it.get('address',''), building_name=it.get('propertyName') if cat == 'used_condo' else '', station_raw=' / '.join(it.get('access') or [])[:160],
                        layout=d.split(' ')[0] if d else '', unit_m2=g(r'^\S+ ([\d.]+)m2') if cat == 'used_condo' else '', building_m2=g(r'建物[:：]?\s*([\d.]+)m2'), land_m2=g(r'土地[:：]?\s*([\d.]+)m2'),
                        built_year=g(r'(\d{4})年\d+月築'), built_month=g(r'\d{4}年(\d+)月築'), floor=g(r'(\d+)階／'), floors_total=g(r'／地上(\d+)階'), direction=g(r'(\S+)向き')))
                tot = pp.get('searchedResultCounts'); tot = tot if isinstance(tot, int) else None
                yield rows, len(pl), tot, url
                if len(pl) < 30: break  # the sort parameter is ignored by the site, so read every page
                page += 1

def rehouse(f):
    for kind, cat in (('mansion','used_condo'),('kodate','used_house')):
        for w in WARDS:
            page = 1
            while True:
                url = f'https://www.rehouse.co.jp/buy/{kind}/prefecture/27/city/27{w}/' + (f'?page={page}' if page > 1 else '')
                raw, at = f.get(url)
                if not raw: break
                x = text(raw); rows = []; n = 0
                tot = re.search(r'([\d,]+) ?件中', x); tot = int(tot.group(1).replace(',','')) if tot else None
                if kind == 'mansion':
                    for m in re.finditer(r'中古マンション ([^⟦]{1,80}?) PRICE 万円 (?:[^⟦/]{0,60} )?(大阪市[^ /]+) / ([^⟦]{0,200}?) (\S+) / ([\d.]+)㎡ / (\d{4})年(\d+)月築 / (\d+)階 ⟦(/buy/mansion/bkdetail/\w+/)⟧'.replace('PRICE', PRICE), x):
                        n += 1; p = man(m.group(2))
                        if inband(p): rows.append(row('rehouse', 'https://www.rehouse.co.jp'+m.group(10), at, cat, p, '大阪府'+m.group(3), building_name=m.group(1).strip(), station_raw=m.group(4).strip(), layout=m.group(5), unit_m2=m.group(6), built_year=m.group(7), built_month=m.group(8), floor=m.group(9)))
                else:
                    for m in re.finditer(r'(中古|新築)戸建 ([^⟦]{1,80}?) PRICE 万円 (?:[^⟦/]{0,60} )?(大阪市[^ /]+) / ([^⟦]{0,200}?) (\S+) / 建物([\d.]+)㎡ / 土地([\d.]+)㎡ / (?:(\d{4})年(\d+)月築|\S+) ⟦(/buy/kodate/bkdetail/\w+/)⟧'.replace('PRICE', PRICE), x):
                        n += 1; p = man(m.group(3))
                        if inband(p): rows.append(row('rehouse', 'https://www.rehouse.co.jp'+m.group(11), at, 'used_house' if m.group(1) == '中古' else 'new_house', p, '大阪府'+m.group(4), station_raw=m.group(5).strip(), layout=m.group(6), building_m2=m.group(7), land_m2=m.group(8), built_year=m.group(9), built_month=m.group(10)))
                cards = len(set(re.findall(r'/buy/%s/bkdetail/\w+/' % kind, raw)))
                yield rows, cards, tot, url + f' parsed={n}'
                if f'?page={page+1}' not in raw: break
                page += 1

def daikyo(f):
    for kind, cat in (('mansion','used_condo'),('house','used_house')):
        for w in WARDS:
            page = 1
            while True:
                url = f'https://www.daikyo-anabuki.co.jp/buy/{kind}/p27/c27{w}/' + (f'?page={page}' if page > 1 else '')
                raw, at = f.get(url)
                if not raw: break
                x = text(raw); tot = re.search(r'該当件数 (\d+) 件', x); tot = int(tot.group(1)) if tot else 0; rows = []; n = 0
                x = re.sub(r'⟦(?!/buy/detail/)[^⟧]*⟧ ?', '', x)
                if kind == 'mansion':
                    for m in re.finditer(r'⟦(/buy/detail/\w+/)⟧ ([^⟦]{1,200}?) (?:New \S+ )?中古マンション 価格 PRICE 万円 (?:新価格 \S+ )?住所 大阪府 (大阪市\S+区) (\S+) 交通 ([^⟦]{0,400}?) 間取り (\S+) 専有面積 ([\d.]+)m 2 築年 (\d{4})年(\d+)月 向き (\S+) 所在階 (\S+?)階 建物階数 地上(\d+)階(?: 地下\d+階)? 総戸数 (?:(\d+)戸|\S+)'.replace('PRICE', PRICE), x):
                        n += 1; p = man(m.group(3))
                        if inband(p): rows.append(row('daikyo', 'https://www.daikyo-anabuki.co.jp'+m.group(1), at, cat, p, '大阪府'+m.group(4)+m.group(5), building_name=m.group(2).strip(), station_raw=m.group(6).strip()[:160], layout=m.group(7), unit_m2=m.group(8), built_year=m.group(9), built_month=m.group(10), direction=m.group(11), floor=m.group(12), floors_total=m.group(13), units_total=m.group(14)))
                else:
                    for m in re.finditer(r'⟦(/buy/detail/\w+/)⟧ [^⟦]{1,200}? (中古|新築)一戸建\S* 価格 PRICE 万円 (?:新価格 \S+ )?住所 大阪府 (大阪市\S+区) (\S+) 交通 ([^⟦]{0,400}?) 間取り (\S+) 築年 (?:(\d{4})年(\d+)月|\S+) 建物面積 ([\d.]+)m 2 土地面積 ([\d.]+)m 2'.replace('PRICE', PRICE), x):
                        n += 1; p = man(m.group(3))
                        if inband(p): rows.append(row('daikyo', 'https://www.daikyo-anabuki.co.jp'+m.group(1), at, 'used_house' if m.group(2) == '中古' else 'new_house', p, '大阪府'+m.group(4)+m.group(5), station_raw=m.group(6).strip()[:160], layout=m.group(7), built_year=m.group(8), built_month=m.group(9), building_m2=m.group(10), land_m2=m.group(11)))
                yield rows, len(set(re.findall(r'/buy/detail/\w+/', x))), tot, url + f' parsed={n}'
                if tot <= page * 20 or f'page={page+1}' not in raw: break
                page += 1

SITES = {'yahoo': (yahoo, 20), 'stepon': (stepon, 80), 'nomu': (nomu, 20), 'livable': (livable, 160), 'rehouse': (rehouse, 200), 'daikyo': (daikyo, 100)}

if __name__ == '__main__':
    site, work = sys.argv[1], sys.argv[2]; fn, limit = SITES[site]
    f = Fetcher(site, work, '--parse-only' in sys.argv, limit); rows = []; pages = []; stop = ''
    try:
        for r, cards, tot, url in fn(f): rows += r; pages.append({'url': url, 'cards': cards, 'in_band_rows': len(r), 'site_total': tot})
    except Stop as e: stop = str(e)
    seen = {}; [seen.setdefault(r['listing_url'], r) for r in rows]; rows = list(seen.values())
    with open(os.path.join(work, f'listings-{site}.csv'), 'w', newline='', encoding='utf-8') as o:
        w = csv.DictWriter(o, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    json.dump({'site': site, 'requests_this_run': f.n, 'pages': pages, 'rows': len(rows), 'stopped': stop}, open(os.path.join(work, f'pages-{site}.json'), 'w'), ensure_ascii=False, indent=1)
    print(site, 'requests', f.n, 'pages', len(pages), 'rows', len(rows), 'STOP: ' + stop if stop else '')
