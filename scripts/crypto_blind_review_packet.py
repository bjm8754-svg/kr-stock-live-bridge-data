#!/usr/bin/env python3
from __future__ import annotations
import json, math
from pathlib import Path

CASES=Path('research/crypto_blind/cases')
OUT=Path('research/crypto_blind/review')
OUT.mkdir(parents=True, exist_ok=True)

def sma(xs,n):
    return None if len(xs)<n else sum(xs[-n:])/n

def atr(rows,n=14):
    if len(rows)<n+1: return None
    trs=[]
    for a,b in zip(rows[-n-1:-1], rows[-n:]):
        trs.append(max(b['high']-b['low'], abs(b['high']-a['close']), abs(b['low']-a['close'])))
    return sum(trs)/n

def pct(a,b):
    return None if not b else (a/b-1)*100

def pos(last, rows, n):
    rs=rows[-n:] if len(rows)>=n else rows
    hi=max(x['high'] for x in rs); lo=min(x['low'] for x in rs)
    p=None if hi==lo else (last-lo)/(hi-lo)*100
    return {'high':round(hi,4),'low':round(lo,4),'positionPct':None if p is None else round(p,2)}

def compress(rows):
    return [[r['date'],round(r['open'],4),round(r['high'],4),round(r['low'],4),round(r['close'],4),round(r.get('quoteVolume',0),2)] for r in rows]

def build_asset(a):
    d=a['daily']; closes=[x['close'] for x in d]; last=d[-1]['close']; at=atr(d)
    qv=[x.get('quoteVolume',0) for x in d]
    v20=(sum(qv[-20:])/20) if len(qv)>=20 else None
    return {
      'lastClose':a['lastClose'],'rsi14':a['rsi14'],
      'change7dPct':a['change7dPct'],'change30dPct':a['change30dPct'],'change90dPct':a['change90dPct'],
      'ma20':round(sma(closes,20),4) if sma(closes,20) else None,
      'ma50':round(sma(closes,50),4) if sma(closes,50) else None,
      'ma100':round(sma(closes,100),4) if sma(closes,100) else None,
      'ma200':round(sma(closes,200),4) if sma(closes,200) else None,
      'closeVsMa20Pct':round(pct(last,sma(closes,20)),2) if sma(closes,20) else None,
      'closeVsMa50Pct':round(pct(last,sma(closes,50)),2) if sma(closes,50) else None,
      'atr14Pct':round(at/last*100,2) if at else None,
      'quoteVolumeVs20dAvg':round(qv[-1]/v20,2) if v20 else None,
      'range20':pos(last,d,20),'range60':pos(last,d,60),'range180':pos(last,d,180),
      'daily45':compress(d[-45:]),
      'weekly20':compress(a['weekly'][-20:]),
      'monthly18':compress(a['monthly'][-18:]),
    }

manifest=json.load(open(CASES/'manifest.json',encoding='utf-8'))
idx=[]
for meta in manifest['cases']:
    d=json.load(open(CASES/meta['file'],encoding='utf-8'))
    out={'schema':'CRYPTO_BLIND_REVIEW_PACKET_V1','caseId':d['caseId'],'cutoff':d['cutoff'],'futureIncluded':False,'assets':{}}
    for sym,a in d['assets'].items(): out['assets'][sym]=build_asset(a)
    p=OUT/f"{d['caseId']}.json"; p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    idx.append({'caseId':d['caseId'],'cutoff':d['cutoff'],'file':p.name})
(OUT/'manifest.json').write_text(json.dumps({'schema':'CRYPTO_BLIND_REVIEW_INDEX_V1','futureIncluded':False,'cases':idx},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS','count':len(idx)}))
