"""Build immutable selection research outputs from cached public observations."""
import argparse,csv,hashlib,json,shutil,sqlite3
from collections import Counter,defaultdict
from datetime import datetime,timezone,date
from urllib.parse import urlsplit
from pathlib import Path
from gate_selection_features import features,classify_priority
from gate_selection_peers import compare,valid,DUPLICATE_HEURISTIC

EXTRA=('preset_id','selection_queue','material_review_reasons','conditional_flags','conditional_flag_details','advertised_fees','screening_coverage','priority_band','priority_reasons','asking_ratio','asking_signal','access_signal','walk_minutes','station_key','station_pairs','peer_url_count','peer_group_count','peer_missing_rights_count','peer_unknown_availability_count','peer_match_tier','peer_evidence_refs','peer_groups','peer_median','duplicate_heuristic','unknown_reasons','research_stage','research_stage_verified','research_stage_reviewer','research_stage_reviewed_at','research_stage_evidence','research_stage_record','formal_review_stage','next_actions')
def decide(f,legacy,peers):
    scope=legacy['scope_status'];availability=legacy['availability']; material=f['material_review_reasons']; flags=f['flags']; unknown=[]
    out={'preset_id':'BALANCED_ASKING_RAIL_V1','selection_queue':'OUTSIDE_SCOPE','material_review_reasons':material,'conditional_flags':flags,'conditional_flag_details':f['flag_details'],'advertised_fees':f['fees'],'screening_coverage':f['coverage'],'priority_band':'','priority_reasons':[], 'asking_ratio':None,'asking_signal':None,'access_signal':f['walk_minutes']<=10 if f['walk_minutes'] is not None else None,'walk_minutes':f['walk_minutes'],'station_key':f['station_key'],'station_pairs':f['station_pairs'],'peer_url_count':0,'peer_group_count':0,'peer_missing_rights_count':0,'peer_unknown_availability_count':0,'peer_match_tier':'NOT_ASSESSED','peer_evidence_refs':[],'peer_groups':[],'peer_median':None,'duplicate_heuristic':DUPLICATE_HEURISTIC,'unknown_reasons':unknown,'research_stage':'NOT_STARTED','research_stage_verified':False,'research_stage_reviewer':'','research_stage_reviewed_at':'','research_stage_evidence':[],'research_stage_record':{},'formal_review_stage':'NOT_STARTED','next_actions':[]}
    if scope!='in_scope':out['selection_queue']=scope.upper();return out
    if material:out['selection_queue']='MATERIAL_REVIEW';out['next_actions']=['review_material_claim'];return out
    if availability in ('not_found','expired'):out['selection_queue']='UNAVAILABLE';return out
    if availability!='active':out['selection_queue']='LINK_REVIEW';out['next_actions']=['verify_availability'];return out
    if f['tenure']=='leasehold' or 'terrace_claim' in flags:out['selection_queue']='SPECIALIST';out['priority_band']='SPECIALIST';out['unknown_reasons']=['tenure_specialist'];out['next_actions']=['review_specialist_rights_or_subtype'];return out
    out['selection_queue']='ORDINARY'
    if not f['tenure']:unknown.append('tenure_unknown')
    if not f['station_key']:unknown.append('station_unparsed')
    if not (f['unit'] if 'condo' in str(f['category']) else f['land'] and f['building']):unknown.append('area_missing')
    if str(f['category']).startswith('used_') and not f['year']:unknown.append('age_missing')
    if f['conflicts']:unknown.append('claim_conflict')
    comp=compare(f,peers);out.update(comp)
    if comp['asking_ratio'] is None and not unknown:unknown.append('peer_sample_thin')
    asking=comp['asking_ratio']<=1 if comp['asking_ratio'] is not None and not unknown else None
    out['asking_signal']=asking;out['priority_band']=classify_priority(asking,out['access_signal'])
    out['priority_reasons']=[('asking_at_or_below_peer_median' if asking else 'asking_above_peer_median') if asking is not None else 'asking_comparison_unknown', ('rail_walk_at_most_10m' if out['access_signal'] else 'rail_walk_over_10m') if out['access_signal'] is not None else 'rail_walk_unknown']
    out['next_actions']=['verify_asking_comparables_and_access'] if out['priority_band']!='U' else ['resolve_'+x for x in unknown]
    return out

def validate_research_stages(data, baseline, facts):
    if data.get('version')!='HOUSING-RESEARCH-STAGES-1.0' or not isinstance(data.get('records'),list):raise ValueError('invalid research stage store')
    result={}; allowed={'IN_RESEARCH','THESIS_SHORTLIST','COUNTEREVIDENCE','MATERIAL_REVIEW'}
    for r in data['records']:
        if not isinstance(r,dict):raise ValueError('invalid research stage record')
        u=r.get('listing_url'); stage=r.get('stage'); reviewer=r.get('reviewer'); reviewed=r.get('reviewed_at'); evidence=r.get('evidence')
        if u not in baseline or u in result or stage not in allowed or not isinstance(reviewer,str) or not reviewer.strip() or len(reviewer)>120:raise ValueError('invalid research stage identity')
        try:date.fromisoformat(reviewed)
        except (TypeError,ValueError):raise ValueError('invalid research review date')
        if not isinstance(evidence,list) or not evidence:raise ValueError('research stage evidence required')
        for item in evidence:
            if not isinstance(item,str):raise ValueError('invalid research evidence')
            v=urlsplit(item)
            if v.scheme!='https' or not v.netloc or v.username or v.password or v.query or v.fragment:raise ValueError('research evidence must be a public HTTPS URL')
        if stage=='THESIS_SHORTLIST':
            if baseline[u]['scope_status']!='in_scope' or facts[u]['material_review_reasons']:raise ValueError('thesis cannot bypass scope or material review')
            if any(not isinstance(r.get(k),str) or not r[k].strip() for k in ('asset_basis','asking_review','thesis','counterevidence','next_action')):raise ValueError('incomplete thesis review')
        result[u]=r
    return result

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def encoded(v):
    if isinstance(v,(list,dict)):return json.dumps(v,ensure_ascii=False,separators=(',',':'))
    if v is True:return 'true'
    if v is False:return 'false'
    return '' if v is None else v

def run(facts_path,baseline,policy_path,output,research_stages_path=None):
    facts_path,baseline,policy_path,output=map(Path,(facts_path,baseline,policy_path,output))
    if output.exists():raise FileExistsError(output)
    summary=json.loads((facts_path.parent/'summary.json').read_text(encoding='utf8')); prior=json.loads((baseline/'run-manifest.json').read_text(encoding='utf8')); policy=json.loads(policy_path.read_text(encoding='utf-8-sig'))
    if digest(facts_path)!=summary['facts_sha256'] or digest(facts_path)!=prior['input_hashes']['facts_sha256']:raise ValueError('facts lineage mismatch')
    expected={'policy_version':'HOUSING-SELECTION-3.0','preset_id':'BALANCED_ASKING_RAIL_V1','walk_minutes_max':10,'min_peer_groups':5,'area_ratio_min':0.8,'area_ratio_max':1.2,'used_year_delta_max':10,'duplicate_heuristic':DUPLICATE_HEURISTIC}
    if any(policy.get(k)!=v for k,v in expected.items()):raise ValueError('unsupported policy configuration')
    with (baseline/'listing-decisions.csv').open(encoding='utf8',newline='') as fh:
        reader=csv.DictReader(fh);legacy_fields=reader.fieldnames; old={r['listing_url']:r for r in reader}
    allfacts={}; index=defaultdict(list)
    with facts_path.open(encoding='utf8') as fh:
        for line in fh:
            fact=json.loads(line);u=fact['listing_url']; f=features(fact)
            if u in allfacts:continue
            allfacts[u]=f
            if valid(f):index[(f['category'],f['ward'],f['station_key'])].append(f)
    if set(old)!=set(allfacts):raise ValueError('facts and baseline URL sets differ')
    research_stages_path=Path(research_stages_path or Path(__file__).with_name('selection_research_stages.json'))
    research=validate_research_stages(json.loads(research_stages_path.read_text(encoding='utf-8-sig')),old,allfacts)
    output.mkdir(parents=True)
    for source in baseline.iterdir():
        if source.is_file():shutil.copy2(source,output/source.name)
    columns=[*legacy_fields,*EXTRA]; db=sqlite3.connect(output/'selection-evaluation.sqlite');db.execute('CREATE TABLE selection_decisions ('+','.join('"'+x+'" TEXT' for x in columns)+')');db.execute('CREATE UNIQUE INDEX selection_url ON selection_decisions(listing_url)')
    counts=Counter();categories=defaultdict(Counter)
    with (output/'selection-decisions.csv').open('w',encoding='utf8',newline='') as sf,(output/'peer-comparisons.csv').open('w',encoding='utf8',newline='') as pf,(output/'priority-diff.csv').open('w',encoding='utf8',newline='') as df:
        sw=csv.DictWriter(sf,fieldnames=columns);sw.writeheader();pc=['listing_url','category','priority_band','asking_ratio','peer_median','peer_url_count','peer_group_count','peer_missing_rights_count','peer_unknown_availability_count','peer_match_tier','peer_evidence_refs','peer_groups','duplicate_heuristic'];pw=csv.DictWriter(pf,fieldnames=pc);pw.writeheader();dw=csv.DictWriter(df,fieldnames=['listing_url','previous_G3','previous_G4','selection_queue','priority_band']);dw.writeheader()
        for u,legacy in old.items():
            f=allfacts[u]; d=decide(f,legacy,index[(f['category'],f['ward'],f['station_key'])]); r=research.get(u);
            if r:d.update({'research_stage':r['stage'],'research_stage_verified':True,'research_stage_reviewer':r['reviewer'],'research_stage_reviewed_at':r['reviewed_at'],'research_stage_evidence':r['evidence'],'research_stage_record':{k:r[k] for k in ('asset_basis','asking_review','thesis','counterevidence','next_action') if k in r}})
            row={**legacy,**d,'policy_version':policy['policy_version']};row={k:encoded(row.get(k)) for k in columns};sw.writerow(row);db.execute('INSERT INTO selection_decisions VALUES ('+','.join('?' for _ in columns)+')',[row[k] for k in columns]);pw.writerow({k:row.get(k,'') for k in pc});dw.writerow({'listing_url':u,'previous_G3':legacy['G3'],'previous_G4':legacy['G4'],'selection_queue':row['selection_queue'],'priority_band':row['priority_band']});counts[row['selection_queue']+(':'+row['priority_band'] if row['priority_band'] else '')]+=1;categories[legacy['category']][row['selection_queue']+(':'+row['priority_band'] if row['priority_band'] else '')]+=1
    db.commit();assert db.execute('pragma integrity_check').fetchone()[0]=='ok';db.close()
    manifest={'policy_version':policy['policy_version'],'preset':policy,'run_at_utc':datetime.now(timezone.utc).isoformat(),'mode':'offline_cached_facts','network_requests':0,'source_snapshot':'ver2.0-20261102','baseline_run':baseline.name,'url_count':len(old),'selection_counts':dict(counts),'category_counts':{k:dict(v) for k,v in categories.items()},'input_hashes':{'facts_sha256':digest(facts_path),'baseline_decisions_sha256':digest(baseline/'listing-decisions.csv'),'baseline_manifest_sha256':digest(baseline/'run-manifest.json'),'facts_summary_sha256':digest(facts_path.parent/'summary.json'),'research_stages_sha256':digest(research_stages_path),'catalog_sha256':summary['catalog_sha256'],'policy_sha256':digest(policy_path),'features_sha256':digest(Path(__file__).with_name('gate_selection_features.py')),'peers_sha256':digest(Path(__file__).with_name('gate_selection_peers.py')),'runner_sha256':digest(Path(__file__))},'limitations':['Asking prices, not transactions or valuations.','Peer rights and identity often unknown; references are heuristic.','Availability and listing observations are historical.','Priority is research order, not investment forecast or purchase verification.']}
    (output/'selection-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(output/'selection-quality-report.md').write_text('# Selection research run\n\n'+'\n'.join('- '+s for s in manifest['limitations'])+'\n\n```json\n'+json.dumps(manifest['selection_counts'],indent=2)+'\n```\n',encoding='utf8');return manifest
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--facts-cache',required=True);p.add_argument('--baseline',required=True);p.add_argument('--policy',required=True);p.add_argument('--output',required=True);p.add_argument('--research-stages');a=p.parse_args();print(json.dumps(run(a.facts_cache,a.baseline,a.policy,a.output,a.research_stages),ensure_ascii=False,indent=2))
