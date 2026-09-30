#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

BASE = Path('research/stock_blind')
active = json.loads((BASE / 'ACTIVE_EPISODE.json').read_text(encoding='utf-8'))
root = BASE / 'episodes' / active['episodeId']
card_path = root / 'current_card.json'
out_path = root / 'current_card_summary.json'
table_path = root / 'current_card_decision_table.json'

card = json.loads(card_path.read_text(encoding='utf-8'))


def compact_item(x):
    review = x.get('review') or {}
    trace = (review.get('chartTrace') or {}) if isinstance(review, dict) else {}
    daily = trace.get('daily') or []
    weekly = trace.get('weekly') or []
    monthly = trace.get('monthly') or []
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
        'levels': ((x.get('structure') or {}).get('levels') or [])[:12],
        'reviewTier': review.get('reviewTier') if isinstance(review, dict) else None,
        'dailyTail': daily[-30:],
        'weeklyTail': weekly[-20:],
        'monthlyTail': monthly[-12:],
    }


def compact_held(x):
    y = compact_item(x)
    simple = x.get('chartTrace') or {}
    if simple:
        y['heldDailyTail'] = (simple.get('daily') or [])[-40:]
    return y


def decision_row(x):
    primary = (x.get('setups') or {}).get('primary') or {}
    conf = x.get('confirmation') or {}
    exe = x.get('execution') or {}
    rsi = conf.get('rsi') or {}
    price = x.get('price') or {}
    money = x.get('money') or {}
    levels = (x.get('structure') or {}).get('levels') or []
    close = price.get('close')
    nearest = []
    if close is not None:
        def dist(lv):
            try:
                return abs(float(lv.get('line')) / float(close) - 1.0)
            except Exception:
                return 999
        nearest = sorted(levels, key=dist)[:5]
    review = x.get('review') or {}
    trace = review.get('chartTrace') or {}
    daily = trace.get('daily') or []
    return {
        'assetId': x.get('assetId'),
        'market': x.get('market'),
        'close': close,
        'closeLocation': price.get('closeLocation'),
        'atrPct': price.get('atrPct'),
        'ma': x.get('ma'),
        'moneyRatio20': money.get('tradingValueRatio20Estimated'),
        'volumeRatio20': money.get('volumeRatio20'),
        'family': primary.get('family'),
        'state': primary.get('state'),
        'triggerLevel': primary.get('triggerLevel'),
        'setupInvalidation': primary.get('invalidationLevel'),
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
        'nearestLevels': [
            {
                'line': lv.get('line'),
                'role': lv.get('role'),
                'importance': lv.get('importance'),
                'kinds': lv.get('kinds'),
            }
            for lv in nearest
        ],
        'dailyLast10': daily[-10:],
    }


def held_row(x):
    y = decision_row(x)
    simple = x.get('chartTrace') or {}
    y['heldDailyLast15'] = (simple.get('daily') or [])[-15:]
    return y

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
    'candidates': [compact_item(x) for x in (card.get('deepReviewCandidates') or [])],
    'heldAnalysis': [compact_held(x) for x in (card.get('heldPositionAnalysis') or [])],
}

table = {
    'schema': 'KOREA_STOCK_BLIND_DECISION_TABLE',
    'episodeId': card.get('episodeId'),
    'step': card.get('step'),
    'relativeSession': card.get('relativeSession'),
    'futureIncluded': card.get('futureIncluded'),
    'portfolioState': card.get('portfolioState'),
    'coverage': card.get('coverage'),
    'candidates': [decision_row(x) for x in (card.get('deepReviewCandidates') or [])],
    'heldAnalysis': [held_row(x) for x in (card.get('heldPositionAnalysis') or [])],
}

if summary['futureIncluded'] is not False or table['futureIncluded'] is not False:
    raise RuntimeError('summary source is not blind')

out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
table_path.write_text(json.dumps(table, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status':'PASS','summary':str(out_path),'table':str(table_path),'candidates':len(summary['candidates']),'held':len(summary['heldAnalysis'])}, ensure_ascii=False))
