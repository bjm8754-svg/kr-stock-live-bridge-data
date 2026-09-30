#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

BASE=Path('research/stock_blind')
active=json.loads((BASE/'ACTIVE_EPISODE.json').read_text(encoding='utf-8'))
root=BASE/'episodes'/str(active['episodeId'])
card=json.loads((root/'current_card.json').read_text(encoding='utf-8'))
outdir=root/'readouts'
outdir.mkdir(parents=True,exist_ok=True)


def slim_money(m):
    m=m or {}
    return {k:m.get(k) for k in (
        'currentTradingValue','avg20TradingValueEstimated','tradingValueRatio20',
        'volumeRatio20','pullbackMoneyContraction','quality'
    ) if k in m}


def slim_primary(c):
    p=((c.get('setups') or {}).get('primary') or {})
    return {k:p.get(k) for k in ('family','state','reference','evidence') if k in p}


def slim_exec(c):
    e=c.get('execution') or {}
    keys=(
        'readiness','entryReference','entryZoneLow','entryZoneHigh','currentToEntryPct',
        'noChaseAbove','structuralInvalidation','stop','nearestAcceptedSupport',
        'nextResistance','target','currentStructuralRR','plannedStructuralRR','warnings'
    )
    return {k:e.get(k) for k in keys if k in e}


def slim_levels(c):
    levels=((c.get('structure') or {}).get('levels') or [])
    core=[x for x in levels if x.get('importance')=='CORE']
    src=core if core else levels
    src=src[:8]
    return [{k:x.get(k) for k in ('line','zoneLow','zoneHigh','role','importance','evidenceCount','strength','kinds') if k in x} for x in src]


def trace_summary(c):
    tr=((c.get('review') or {}).get('chartTrace') or {})
    daily=tr.get('daily') or []
    weekly=tr.get('weekly') or []
    monthly=tr.get('monthly') or []
    return {'daily12':daily[-12:],'weekly8':weekly[-8:],'monthly6':monthly[-6:]}


def fmt(v):
    if v is None:return '-'
    if isinstance(v,float):return f'{v:.2f}'
    return str(v).replace('\t',' ').replace('\n',' ')

rows=[]
summary=[]
for c in card.get('deepReviewCandidates') or []:
    aid=c.get('assetId')
    row={
        'assetId':aid,'market':c.get('market'),'price':c.get('price'),'ma':c.get('ma'),
        'money':slim_money(c.get('money')),'primary':slim_primary(c),
        'confirmation':c.get('confirmation'),'execution':slim_exec(c),
        'levels':slim_levels(c),'trace':trace_summary(c),
    }
    rows.append(row)
    (outdir/f'{aid}.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    p=c.get('price') or {}; ma=c.get('ma') or {}; m=c.get('money') or {}
    pri=((c.get('setups') or {}).get('primary') or {}); e=c.get('execution') or {}
    tr=((c.get('review') or {}).get('chartTrace') or {}).get('daily') or []
    closes=[x[4] for x in tr[-12:] if isinstance(x,list) and len(x)>4]
    vols=[x[5] for x in tr[-6:] if isinstance(x,list) and len(x)>5]
    core=slim_levels(c)
    coretxt=';'.join(f"{fmt(x.get('line'))}:{fmt(x.get('role'))}" for x in core[:4])
    summary.append('\t'.join([
        fmt(aid),fmt(c.get('market')),f"px={fmt(p.get('close'))}",f"atr={fmt(p.get('atrPct'))}",
        f"ma20={fmt(ma.get('20'))}",f"ma60={fmt(ma.get('60'))}",f"ma120={fmt(ma.get('120'))}",f"ma240={fmt(ma.get('240'))}",
        f"tvR={fmt(m.get('tradingValueRatio20'))}",f"volR={fmt(m.get('volumeRatio20'))}",
        f"setup={fmt(pri.get('family'))}/{fmt(pri.get('state'))}",f"ready={fmt(e.get('readiness'))}",
        f"entry={fmt(e.get('entryReference'))}",f"dist={fmt(e.get('currentToEntryPct'))}%",
        f"support={fmt(e.get('nearestAcceptedSupport'))}",f"stop={fmt(e.get('structuralInvalidation') if e.get('structuralInvalidation') is not None else e.get('stop'))}",
        f"res={fmt(e.get('nextResistance'))}",f"RR={fmt(e.get('currentStructuralRR'))}/{fmt(e.get('plannedStructuralRR'))}",
        'closes='+','.join(fmt(x) for x in closes),'vol6='+','.join(fmt(x) for x in vols),'levels='+coretxt,
    ]))

held=[]
for c in card.get('heldPositionAnalysis') or []:
    held.append({'assetId':c.get('assetId'),'price':c.get('price'),'ma':c.get('ma'),
        'money':slim_money(c.get('money')),'primary':slim_primary(c),
        'execution':slim_exec(c),'levels':slim_levels(c),
        'chartTrace':(c.get('chartTrace') or {}).get('daily',[])[-30:]})

digest={'schema':'KOREA_STOCK_BLIND_DIGEST','episodeId':card.get('episodeId'),'step':card.get('step'),
    'relativeSession':card.get('relativeSession'),'futureIncluded':False,
    'portfolioState':card.get('portfolioState'),'coverage':card.get('coverage'),
    'candidateCount':len(rows),'candidates':rows,'held':held}
(outdir/'current_digest.json').write_text(json.dumps(digest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# Human-readable bounded comparison: market context last 12 closes + exactly one line per candidate.
lines=[f"episode={card.get('episodeId')} step={card.get('step')} rel={card.get('relativeSession')} candidates={len(rows)}"]
for label,ctx in (card.get('marketContext') or {}).items():
    d=ctx.get('daily') or []
    lines.append(f"MARKET\t{label}\tcloses="+','.join(fmt(x[4]) for x in d[-12:] if len(x)>4)+"\tvol="+','.join(fmt(x[5]) for x in d[-6:] if len(x)>5))
lines.append('CANDIDATES')
lines.extend(summary)
(outdir/'current_summary.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'status':'OK','episodeId':card.get('episodeId'),'step':card.get('step'),'candidates':len(rows)},ensure_ascii=False))
