#!/usr/bin/env python3
"""Validate Sensync JSON records and consequential cross-field business invariants."""
from __future__ import annotations
import argparse,json,re,sys
from datetime import date,datetime
from pathlib import Path
from urllib.parse import urlparse

SCHEMA=Path(__file__).resolve().parents[1]/'assets/company-record.schema.json'

def check_shape(value,schema,path='$'):
    if 'anyOf' in schema:
        for choice in schema['anyOf']:
            try:check_shape(value,choice,path);return
            except ValueError:pass
        raise ValueError(path+': no allowed shape')
    if 'const' in schema and value!=schema['const']:raise ValueError(path+': wrong constant')
    if 'enum' in schema and value not in schema['enum']:raise ValueError(path+': invalid value')
    types=schema.get('type',[]);types=[types] if isinstance(types,str) else types
    valid={'null':value is None,'object':isinstance(value,dict),'array':isinstance(value,list),'string':isinstance(value,str),'boolean':isinstance(value,bool),'integer':isinstance(value,int) and not isinstance(value,bool),'number':isinstance(value,(int,float)) and not isinstance(value,bool)}
    if types and not any(valid.get(t,False) for t in types):raise ValueError(path+': wrong type')
    if isinstance(value,dict):
        missing=set(schema.get('required',[]))-set(value)
        if missing:raise ValueError(path+': missing '+','.join(sorted(missing)))
        props=schema.get('properties',{})
        if schema.get('additionalProperties') is False and set(value)-set(props):raise ValueError(path+': unexpected fields')
        for k,v in value.items():
            if k in props:check_shape(v,props[k],path+'.'+k)
    elif isinstance(value,list):
        if len(value)<schema.get('minItems',0) or len(value)>schema.get('maxItems',float('inf')):raise ValueError(path+': wrong item count')
        for i,v in enumerate(value):check_shape(v,schema.get('items',{}),f'{path}[{i}]')
    elif isinstance(value,str):
        if len(value)<schema.get('minLength',0):raise ValueError(path+': empty required text')
        if 'pattern' in schema and not re.search(schema['pattern'],value):raise ValueError(path+': invalid pattern')
        fmt=schema.get('format')
        if fmt=='date':date.fromisoformat(value)
        elif fmt=='date-time':
            parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
            if parsed.tzinfo is None:raise ValueError(path+': timestamp needs timezone')
        elif fmt=='uri':
            u=urlparse(value)
            if u.scheme not in ('http','https') or not u.netloc:raise ValueError(path+': expected source HTTP URL')
    elif isinstance(value,(int,float)) and not isinstance(value,bool):
        if value<schema.get('minimum',-float('inf')) or value>schema.get('maximum',float('inf')):raise ValueError(path+': out of range')

def unique(items,key,label):
    keys=[x[key] for x in items]
    if len(keys)!=len(set(keys)):raise ValueError('Duplicate '+label)
    return set(keys)

def validate(record):
    check_shape(record,json.loads(SCHEMA.read_text(encoding='utf-8')))
    sources={s['id']:s for s in record['sources']}
    unique(record['sources'],'id','source ID')
    opp_ids=unique(record['opportunities'],'opportunity_id','opportunity ID')
    contact_ids=unique(record['contacts'],'contact_id','contact ID')
    def refs(ids):
        if set(ids)-set(sources):raise ValueError('Unknown source ID')
    for o in record['opportunities']:
        refs(o['source_ids']);refs(o['scoring_evidence_ids']);refs(o['purchase_intent_source_ids']);refs(o['competition']['source_ids'])
        if o['purchase_intent']=='EXPLICIT_SIGNAL' and not o['purchase_intent_source_ids']:raise ValueError('Explicit intent has no source')
        if o['competition']['status'] in ('CONFIRMED','POSSIBLE') and (not o['competition']['source_ids'] or not o['competition']['product_lines'] or not o['competition']['description']):raise ValueError('Competition label lacks evidence/scope')
        fact_ids=unique(o['facts'],'id','fact ID')
        unique(o['inferences'],'id','inference ID')
        for fact in o['facts']+o['negative_evidence']:
            refs(fact['source_ids'])
            if not fact['source_ids']:raise ValueError('Fact has no evidence')
        for inf in o['inferences']:
            if not inf['supports'] or set(inf['supports'])-fact_ids:raise ValueError('Inference lacks supporting facts')
        decisions=[g['decision'] for g in o['hard_gates'].values()]
        for gate in o['hard_gates'].values():refs(gate['source_ids'])
        if record['known_customer_list_state']=='NOT_PROVIDED' and o['hard_gates']['known_customer']['decision']!='UNKNOWN':raise ValueError('Missing historical list must remain UNKNOWN')
        if o['qualification_status']=='DUPLICATE':continue
        if 'FAIL' in decisions or 'UNKNOWN' in decisions:
            if o['score_status']!='NOT_SCORED' or o['score'] is not None or any(v is not None for v in o['components'].values()):raise ValueError('Blocked gates cannot be scored')
            expected='REJECTED' if 'FAIL' in decisions else 'REVIEW'
            if o['qualification_status']!=expected:raise ValueError('Gate/status conflict')
        else:
            if o['score_status']!='SCORED' or o['score'] is None or any(v is None for v in o['components'].values()):raise ValueError('Passed gates need component scores')
            if abs(sum(o['components'].values())-o['score'])>0.0001:raise ValueError('Score does not equal component sum')
            expected='QUALIFIED' if o['score']>=75 else 'REVIEW' if o['score']>=60 else 'REJECTED'
            if o['qualification_status']!=expected:raise ValueError('Threshold/status conflict')
            selected=[sources[i] for i in o['source_ids']]
            if len({s['independence_group'] for s in selected})<2 or not any(s['source_tier']!='S5' for s in selected):raise ValueError('Insufficient independent evidence')
            if not o['scoring_evidence_ids']:raise ValueError('Scores need evidence')
        band='BORDERLINE' if o['qualification_status']=='QUALIFIED' and 75<=o['score']<80 else 'STANDARD' if o['qualification_status']=='QUALIFIED' else 'NOT_APPLICABLE'
        if o['qualification_band']!=band:raise ValueError('Qualification band mismatch')
    scoped=[o for o in record['opportunities'] if o['in_batch_scope']]
    if record['qualification_status']=='QUALIFIED' and not any(o['qualification_status']=='QUALIFIED' for o in scoped):raise ValueError('Company has no qualified in-scope opportunity')
    for c in record['contacts']:
        if set(c['opportunity_ids'])-opp_ids:raise ValueError('Unknown contact opportunity')
        refs(c['relationship_source_ids']);refs(c['email_source_ids'])
        if c['contact_type']=='GENERIC_CHANNEL' and (c['name'] is not None or c['email_confidence'] not in ('E1','E0','NOT_EVALUATED')):raise ValueError('Generic inbox misattributed')
        if c['contact_type']=='PERSON' and c['name'] and not c['relationship_source_ids']:raise ValueError('Named contact needs identity evidence')
        if c['email_confidence'] in ('E4','E5') and (not c['email'] or not c['email_source_ids']):raise ValueError('Published personal email lacks source')
        if c['email_confidence'] in ('E2','E3') and (not c['email_source_ids'] or not c['pattern_example_dates']):raise ValueError('Pattern inference needs examples/dates')
        if c['contact_currency']!='CURRENT' and not c['reverify_title_before_send']:raise ValueError('Contact needs re-verification flag')
        checks=c['technical_checks']
        if any(checks[k] not in ('UNKNOWN','NOT_AVAILABLE') for k in ('syntax','mx','smtp','catch_all')) and (not checks['tool'] or not checks['checked_at'] or not checks['result']):raise ValueError('Technical verification lacks actual result metadata')
    draft=record['email_draft']
    if draft:
        if draft['opportunity_id'] not in opp_ids or draft['contact_id'] not in contact_ids:raise ValueError('Draft references missing opportunity/contact')
        chosen=next(o for o in record['opportunities'] if o['opportunity_id']==draft['opportunity_id'])
        if not chosen['in_batch_scope']:raise ValueError('Draft changed product scope')
        if draft['recommended_subject'] not in draft['subject_options']:raise ValueError('Recommended subject not among options')
        if not draft['evidence_used']:raise ValueError('Draft has no evidence')
        refs(draft['evidence_used'])
        if len(draft['body'].split())!=draft['body_word_count']:raise ValueError('Draft body word count mismatch')
    elif record['draft_requested'] and not record['draft_blockers']:raise ValueError('Requested draft absent without blocker')
    if record['research_completeness']=='COMPLETE':
        if record['completeness_blockers']:raise ValueError('COMPLETE has blockers')
        if any(g['decision']!='PASS' for o in scoped for g in o['hard_gates'].values()):raise ValueError('COMPLETE has unresolved gates')
        if any(c['contact_currency']!='CURRENT' or c['email_confidence']=='NOT_EVALUATED' for c in record['contacts']):raise ValueError('COMPLETE has uncompleted contact research')
        if record['draft_requested'] and not draft:raise ValueError('COMPLETE missing requested draft')
    return True

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',type=Path);a=p.parse_args()
    try:
        data=json.loads(a.input.read_text(encoding='utf-8'))
        records=data if isinstance(data,list) else [data]
        if not records:raise ValueError('No records supplied')
        ids=set()
        for i,r in enumerate(records):
            try:validate(r)
            except Exception as e:raise ValueError(f'Record {i+1}: {e}') from e
            key=(r['run_id'],r['lead_id'])
            if key in ids:raise ValueError('Repeated company ID within run')
            ids.add(key)
        print('VALID_RECORDS:',len(records));return 0
    except Exception as e:print('INVALID:',str(e),file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
