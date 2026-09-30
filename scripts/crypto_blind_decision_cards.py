#!/usr/bin/env python3
import json
from pathlib import Path
SRC=Path('research/crypto_blind/review'); OUT=Path('research/crypto_blind/cards'); OUT.mkdir(parents=True,exist_ok=True)
KEYS=['lastClose','rsi14','change7dPct','change30dPct','change90dPct','ma20','ma50','ma100','ma200','closeVsMa20Pct','closeVsMa50Pct','atr14Pct','quoteVolumeVs20dAvg','range20','range60','range180']
for p in sorted(SRC.glob('C*.json')):
    d=json.load(open(p,encoding='utf-8'))
    o={'schema':'CRYPTO_BLIND_DECISION_CARD_V1','caseId':d['caseId'],'cutoff':d['cutoff'],'futureIncluded':False,'assets':{}}
    for sym,a in d['assets'].items():
        x={k:a.get(k) for k in KEYS}
        x['daily15']=a['daily45'][-15:]
        x['weekly8']=a['weekly20'][-8:]
        x['monthly6']=a['monthly18'][-6:]
        o['assets'][sym]=x
    (OUT/p.name).write_text(json.dumps(o,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS','count':len(list(OUT.glob('C*.json')))}))
