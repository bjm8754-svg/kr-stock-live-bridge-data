#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

BASE = Path('research/stock_blind')
active = json.loads((BASE / 'ACTIVE_EPISODE.json').read_text(encoding='utf-8'))
root = BASE / 'episodes' / active['episodeId']
card = json.loads((root / 'current_card.json').read_text(encoding='utf-8'))
summary_path = root / 'current_card_summary.json'
table_path = root / 'current_card_decision_table.json'
matrix_path = root / 'current_card_matrix.json'
detail_dir = root / 'current_details'
detail_dir.mkdir(parents=True, exist_ok=True)
for p in detail_dir.glob('*.json'):
    p.unlink()


def review_trace(x):
    return ((x.get('review') or {}).get('chartTrace') or {})


def detail_item(x):
    trace = review_trace(x)
    simple = x.get('chartTrace') or {}
    return {
        'assetId': x.get('assetId'),
        'market': x.get('market'),
        'price': x.get('price'),
        'money': x.get('money'),
        'ma': x.get('ma'),
        'primarySetup': (x.get('setups') or {}).get('primary'),
        'confirmation': x.get('confirmation'),
        'execution': x.get('execution'),
        'warnings': x.get('warnings'),
        'levels': (x.get('structure') or {}).get('levels') or [],
        'reviewTier': (x.get('review') or {}).get('reviewTier'),
        'daily': (trace.get('daily') or [])[-60:],
        'weekly': (trace.get('weekly') or [])[-30:],
        'monthly': (trace.get('monthly') or [])[-18:],
        'heldDaily': (simple.get('daily') or [])[-60:],
    }


def matrix_row(x, held=False):
    primary = (x.get('setups') or {}).get('primary') or {}
    conf = x.get('confirmation') or {}
    exe = x.get('execution') or {}
    rsi = conf.get('rsi') or {}
    price = x.get('price') or {}
    money = x.get('money') or {}
    daily = review_trace(x).get('daily') or []
    if held and not daily:
        daily = (x.get('chartTrace') or {}).get('daily') or []
    return {
        'assetId': x.get('assetId'),
        'market': x.get('market'),
        'close': price.get('close'),
        'closeLocation': price.get('closeLocation'),
        'atrPct': price.get('atrPct'),
        'ma20': (x.get('ma') or {}).get('20'),
        'ma60': (x.get('ma') or {}).get('60'),
        'ma120': (x.get('ma') or {}).get('120'),
        'moneyRatio20': money.get('tradingValueRatio20Estimated'),
        'volumeRatio20': money.get('volumeRatio20'),
        'family': primary.get('family'),
        'state': primary.get('state'),
        'readiness': exe.get('readiness'),
        'entryReference': exe.get('entryReference'),
        'currentVsEntryPct': exe.get('currentVsEntryPct'),
        'invalidation': exe.get('invalidation'),
        'nearestAcceptedSupport': exe.get('nearestAcceptedSupport'),
        'nextResistance': exe.get('nextResistance'),
        'riskPct': exe.get('riskPct'),
        'rewardPct': exe.get('rewardPct'),
        'structuralRR': exe.get('structuralRR'),
        'rsi': rsi.get('value'),
        'rsiDirection': rsi.get('direction'),
        'warnings': sorted(set((x.get('warnings') or []) + (exe.get('warnings') or []) + (conf.get('warnings') or []))),
        'last3': daily[-3:],
    }

candidates = card.get('deepReviewCandidates') or []
held = card.get('heldPositionAnalysis') or []

summary = {
    'schema': 'KOREA_STOCK_BLIND_CARD_SUMMARY',
    'episodeId': card.get('episodeId'),
    'step': card.get('step'),
    'relativeSession': card.get('relativeSession'),
    'futureIncluded': card.get('futureIncluded'),
    'portfolioState': card.get('portfolioState'),
    'coverage': card.get('coverage'),
    'decisionContract': card.get('decisionContract'),
    'marketContext': card.get('marketContext'),
    'candidates': [detail_item(x) for x in candidates],
    'heldAnalysis': [detail_item(x) for x in held],
}

table = {
    'schema': 'KOREA_STOCK_BLIND_DECISION_TABLE',
    'episodeId': card.get('episodeId'),
    'step': card.get('step'),
    'relativeSession': card.get('relativeSession'),
    'futureIncluded': card.get('futureIncluded'),
    'portfolioState': card.get('portfolioState'),
    'coverage': card.get('coverage'),
    'candidates': [matrix_row(x) | {'detailFile': f"current_details/{x.get('assetId')}.json"} for x in candidates],
    'heldAnalysis': [matrix_row(x, held=True) | {'detailFile': f"current_details/{x.get('assetId')}.json"} for x in held],
}

matrix = {
    'schema': 'KOREA_STOCK_BLIND_MATRIX',
    'episodeId': card.get('episodeId'),
    'step': card.get('step'),
    'relativeSession': card.get('relativeSession'),
    'futureIncluded': card.get('futureIncluded'),
    'portfolioState': card.get('portfolioState'),
    'coverage': card.get('coverage'),
    'candidates': [matrix_row(x) for x in candidates],
    'heldAnalysis': [matrix_row(x, held=True) for x in held],
}

if any(x.get('futureIncluded') is not False for x in (summary, table, matrix)):
    raise RuntimeError('summary source is not blind')

summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
table_path.write_text(json.dumps(table, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
matrix_path.write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

for x in candidates + held:
    aid = x.get('assetId')
    if not aid:
        continue
    payload = {
        'schema': 'KOREA_STOCK_BLIND_CANDIDATE_DETAIL',
        'episodeId': card.get('episodeId'),
        'step': card.get('step'),
        'relativeSession': card.get('relativeSession'),
        'futureIncluded': False,
        'detail': detail_item(x),
    }
    (detail_dir / f'{aid}.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

print(json.dumps({'status':'PASS','matrix':str(matrix_path),'candidates':len(candidates),'held':len(held)}, ensure_ascii=False))

# refresh marker: S01 step 3
