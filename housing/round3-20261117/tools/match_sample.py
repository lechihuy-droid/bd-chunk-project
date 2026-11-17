import re,html,csv,unicodedata,sys,json
P=__import__('os').path.join(__import__('os').path.dirname(__file__),'..','wave0','properties.csv')
props=list(csv.DictReader(open(P)))
def na(a):
    a=unicodedata.normalize('NFKC',a or '').replace('大阪府','').replace(' ','')
    a=re.sub(r'(\d+)丁目.*',r'\1',a); a=re.sub(r'(\d+)[-−ー].*',r'\1',a); return a
f2=lambda s:f'{float(s):.2f}' if s else ''
idx={}
for p in props:
    cat='condo' if 'condo' in p['category'] else 'house'
    areas=(f2(p['unit_m2']),) if cat=='condo' else (f2(p['land_m2']),f2(p['building_m2']))
    idx.setdefault((cat,)+areas,[]).append(p)
def match(cat,addr,areas,year=None):
    c=idx.get((cat,)+tuple(f2(a) for a in areas),[])
    exact=[p for p in c if na(p['address'])==na(addr)]
    if exact: return 'match'
    ward=re.search(r'大阪市(\S+?区)',addr or '')
    near=[p for p in c if ward and p['ward']==ward.group(1) and (not year or not p['built_year'] or p['built_year']==str(year))]
    return 'probable' if near else 'new'
def text(f,enc='utf-8'): 
    t=open(f,'rb').read().decode(enc,errors='replace')
    return re.sub(r'\s+',' ',html.unescape(re.sub(r'<(script|style)[\s\S]*?</\1>|<[^>]+>',' ',t)))
