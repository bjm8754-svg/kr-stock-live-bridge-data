"""Read-only audit of the supplied-quote report. Does not create trades or account paths."""
import csv,json,hashlib,math
from pathlib import Path
P=Path(__file__).resolve().parent
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((P/'MARKET_FINDINGS_FREEZE.json').read_text(encoding='utf-8'))
for n,h in receipt['files'].items():assert digest(P/n)==h,n
assert digest(P/'ORIGINAL_FIRST_ANSWER_UNCHANGED.md')==receipt['original_answer_sha256']
audit=json.loads((P/'PRESERVATION_AND_VALIDATION.json').read_text(encoding='utf-8'))
assert digest(P/'V84_ORIGINAL_SCORES_UNCHANGED.json')==audit['prior_scores_sha256']
scores=json.loads((P/'V84_ORIGINAL_SCORES_UNCHANGED.json').read_text(encoding='utf-8'))
assert scores['totals']=={'A':15,'T':16,'R':20}
data=json.loads((P/'CHRONOLOGICAL_EVIDENCE.json').read_text(encoding='utf-8'))
allrows=list(csv.DictReader((P/'PATHS_KRW.csv').open(encoding='utf-8')))
for c in data:
 rows=[dict(session=int(r['session']),date=r['date'],tradable=r['tradable']=='True',**{k:float(r[k]) if r[k] else None for k in ['Open','High','Low','Close']}) for r in allrows if r['case_id']==c['case_id']]
 assert len(rows)==120
 assert c['realized_return'] is None and c['actual_fill_authenticated'] is False
 assert not c['original_sell_rule_fixed'] and not c['new_trade_or_portfolio_created']
 for h in c['horizons']:
  window=[r for r in rows if r['session']<=h['horizon'] and r['tradable']]
  assert len(window)==h['tradable_sessions']
  # Different-day brute force, independently from the linear build check.
  upper=max(window[j]['High']/window[i]['Low']-1 for i in range(len(window)) for j in range(i+1,len(window)))
  assert math.isclose(upper*100,h['hindsight_ordered_envelope_pct'],abs_tol=1e-8)
  assert h['realized_B_return'] is None
 if 'bid' in c['levels']:
  bid=c['levels']['bid']['krw']
  first=next((r for r in rows if r['tradable'] and r['Low']<=bid+1e-7),None)
  assert (None if first is None else first['date'])==(None if c['first_bid_price_access'] is None else c['first_bid_price_access']['date'])
  for target in c['target_events_after_price_access']:
   hit=next((r for r in rows if r['tradable'] and first and r['session']>first['session'] and r['High']>=target['target']['krw']-1e-7),None)
   assert (None if hit is None else hit['date'])==(None if not target['first_separate_later_day_target'] else target['first_separate_later_day_target']['date'])
 assert c['partial_final_week_not_scored_as_completed']
 if c['first_completed_week_failure']:assert c['first_completed_week_failure']['date']<='2018-06-22'
idx={c['case_id']:c for c in data}
assert idx['E02']['first_bid_price_access'] is None
assert idx['E04']['target_events_after_price_access'][0]['same_day_order_ambiguous']
assert idx['E05']['bid_access_type']=='OPEN_GAP_BELOW_LIMIT'
assert idx['E06']['minimal_hold_occurs_only_after_first_reclaim_attempt_failed']
assert idx['E07']['minimal_hold_occurs_only_after_first_reclaim_attempt_failed']
assert all(t['first_separate_later_day_target']['session']<120 for t in idx['E09']['target_events_after_price_access'])
assert idx['E08']['horizons'][1]['endpoint_close'] is None and audit['E08_excluded_from_ordinary_skill_and_return_evaluation']
print('PASS: original and scores preserved; 30 fixed-window envelopes; quote chronology; no invented fills/returns; E08 separated.')
