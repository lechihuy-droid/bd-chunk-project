"""Extract conservative, public-advertised selection features."""
import math,re,unicodedata

def norm(x): return re.sub(r'\s+','',unicodedata.normalize('NFKC',str(x or '')))

def station_pairs(raw):
    text=unicodedata.normalize('NFKC',str(raw or ''))
    pattern=r'([^/／\n、,]+?)「([^」]+)」\s*徒歩\s*(\d+)\s*分(?!\s*(?:[～〜~\-]|から))'
    pairs=[]
    for m in re.finditer(pattern,text):
        line=norm(m.group(1)); station=norm(m.group(2))
        if not line or not station or re.search(r'バス|bus|自動車|車',line,re.I): continue
        if not re.search(r'線|鉄道|JR|阪堺',line,re.I): continue
        minutes=int(m.group(3))
        if minutes<1: continue
        pairs.append({'line':line,'station':station,'minutes':minutes,'key':line+'|'+station})
    return sorted(pairs,key=lambda p:(p['minutes'],p['key']))

def classify_priority(asking,access):
    if asking is None or access is None:return 'U'
    return 'P1' if asking and access else 'P2' if asking or access else 'P3'

def features(f):
    fields=f.get('fields') or {}; hints=f.get('scope_hints') or {}; conflicts=f.get('conflicts') or []
    ids={e.get('id') for e in f.get('evidence',[]) if e.get('id') and not e.get('conflicts')}
    def supported(k):return any(i in ids for i in (fields.get(k) or {}).get('evidence_ids',[]))
    def val(k):return (fields.get(k) or {}).get('value')
    def conflicted(k):return any(k in str(c.get('field','')) for c in conflicts if isinstance(c,dict))
    def number(k):
        v=val(k)
        return v if type(v) in (int,float) and math.isfinite(v) and v>0 and not conflicted(k) and supported(k) else None
    raw_rights=str(val('rights') or '') if supported('rights') and not conflicted('rights') else ''; tenure='ownership' if norm(raw_rights)=='所有権' else 'leasehold' if re.search('借地|賃借|地上権',raw_rights) else None
    flags=list(dict.fromkeys(hints.get('advertised_risk_flags') or []));
    if tenure=='leasehold' and 'leasehold_claim' not in flags:flags.append('leasehold_claim')
    material=[]
    if any(any(k in str(c.get('field','')) for k in ('price','address','ward','category','listing_level','occupancy','handover')) for c in conflicts if isinstance(c,dict)):material.append('material_claim_conflict')
    patterns={'private_road_claim':r'\u79c1\u9053','setback_claim':r'\u30bb\u30c3\u30c8\u30d0\u30c3\u30af','leasehold_claim':r'\u501f\u5730|\u8cc3\u501f|\u5730\u4e0a\u6a29','terrace_claim':r'\u30c6\u30e9\u30b9\u30cf\u30a6\u30b9|\u9023\u68df','no_rebuild_claim':r'\u518d\u5efa\u7bc9\u4e0d\u53ef|\u518d\u5efa\u7bc9\u3067\u304d\u306a\u3044','tenanted_claim':r'\u8cc3\u8cb8\u4e2d|\u30aa\u30fc\u30ca\u30fc\u30c1\u30a7\u30f3\u30b8'}
    flag_details={}
    for flag in patterns:
        pattern=patterns.get(flag)
        if not pattern:continue
        hits=[]
        for k in ('title','rights','road','setback','occupancy','handover','structure','zoning','renovation','coverage_far','completion','energy','insulation','utility_estimate','management_fee','repair_fee','lease_fee','sale_units','total_units','floor','floor_structure','advertised_price'):
            field=fields.get(k) or {}; raw=field.get('raw'); value=field.get('value'); text=str(value or raw or '')
            scoped_text=re.sub(r'\u79c1\u9053(?:\u8ca0\u62c5)?(?:\u306f)?\u306a\u3057|\u30bb\u30c3\u30c8\u30d0\u30c3\u30af(?:\u306f)?\u306a\u3057','',text) if flag in ('private_road_claim','setback_claim') else text
            if supported(k) and re.search(pattern,scoped_text):hits.append({'field':k,'excerpt':text[:300],'evidence_ids':field.get('evidence_ids') or []})
        if hits and flag not in flags:flags.append(flag)
        if flag in flags:flag_details[flag]=hits
        if flag in ('no_rebuild_claim','tenanted_claim') and flag in flags:
            # Negation or absent scoped provenance is a question for review, not a positive claim.
            negated=any(re.search(r'ではない|ではありません|でない|不明|未確認',hit['excerpt']) for hit in hits)
            material.append(flag if hits and not negated else 'claim_needs_review')
    material=list(dict.fromkeys(material))
    pairs=[] if conflicted('station_raw') or not supported('station_raw') else station_pairs(val('station_raw'))
    cat=val('category'); price=number('price_jpy'); unit=number('unit_m2'); land=number('land_m2'); building=number('building_m2');year=number('built_year')
    if year is not None and (year<1800 or year>2026 or int(year)!=year):year=None
    field_refs={k:(fields.get(k) or {}).get('evidence_ids',[]) for k in ('price_jpy','station_raw','unit_m2','land_m2','building_m2','built_year','rights')}
    fees={k:{'value':val(k),'evidence_ids':(fields.get(k) or {}).get('evidence_ids',[])} for k in ('management_fee','repair_fee','lease_fee') if isinstance(val(k),dict) and supported(k) and not conflicted(k)}
    evidence=f.get('evidence') or []; detail=any(str(e.get('id','')).startswith('detail:') for e in evidence)
    coverage='detail_scanned' if detail else 'scan_failed' if any((fields.get(k) or {}).get('missing_reason')=='fetch_failed' for k in ('rights','road')) else 'catalog_only'
    return {'source_valid':all(supported(k) and not conflicted(k) for k in ('category','listing_level','address','ward','price_jpy')),'url':f.get('listing_url'), 'category':cat,'level':val('listing_level'),'price_kind':hints.get('price_kind'),'price':price,'ward':norm(val('ward')),'address':norm(val('address')),'title':norm(val('title')),'layout':norm(val('layout')),'floor':norm(val('floor')),'year':year,'unit':unit,'land':land,'building':building,'station_pairs':pairs,'station_key':pairs[0]['key'] if pairs else None,'walk_minutes':pairs[0]['minutes'] if pairs else None,'tenure':tenure,'flags':flags,'flag_details':flag_details,'material_review_reasons':material,'coverage':coverage,'availability':f.get('availability') or 'not_checked','conflicts':conflicts,'field_refs':field_refs,'fees':fees,'rights_raw':raw_rights,'observed_at':val('observed_at')}
