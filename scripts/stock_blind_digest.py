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
    # All dates are already blind-relative in current_card. Keep small tails only.
    return {'daily12':daily[-12:],'weekly8':weekly[-8:],'monthly6':monthly[-6:]}

rows=[]
for c in card.get('deepReviewCandidates') or []:
    aid=c.get('assetId')
    row={
        'assetId':aid,
        'market':c.get('market'),
        'price':c.get('price'),
        'ma':c.get('ma'),
        'money':slim_money(c.get('money')),
        'primary':slim_primary(c),
        'confirmation':c.get('confirmation'),
        'execution':slim_exec(c),
        'levels':slim_levels(c),
        'trace':trace_summary(c),
    }
    rows.append(row)
    # Candidate-specific readout preserves the entire already-blinded candidate object.
    (outdir/f'{aid}.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

held=[]
for c in card.get('heldPositionAnalysis') or []:
    held.append({
        'assetId':c.get('assetId'),'price':c.get('price'),'ma':c.get('ma'),
        'money':slim_money(c.get('money')),'primary':slim_primary(c),
        'execution':slim_exec(c),'levels':slim_levels(c),
        'chartTrace':(c.get('chartTrace') or {}).get('daily',[])[-30:],
    })

digest={
    'schema':'KOREA_STOCK_BLIND_DIGEST',
    'episodeId':card.get('episodeId'),'step':card.get('step'),
    'relativeSession':card.get('relativeSession'),'futureIncluded':False,
    'portfolioState':card.get('portfolioState'),
    'marketContext':card.get('marketContext'),
    'coverage':card.get('coverage'),
    'candidateCount':len(rows),'candidates':rows,'held':held,
}
(outdir/'current_digest.json').write_text(json.dumps(digest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'OK','episodeId':card.get('episodeId'),'step':card.get('step'),'candidates':len(rows)},ensure_ascii=False))
