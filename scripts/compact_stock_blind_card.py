#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

BASE = Path('research/stock_blind')
active = json.loads((BASE / 'ACTIVE_EPISODE.json').read_text(encoding='utf-8'))
root = BASE / 'episodes' / active['episodeId']
card_path = root / 'current_card.json'
out_path = root / 'current_card_summary.json'

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
    # Held analyses may carry a separate simple chartTrace rather than review.chartTrace.
    simple = x.get('chartTrace') or {}
    if simple:
        y['heldDailyTail'] = (simple.get('daily') or [])[-40:]
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

if summary['futureIncluded'] is not False:
    raise RuntimeError('summary source is not blind')

out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status':'PASS','output':str(out_path),'candidates':len(summary['candidates']),'held':len(summary['heldAnalysis'])}, ensure_ascii=False))
