"""Pure exploratory gate evaluation; E1 claims never verify a purchase."""
from __future__ import annotations
import json
import math
import re
from typing import Any

FLAG_PATTERNS={
    'private_road_claim':r'私道', 'setback_claim':r'セットバック',
    'leasehold_claim':r'借地権|定期借地', 'terrace_claim':r'テラスハウス|連棟',
    'no_rebuild_claim':r'再建築不可|再建築できない',
    'tenanted_claim':r'賃貸中|オーナーチェンジ',
}
G5_CHECKS=('private_finance_and_funding','seller_and_property_rights','land_road_building_and_risk',
           'verified_comparables_costs_and_scenarios','terms_deposit_handover_and_insurance')

def evaluate_practical(facts:dict, policy:dict, *, shortlisted:bool=False, buyer_profile:dict|None=None)->dict:
    fields=facts.get('fields') or {}; hints=facts.get('scope_hints') or {}; conflicts=facts.get('conflicts') or []
    evidence={e.get('id'):e for e in facts.get('evidence',[]) if isinstance(e,dict) and e.get('id')}
    def val(k): return (fields.get(k) or {}).get('value')
    def refs(k): return [x for x in (fields.get(k) or {}).get('evidence_ids',[]) if x in evidence and not evidence[x].get('conflicts')]
    def conflict(*names):
        return any(any(n in str(c.get('field','')) for n in names) if isinstance(c,dict) else any(n in str(c) for n in names) for c in conflicts)
    def gate(status,reason): return {'status':status,'reason_code':reason}
    url=facts.get('listing_url') or ''; address=val('address') or ''; category=val('category') or ''; level=val('listing_level') or ''; price=val('price_jpy'); kind=hints.get('price_kind') or ''
    availability=facts.get('availability') or 'not_checked'; flags=sorted(set(hints.get('advertised_risk_flags') or [])); holds=[]
    project=level in ('project','project_level','project_or_range') or kind in ('range','project','undisclosed_project')
    valid_price=type(price) in (int,float) and math.isfinite(price) and price>0 and bool(refs('price_jpy')) and kind=='exact'
    is_city=isinstance(address,str) and ('大阪市' in address or 'osaka city' in address.lower())
    is_outside=isinstance(address,str) and (('\u5927\u962a\u5e9c' in address and '\u5e02' in address and '\u5927\u962a\u5e02' not in address) or (address.startswith('\u6771\u4eac\u90fd') and '\u533a' in address))
    recognized=category in ('used_house','new_house','used_condo','new_condo')
    candidate=level in ('unverified_unit','unit','single_unit','unit_level')
    if is_outside and refs('address') and not conflict('address','ward'):
        scope='out_of_scope';g1=gate('OUT_OF_SCOPE','outside_osaka_city')
    elif project:
        scope='project_queue';g1=gate('PROJECT_QUEUE','project_or_range')
    elif conflict('address','ward') or not refs('address') or not address:
        scope='scope_review';g1=gate('HOLD','address_missing_or_conflict')
    elif not is_city:
        scope='scope_review';g1=gate('HOLD','location_unclear')
    elif conflict('price','advertised_price','listing_level','category'):
        scope='scope_review';g1=gate('HOLD','scope_conflict')
    elif not url or not candidate or not recognized or not refs('listing_level') or not refs('category'):
        scope='scope_review';g1=gate('HOLD','listing_identity_or_type_unclear')
    elif not valid_price:
        scope='scope_review';g1=gate('HOLD','price_unclear')
    elif not policy['price_min_jpy']<=price<=policy['price_max_jpy']:
        scope='out_of_scope';g1=gate('OUT_OF_SCOPE','price_outside_preference')
    else:
        scope='in_scope';g1=gate('RESEARCH_PASS','public_scope_satisfied')
    if conflict('price','advertised_price','listing_level','category','address','ward','occupancy','handover'):
        holds.append('material_claim_conflict')
    if 'tenanted_claim' in flags: holds.append('tenanted_owner_use_needs_review')
    if 'no_rebuild_claim' in flags and (buyer_profile or {}).get('confirmed_rebuild_required') is True:
        holds.append('rebuild_requirement_needs_review')
    if (buyer_profile or {}).get('confirmed_mandatory_mismatch') is True: holds.append('confirmed_requirement_mismatch')
    g2=gate('HOLD','material_claim_or_need_requires_review') if holds else gate('RESEARCH_PASS','public_claims_screened_not_verified') if scope=='in_scope' else gate('NOT_EVALUATED','scope_not_ready')
    def positive(k):
        x=val(k)
        return type(x) in (int,float) and math.isfinite(x) and x>0 and bool(refs(k)) and not conflict(k)
    condo=category in ('used_condo','new_condo'); house=category in ('used_house','new_house')
    comparable_area=(condo and positive('unit_m2')) or (house and (positive('land_m2') or positive('building_m2')))
    station=bool(val('station_raw') and refs('station_raw') and not conflict('station_raw'))
    prerequisites=g1['status']=='RESEARCH_PASS' and g2['status']=='RESEARCH_PASS'
    ready=bool(prerequisites and (comparable_area or station or shortlisted is True))
    g3=gate('RESEARCH_READY','public_basics' if comparable_area or station else 'user_shortlist') if ready else gate('HOLD','comparison_inputs_missing') if prerequisites else gate('NOT_EVALUATED','earlier_research_gate_not_passed')
    g4=gate('NOT_EVALUATED','research_priority_not_assessed' if ready else 'research_not_ready')
    def rate(k,applicable): return round(price/val(k),2) if applicable and valid_price and not project and not conflict('price','advertised_price') and positive(k) else None
    rates={'unit':rate('unit_m2',condo),'land':rate('land_m2',house),'building':rate('building_m2',house)}
    flag_evidence={}
    for flag in flags:
        pattern=FLAG_PATTERNS.get(flag)
        flag_evidence[flag]=sorted(eid for eid,e in evidence.items() if pattern and e.get('level')=='E1' and re.search(pattern,json.dumps(e.get('raw_claim'),ensure_ascii=False,default=str)))
    evidence_ids=sorted({i for key in ('address','ward','category','listing_level','price_jpy','unit_m2','land_m2','building_m2','station_raw') for i in refs(key)})
    history=hints.get('availability_history') or []; checked=next((h.get('observed_at') for h in reversed(history) if isinstance(h,dict) and h.get('observed_at')),None)
    actions=['unverified_legal_technical_financial']
    if ready: actions.append('research_priority_not_assessed')
    if holds: actions.append('review_material_claim_or_confirmed_need')
    if not ready and prerequisites: actions.append('add_area_station_or_shortlist')
    if availability!='active': actions.append('verify_link_availability')
    return {'listing_url':url,'policy_version':policy['policy_version'],'scope_status':scope,'availability':availability,
            'gates':{'G1':g1,'G2':g2,'G3':g3,'G4':g4,'G5':gate('REVIEW','purchase_verification_not_performed')},
            'flags':flags,'flag_evidence':flag_evidence,'hold_reasons':holds,'research_ready':ready,
            'shortlist_eligible':prerequisites,'map_eligible':bool(ready and availability=='active'),
            'buy_verified':False,'score_total':None,'price_per_m2':rates,'next_actions':actions,
            'evidence_references':evidence_ids,'observed_at':val('observed_at'),'availability_checked_at':checked,
            'g5_checklist':[{'criterion_id':x,'status':'REVIEW'} for x in G5_CHECKS]}
