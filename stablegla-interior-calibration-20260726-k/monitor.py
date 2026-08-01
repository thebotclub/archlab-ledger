#!/usr/bin/env python3
import json,os,pathlib,statistics,time
R=pathlib.Path(__file__).resolve().parent;m=json.load(open(R/'campaign.json'))
def alive(p):
 try: os.kill(int(p.read_text()),0); return True
 except: return False
while True:
 complete={}; failures=[]
 for panel in m['panels']:
  d=R/panel['id']; f=d/'result.json'
  if f.exists():
   try:
    rows=json.load(open(f))['results']
    if len(rows)==2*len(m['paired_init_data_seeds']): complete[panel['id']]=rows
    elif not alive(d/'pid'): failures.append(panel['id']+':partial-result')
   except Exception as e: failures.append(panel['id']+':invalid:'+type(e).__name__)
  elif not alive(d/'pid'): failures.append(panel['id']+':exited-without-result')
 if failures:
  tmp=R/'decision.json.tmp';tmp.write_text(json.dumps({'campaign':R.name,'status':'INCOMPLETE_FAILED','claim_eligible':False,'failures':failures},indent=2)+'\n');os.replace(tmp,R/'decision.json');break
 if len(complete)==len(m['panels']):
  summaries=[]
  for p in m['panels']:
   rows=complete[p['id']]; by={a:[r for r in rows if r['arm']==a] for a in ('gla','stablegla')}
   g=statistics.mean(r['recall'] for r in by['gla']);s=statistics.mean(r['recall'] for r in by['stablegla']); spread=s-g
   valid=(len(by['gla'])==3 and len(by['stablegla'])==3 and .2<=s<=.9 and g<=.8 and spread>=.1)
   summaries.append({'panel':p['id'],'mqar_pairs':p['mqar_pairs'],'gla_recall_mean':g,'stablegla_recall_mean':s,'stablegla_min':min(r['recall'] for r in by['stablegla']),'spread':spread,'valid':valid})
  valid=[x for x in summaries if x['valid']];selected=max(valid,key=lambda x:x['mqar_pairs'])['panel'] if valid else None
  result={'campaign':R.name,'stage':m['stage'],'claim_eligible':False,'panels':summaries,'selected_panel':selected,'status':'CALIBRATED' if selected else 'ASSAY_REPAIR_REQUIRED','completed_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
  tmp=R/'decision.json.tmp';tmp.write_text(json.dumps(result,indent=2)+'\n');os.replace(tmp,R/'decision.json');break
 time.sleep(20)
