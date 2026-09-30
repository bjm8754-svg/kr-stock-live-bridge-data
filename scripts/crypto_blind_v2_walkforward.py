#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt, hashlib, json, random, time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

REPO=Path('.')
BASE_ROOT=REPO/'research/crypto_blind_v2'
ACTIVE=BASE_ROOT/'ACTIVE_EPISODE.json'
BASE='https://data-api.binance.vision/api/v3/klines'
SYMS=('BTCUSDT','ETHUSDT')
EPISODE_DAYS=120
STEP_DAYS=5
MAX_DECISIONS=EPISODE_DAYS//STEP_DAYS
START_FETCH=dt.date(2019,1,1)
END_FETCH=dt.date(2025,12,31)

def load_active():
    if not ACTIVE.exists():
        return {'episodeId':'E01_LEGACY','seed':560219,'legacy':True}
    c=json.load(open(ACTIVE,encoding='utf-8'))
    eid=str(c['episodeId']).strip()
    seed=int(c['seed'])
    if not eid or '/' in eid or '..' in eid: raise RuntimeError('invalid episodeId')
    return {'episodeId':eid,'seed':seed,'legacy':False}

CFG=load_active()
SEED=CFG['seed']
ROOT=BASE_ROOT if CFG['legacy'] else BASE_ROOT/'episodes'/CFG['episodeId']
DEC=ROOT/'decisions'
OUT=ROOT/'current_card.json'
STATE=ROOT/'state.json'
RESULT=ROOT/'FINAL_RESULT.json'

def ms(d): return int(dt.datetime(d.year,d.month,d.day,tzinfo=dt.timezone.utc).timestamp()*1000)
def fetch_all(sym):
    rows=[]; cur=ms(START_FETCH); end=ms(END_FETCH+dt.timedelta(days=1))-1
    while cur<=end:
        q=urlencode({'symbol':sym,'interval':'1d','startTime':cur,'endTime':end,'limit':1000})
        with urlopen(Request(f'{BASE}?{q}',headers={'User-Agent':'blind-v2/1.0'}),timeout=30) as r: batch=json.loads(r.read())
        if not batch: break
        for x in batch:
            d=dt.datetime.fromtimestamp(x[0]/1000,tz=dt.timezone.utc).date()
            rows.append({'date':d,'open':float(x[1]),'high':float(x[2]),'low':float(x[3]),'close':float(x[4]),'qv':float(x[7])})
        nxt=int(batch[-1][0])+86400000
        if nxt<=cur: break
        cur=nxt; time.sleep(.03)
    return rows

def blocked_ranges():
    blocked=[]
    v1_path=REPO/'research/crypto_blind/results.json'
    if v1_path.exists():
        v1=json.load(open(v1_path,encoding='utf-8'))
        for c in v1.get('cases',[]):
            blocked.append((dt.date.fromisoformat(c['entryDate']),dt.date.fromisoformat(c['endDate'])))
    finals=[]
    legacy=BASE_ROOT/'FINAL_RESULT.json'
    if legacy.exists(): finals.append(legacy)
    ep_root=BASE_ROOT/'episodes'
    if ep_root.exists(): finals.extend(ep_root.glob('*/FINAL_RESULT.json'))
    for p in finals:
        try:
            r=json.load(open(p,encoding='utf-8'))
            s=dt.date.fromisoformat(r['revealedStartDate'])
            blocked.append((s,s+dt.timedelta(days=EPISODE_DAYS)))
        except Exception:
            pass
    return blocked

def pick_start(common):
    blocked=blocked_ranges(); cands=[]
    for d in common:
        if d<dt.date(2019,7,1) or d+dt.timedelta(days=EPISODE_DAYS)>END_FETCH: continue
        ep=(d,d+dt.timedelta(days=EPISODE_DAYS))
        if any(not(ep[1]<a or ep[0]>b) for a,b in blocked): continue
        cands.append(d)
    if not cands: raise RuntimeError('no unseen episode')
    return random.Random(SEED).choice(cands)

def rsi(rows,n=14):
    if len(rows)<n+1:return None
    ds=[rows[i]['close']-rows[i-1]['close'] for i in range(len(rows)-n,len(rows))]
    g=sum(max(x,0) for x in ds)/n; l=sum(max(-x,0) for x in ds)/n
    return 100.0 if l==0 else 100-100/(1+g/l)
def avg(xs): return sum(xs)/len(xs) if xs else None
def atrp(rows,n=14):
    if len(rows)<n+1:return None
    trs=[]
    for i in range(len(rows)-n,len(rows)):
        r,p=rows[i],rows[i-1]['close']; trs.append(max(r['high']-r['low'],abs(r['high']-p),abs(r['low']-p)))
    return avg(trs)/rows[-1]['close']*100

def norm_rows(rows,base,start,limit):
    z=rows[-limit:]; out=[]
    for idx,r in z:
        pos=rows.index((idx,r)); h=[x[1]['qv'] for x in rows[max(0,pos-19):pos+1]]
        rel=r['qv']/avg(h) if h else 1
        out.append([idx,round(r['open']/base*100,3),round(r['high']/base*100,3),round(r['low']/base*100,3),round(r['close']/base*100,3),round(rel,3)])
    return out

def aggregate(indexed,base,block,count):
    use=indexed[-block*count:]; out=[]
    for k in range(0,len(use),block):
        g=use[k:k+block]
        if not g:continue
        out.append([g[-1][0],round(g[0][1]['open']/base*100,3),round(max(x[1]['high'] for x in g)/base*100,3),round(min(x[1]['low'] for x in g)/base*100,3),round(g[-1][1]['close']/base*100,3)])
    return out[-count:]

def card_for(data,start,step):
    cutoff=start+dt.timedelta(days=step*STEP_DAYS)
    payload={'schema':'CRYPTO_BLIND_V2_CARD','episodeId':CFG['episodeId'],'step':step,'relativeDay':step*STEP_DAYS,'futureIncluded':False,'assets':{}}
    for s,rows in data.items():
        by={r['date']:r for r in rows}; base=by[start]['close']; hist=[r for r in rows if r['date']<=cutoff]
        indexed=[((r['date']-start).days,r) for r in hist]
        last=hist[-1]['close']; closes=[r['close'] for r in hist]
        def ma(n): return avg(closes[-n:]) if len(closes)>=n else None
        def np(x): return None if x is None else round(x/base*100,3)
        def rng(n):
            z=hist[-n:]; hi=max(r['high'] for r in z); lo=min(r['low'] for r in z)
            return {'high':np(hi),'low':np(lo),'positionPct':round((last-lo)/(hi-lo)*100,2) if hi>lo else 50}
        payload['assets'][s]={'last':np(last),'rsi14':round(rsi(hist),2),'ma20':np(ma(20)),'ma50':np(ma(50)),'ma100':np(ma(100)),'atr14Pct':round(atrp(hist),2),'range20':rng(20),'range60':rng(60),'daily20':norm_rows(indexed,base,start,20),'weekly8':aggregate(indexed,base,7,8),'monthly6':aggregate(indexed,base,30,6)}
    return payload

def decisions():
    DEC.mkdir(parents=True,exist_ok=True); out=[]
    for p in sorted(DEC.glob('D*.json')): out.append(json.load(open(p,encoding='utf-8')))
    return out

def interval_value(sym,vehicle,capital,stop_norm,data,start,day0,day1):
    rows={r['date']:r for r in data[sym]}; base=rows[start]['close']; entry_date=start+dt.timedelta(days=day0); entry=rows[entry_date]['close']; value=capital; prev=entry; stopped=False; exit_rel=None
    for d in range(day0+1,day1+1):
        r=rows[start+dt.timedelta(days=d)]; stop_abs=stop_norm/100*base
        exitpx=None
        if r['open']<=stop_abs: exitpx=r['open']
        elif r['low']<=stop_abs: exitpx=stop_abs
        px=exitpx if exitpx is not None else r['close']; ret=px/prev-1
        value*= (px/prev) if vehicle=='SPOT' else max(0.0,1+2*ret)
        prev=px
        if exitpx is not None: stopped=True; exit_rel=d; break
    return value,stopped,exit_rel

def replay(data,start,decs,through_step):
    equity=10_000_000.0; history=[]
    for j in range(min(len(decs),through_step)):
        d=decs[j]; assert d['step']==j
        alloc=sum(x['capitalPct'] for x in d.get('portfolio',[])); assert alloc<=100.0001
        cash=equity*(100-alloc)/100; end=min((j+1)*STEP_DAYS,EPISODE_DAYS); sleeves=[]; total=cash
        for x in d.get('portfolio',[]):
            cap=equity*x['capitalPct']/100
            val,stopped,exit_rel=interval_value(x['symbol'],x['vehicle'],cap,x['stop'],data,start,j*STEP_DAYS,end)
            total+=val; sleeves.append({'symbol':x['symbol'],'vehicle':x['vehicle'],'capitalPct':x['capitalPct'],'startValue':round(cap,2),'endValue':round(val,2),'stopped':stopped,'stopDay':exit_rel})
        history.append({'step':j,'startEquity':round(equity,2),'endEquity':round(total,2),'returnPct':round((total/equity-1)*100,3),'sleeves':sleeves}); equity=total
    peak=10_000_000.0; mdd=0.0
    for h in history:
        peak=max(peak,h['endEquity']); mdd=min(mdd,h['endEquity']/peak-1)
    return equity,history,mdd*100

def main():
    data={s:fetch_all(s) for s in SYMS}; common=sorted(set(r['date'] for r in data[SYMS[0]]) & set(r['date'] for r in data[SYMS[1]])); start=pick_start(common)
    commit=hashlib.sha256(f"{CFG['episodeId']}|{start.isoformat()}|{SEED}|{EPISODE_DAYS}".encode()).hexdigest()
    decs=decisions(); step=len(decs)
    if step>MAX_DECISIONS: raise RuntimeError('too many decisions')
    equity,hist,mdd=replay(data,start,decs,step)
    state={'schema':'CRYPTO_BLIND_V2_STATE','episodeId':CFG['episodeId'],'step':step,'relativeDay':step*STEP_DAYS,'episodeCommitment':commit,'equityKrw':round(equity,2),'returnPct':round((equity/10_000_000-1)*100,3),'maxDrawdownPct':round(mdd,3),'previousInterval':hist[-1] if hist else None,'decisionsLocked':len(decs),'futureIncluded':False}
    ROOT.mkdir(parents=True,exist_ok=True); STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if step<MAX_DECISIONS:
        OUT.write_text(json.dumps(card_for(data,start,step),ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
        if RESULT.exists(): RESULT.unlink()
        print(json.dumps({'status':'READY','episodeId':CFG['episodeId'],'step':step,'relativeDay':step*STEP_DAYS,'episodeCommitment':commit,'equityKrw':round(equity,2)}))
    else:
        if OUT.exists(): OUT.unlink()
        result={'schema':'CRYPTO_BLIND_V2_FINAL','episodeId':CFG['episodeId'],'episodeCommitment':commit,'revealedStartDate':start.isoformat(),'initialCapitalKrw':10000000,'finalCapitalKrw':round(equity,2),'totalReturnPct':round((equity/10_000_000-1)*100,3),'maxDrawdownPct':round(mdd,3),'intervals':hist,'decisionCount':len(decs)}
        RESULT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'status':'FINAL','episodeId':CFG['episodeId'],'finalCapitalKrw':round(equity,2),'returnPct':result['totalReturnPct'],'mddPct':result['maxDrawdownPct']}))
if __name__=='__main__': main()
