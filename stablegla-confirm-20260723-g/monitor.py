#!/usr/bin/env python3
import itertools,json,math,os,pathlib,time
R=pathlib.Path('/home/hani/archlab-runs/stablegla-confirm-20260723-g')
def alive(p):
 try:os.kill(int(p.read_text()),0);return True
 except:return False
def signflip_p(ds):
 obs=sum(ds)/len(ds); n=len(ds)
 return sum(1 for signs in itertools.product((-1,1),repeat=n) if sum(s*d for s,d in zip(signs,ds))/n>=obs-1e-15)/(2**n)
while True:
 lanes=[];failed=[]
 for i in range(4):
  d=R/f'gpu{i}';f=d/'result.json';
  if f.exists():
   try:lanes.extend(json.load(open(f))['results'])
   except Exception as e:failed.append(f'gpu{i}:invalid:{type(e).__name__}')
  elif not alive(d/'pid'):failed.append(f'gpu{i}:exited-without-result')
 if failed:
  (R/'decision.json').write_text(json.dumps({'campaign':R.name,'status':'INCOMPLETE_FAILED','failures':failed,'claim_eligible':False},indent=2)+'\n');break
 if len(lanes)==16:
  by={}
  for x in lanes:by.setdefault(x['seed'],{})[x['arm']]=x
  if len(by)!=8 or any(set(v)!=set(('gla','stablegla')) for v in by.values()):
   (R/'decision.json').write_text(json.dumps({'campaign':R.name,'status':'INCOMPLETE_PAIRING','claim_eligible':False},indent=2)+'\n');break
  pairs=[]
  for seed,v in sorted(by.items()):
   delta=v['stablegla']['recall']-v['gla']['recall'];pairs.append({'seed':seed,'gla':v['gla']['recall'],'stablegla':v['stablegla']['recall'],'delta':delta})
  ds=[p['delta'] for p in pairs]; cm=sum(p['stablegla'] for p in pairs)/8
  gates={'complete_finite_pairs':len(ds)==8 and all(math.isfinite(x) for x in ds),'mean_delta_ge_0_10':sum(ds)/8>=.10,'one_sided_exact_signflip_p_le_0_025':signflip_p(ds)<=.025,'positive_pairs_ge_7':sum(x>0 for x in ds)>=7,'worst_pair_ge_minus_0_10':min(ds)>=-.10,'candidate_mean_interior_0_20_0_90':.20<=cm<=.90}
  out={'campaign':R.name,'stage':'sealed paired confirmation','claim_eligible':True,'pairs':pairs,'mean_delta':sum(ds)/8,'candidate_recall_mean':cm,'positive_pairs':sum(x>0 for x in ds),'worst_pair_delta':min(ds),'one_sided_exact_signflip_p':signflip_p(ds),'gates':gates,'status':'PASS' if all(gates.values()) else 'FAIL','completed_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
  (R/'decision.json').write_text(json.dumps(out,indent=2)+'\n');break
 time.sleep(15)
