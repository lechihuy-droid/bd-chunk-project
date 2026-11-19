"""Cross-listing, same-snapshot asking-price comparisons (not valuation)."""
from collections import defaultdict
from statistics import median

DUPLICATE_HEURISTIC='address-category-areas-year-layout-floor-v1'

def fingerprint(f):
    # Group cautiously, without price or mutable title, so duplicate ads cannot inflate n.
    return (f['address'],f['category'],f['unit'],f['land'],f['building'],f['year'],f['layout'],f['floor'])

def valid(f):
    cat=f['category']; return bool(f['source_valid'] and cat in ('used_condo','new_condo','used_house','new_house') and f['level'] in ('unverified_unit','unit','single_unit','unit_level') and f['price_kind']=='exact' and f['price'] and f['address'] and f['ward'] and f['station_key'] and (f['unit'] if 'condo' in cat else f['land'] and f['building']) and (not cat.startswith('used_') or f['year']) and not f['material_review_reasons'] and not any(x in f['flags'] for x in ('terrace_claim','leasehold_claim')) and f['tenure']!='leasehold' and f['availability'] not in ('not_found','expired'))

def compare(target, peers):
    groups=defaultdict(list); tfp=fingerprint(target)
    if valid(target):
        for p in peers:
            if not valid(p) or p['url']==target['url'] or fingerprint(p)==tfp:continue
            if (p['category'],p['ward'],p['station_key'])!=(target['category'],target['ward'],target['station_key']):continue
            if p['tenure'] and target['tenure'] and p['tenure']!=target['tenure']:continue
            keys=('unit',) if 'condo' in target['category'] else ('land','building')
            if any(not .8*target[k]<=p[k]<=1.2*target[k] for k in keys):continue
            if target['category'].startswith('used_') and abs(target['year']-p['year'])>10:continue
            groups[fingerprint(p)].append(p)
    selected=[sorted(g,key=lambda x:x['url'])[0] for _,g in sorted(groups.items(),key=lambda x:str(x[0]))]
    # Median within each property group prevents multiple URLs voting multiple times.
    values=[median(sorted({p['price']/p['unit'] if 'condo' in p['category'] else p['price'] for p in groups[fingerprint(r)]})) for r in selected]
    details=[]
    for representative,group_value in zip(selected,values):
        members=[{'url':p['url'],'metric':p['price']/p['unit'] if 'condo' in p['category'] else p['price'],'tenure':p['tenure'],'availability':p['availability']} for p in sorted(groups[fingerprint(representative)],key=lambda x:x['url'])]
        details.append({'group_metric':group_value,'members':members})
    reference=median(values) if len(values)>=5 else None
    own=(target['price']/target['unit'] if 'condo' in str(target['category']) else target['price']) if valid(target) else None
    return {'peer_url_count':sum(len(g) for g in groups.values()),'peer_group_count':len(groups),'peer_missing_rights_count':sum(any(p['tenure'] is None for p in groups[fingerprint(r)]) for r in selected),'peer_unknown_availability_count':sum(any(p['availability'] not in ('active','not_found','expired') for p in groups[fingerprint(r)]) for r in selected),'peer_match_tier':'BASIC_MATCHED' if reference else 'INSUFFICIENT','asking_ratio':own/reference if reference and own else None,'peer_evidence_refs':[r['url'] for r in selected], 'peer_groups':details, 'duplicate_heuristic':DUPLICATE_HEURISTIC, 'peer_median':reference}
