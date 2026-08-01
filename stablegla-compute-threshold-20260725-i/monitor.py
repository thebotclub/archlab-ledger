#!/usr/bin/env python3
import json,math,os,pathlib,statistics,time
R=pathlib.Path(__file__).resolve().parent;m=json.load(open(R/'campaign.json'))
def alive(p):
 try:os.kill(int(p.read_text()),0);return True
 except:return False
while True:
 out={};failed=[]
 for c in m['cells']:
  d=R/c['id'];f=d/'result.json'
  if f.exists():
   try:
    rows=json.load(open(f))['results']
    if len(rows)==len(m['seeds']):out[c['id']]=rows
   except Exception as e:failed.append(c['id']+':invalid:'+type(e).__name__)
  elif not alive(d/'pid'):failed.append(c['id']+':exited-without-result')
 if failed:
  (R/'decision.json').write_text(json.dumps({'campaign':R.name,'status':'INCOMPLETE_FAILED','claim_eligible':False,'failures':failed},indent=2)+'\n');break
 if len(out)==4:
  s={k:{'recall_mean':statistics.mean(r['recall'] for r in v),'recall_min':min(r['recall'] for r in v),'long_mean':statistics.mean(r['recall_long'] for r in v),'loss_mean':statistics.mean(r['final_loss'] for r in v),'n':len(v)} for k,v in out.items()}
  gain=s['stable_3e15']['recall_mean']-s['stable_1e15']['recall_mean']; threshold=s['stable_3e15']['recall_mean']>=.20 and gain>=.10
  result={'campaign':R.name,'claim_eligible':False,'summary':s,'stable_compute_gain':gain,'generic_gla_compute_gain':s['gla_3e15']['recall_mean']-s['gla_1e15']['recall_mean'],'decision':'COMPUTE_THRESHOLD_SUPPORTED' if threshold else 'ARCHITECTURE_OR_REGIME_LIMITED','status':'DIAGNOSTIC_COMPLETE','completed_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
  (R/'decision.json').write_text(json.dumps(result,indent=2)+'\n');break
 time.sleep(20)
