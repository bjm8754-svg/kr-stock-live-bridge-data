#!/usr/bin/env python3
from __future__ import annotations

import concurrent.futures as cf
import copy
import datetime as dt
import hashlib
import json
import math
import random
import re
from pathlib import Path

import FinanceDataReader as fdr
import pandas as pd

from msv3.engine import analyze_frame, build_output

REPO = Path('.')
BASE = REPO / 'research/stock_blind'
ACTIVE = BASE / 'ACTIVE_EPISODE_V2.json'

# Isolated S02+ research engine; never imported by the original S01 runner.
import sys
sys.path.insert(0, str(BASE))
from reservation_engine import simulate as simulate_reservations
V3CFG = REPO / 'market-structure-v3-config.json'
DATE8 = re.compile(r'^20\d{6}$')
DATE10 = re.compile(r'^20\d{2}-\d{2}-\d{2}$')


def load_cfg():
    cfg = json.loads(ACTIVE.read_text(encoding='utf-8'))
    cfg['episodeId'] = str(cfg['episodeId']).strip()
    if not cfg['episodeId'] or '/' in cfg['episodeId'] or '..' in cfg['episodeId']:
        raise RuntimeError('invalid episodeId')
    cfg['seed'] = int(cfg['seed'])
    cfg['episodeSessions'] = int(cfg.get('episodeSessions', 30))
    cfg['stepSessions'] = int(cfg.get('stepSessions', 3))
    if cfg['episodeSessions'] % cfg['stepSessions']:
        raise RuntimeError('episodeSessions must be divisible by stepSessions')
    return cfg


CFG = load_cfg()
ROOT = BASE / 'episodes' / CFG['episodeId']
DEC = ROOT / 'decisions'
CARD = ROOT / 'current_card.json'
STATE = ROOT / 'state.json'
FINAL = ROOT / 'FINAL_RESULT.json'


def pdate(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    try:
        return pd.to_datetime(x).date()
    except Exception:
        return None


def normalize_listing(df, source):
    if df is None or df.empty:
        return []
    code_col = 'Code' if 'Code' in df.columns else ('Symbol' if 'Symbol' in df.columns else None)
    if not code_col:
        return []
    out = []
    for _, x in df.iterrows():
        code = str(x.get(code_col, '')).zfill(6)
        if not re.fullmatch(r'\d{6}', code):
            continue
        name = str(x.get('Name', code))
        market = str(x.get('Market', ''))
        if market not in ('KOSPI', 'KOSDAQ'):
            continue
        if re.search(r'스팩|SPAC', name, re.I):
            continue
        out.append({
            'code': code,
            'name': name,
            'market': market,
            'listingDate': pdate(x.get('ListingDate')),
            'delistingDate': pdate(x.get('DelistingDate')),
            'source': source,
            'amount': None,
            'marcap': None,
        })
    return out


def listing_sources(delist_start=None):
    current = fdr.StockListing('KRX')
    if delist_start:
        try:
            dl = fdr.StockListing('KRX-DELISTING', delist_start.isoformat(), dt.date.today().isoformat())
        except Exception:
            dl = fdr.StockListing('KRX-DELISTING')
    else:
        dl = fdr.StockListing('KRX-DELISTING')
    return normalize_listing(current, 'CURRENT'), normalize_listing(dl, 'DELISTING')


def active_universe(cutoff):
    current, delisted = listing_sources(cutoff)
    rows = []
    for m in current:
        if m['listingDate'] is None or m['listingDate'] <= cutoff:
            rows.append(m)
    for m in delisted:
        ld, dd = m['listingDate'], m['delistingDate']
        if (ld is None or ld <= cutoff) and (dd is None or cutoff <= dd):
            rows.append(m)
    # Prefer the historically delisted record if the same code appears in both sources
    # at the cutoff; listing date disambiguates most code re-use cases.
    dedup = {}
    for m in rows:
        key = (m['code'], m['listingDate'])
        if key not in dedup or m['source'] == 'DELISTING':
            dedup[key] = m
    return list(dedup.values())


def global_catalog():
    start = dt.date.fromisoformat(CFG['historyStart'])
    current, delisted = listing_sources(start)
    out = current + delisted
    return {asset_id(x): x for x in out}


def asset_id(meta):
    ld = meta['listingDate'].isoformat() if meta.get('listingDate') else 'NA'
    raw = f"{CFG['seed']}|{meta['code']}|{ld}|{meta['source']}"
    return 'A' + hashlib.sha256(raw.encode()).hexdigest()[:9].upper()


def enforce_asof(df, end):
    """Hard-filter source bars before *any* technical indicator sees them."""
    if df is None or df.empty:
        return df
    out = df.copy()
    out.index = pd.to_datetime(out.index)
    out = out.loc[out.index.date <= end].sort_index()
    if not out.empty and any(out.index.date > end):
        raise RuntimeError("PIT_FUTURE_BAR: cutoff filter failed")
    return out


def fetch_price(meta, start, end):
    s = start.isoformat()
    e = (end + dt.timedelta(days=1)).isoformat()
    try:
        if meta['source'] == 'DELISTING':
            try:
                df = fdr.DataReader(meta['code'], s, e, exchange='KRX-DELISTING')
            except Exception:
                df = fdr.DataReader(f"KRX-DELISTING:{meta['code']}", s, e)
        else:
            df = fdr.DataReader(meta['code'], s, e)
    except Exception:
        return pd.DataFrame()
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    keep = [c for c in ['Open','High','Low','Close','Volume'] if c in df.columns]
    if len(keep) < 5:
        return pd.DataFrame()
    return enforce_asof(df[keep].dropna(), end)


def index_frame(symbol, start, end):
    df = fdr.DataReader(symbol, start.isoformat(), (end + dt.timedelta(days=1)).isoformat())
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    return enforce_asof(df, end)


def episode_calendar():
    h0 = dt.date.fromisoformat(CFG['historyStart'])
    h1 = dt.date.fromisoformat(CFG['historyEnd'])
    ks = index_frame('KS11', h0 - dt.timedelta(days=10), h1 + dt.timedelta(days=120))
    dates = [x.date() for x in ks.index if h0 <= x.date() <= h1 + dt.timedelta(days=120)]
    need = CFG['episodeSessions']
    cands = []
    for i, d in enumerate(dates):
        if d < h0 or d > h1:
            continue
        if i + need >= len(dates):
            continue
        cands.append(i)
    blocked = []
    epdir = BASE / 'episodes'
    if epdir.exists():
        for p in epdir.glob('*/FINAL_RESULT.json'):
            try:
                z = json.loads(p.read_text(encoding='utf-8'))
                a = dt.date.fromisoformat(z['revealedStartDate'])
                b = dt.date.fromisoformat(z['revealedEndDate'])
                blocked.append((a,b))
            except Exception:
                pass
    cands = [i for i in cands if not any(not (dates[i+need] < a or dates[i] > b) for a,b in blocked)]
    if not cands:
        raise RuntimeError('no unseen stock replay episode available')
    idx = random.Random(CFG['seed']).choice(cands)
    return dates[idx:idx+need+1]


def commitment(dates):
    raw = f"{CFG['episodeId']}|{dates[0].isoformat()}|{CFG['seed']}|{CFG['episodeSessions']}|{CFG['stepSessions']}"
    return hashlib.sha256(raw.encode()).hexdigest()


def decisions():
    DEC.mkdir(parents=True, exist_ok=True)
    out = []
    for p in sorted(DEC.glob('D*.json')):
        out.append(json.loads(p.read_text(encoding='utf-8')))
    return out


def close_on_or_before(df, d):
    if df.empty:
        return None
    s = df.loc[df.index.date <= d]
    if s.empty:
        return None
    return float(s.iloc[-1]['Close'])


def row_on(df, d):
    if df.empty:
        return None
    s = df.loc[df.index.date == d]
    return None if s.empty else s.iloc[-1]


def replay(decs, review_dates, catalog):
    return simulate_reservations(decs, review_dates, catalog, fetch_price, CFG)


def relative_date_string(s, cutoff):
    try:
        if DATE8.match(s):
            d = dt.datetime.strptime(s, '%Y%m%d').date()
        elif DATE10.match(s):
            d = dt.date.fromisoformat(s)
        else:
            return s
        delta = (d - cutoff).days
        return f"T{delta:+d}D"
    except Exception:
        return 'HIDDEN'


def scrub(obj, cutoff, replacements=None):
    replacements = replacements or {}
    if isinstance(obj, dict):
        out = {}
        for k,v in obj.items():
            if k in ('code','name','tradeDate','generatedAtKst'):
                continue
            out[k] = scrub(v, cutoff, replacements)
        return out
    if isinstance(obj, list):
        return [scrub(x, cutoff, replacements) for x in obj]
    if isinstance(obj, str):
        if obj in replacements:
            return replacements[obj]
        if DATE8.match(obj) or DATE10.match(obj):
            return relative_date_string(obj, cutoff)
        z = obj
        for a,b in replacements.items():
            z = z.replace(a,b)
        return z
    return obj


def simple_trace(df, n=100):
    if df is None or df.empty:
        return []
    z = df.iloc[-n:].copy()
    vr = z['Volume'] / z['Volume'].shift(1).rolling(20, min_periods=5).mean()
    out=[]
    total=len(z)
    for i,(_,r) in enumerate(z.iterrows()):
        v = vr.iloc[i]
        out.append([
            i-total+1,
            round(float(r['Open']),2), round(float(r['High']),2),
            round(float(r['Low']),2), round(float(r['Close']),2),
            None if pd.isna(v) else round(float(v),2),
        ])
    return out


def scan_market(cutoff, held_ids, catalog):
    v3 = json.loads(V3CFG.read_text(encoding='utf-8'))
    v3['maxDeepReviewCandidates'] = int(CFG.get('maxDeepReviewCandidates', 18))
    hist_start = cutoff - dt.timedelta(days=int(v3.get('historyCalendarDays',3300)))
    universe = active_universe(cutoff)
    rows=[]; errors=[]; raw_by_aid={}; meta_by_code={}

    def worker(meta):
        df = fetch_price(meta, hist_start, cutoff)
        row = analyze_frame(meta, df, v3)
        return meta,df,row

    with cf.ThreadPoolExecutor(max_workers=int(v3.get('maxWorkers',8))) as ex:
        futs={ex.submit(worker,m):m for m in universe}
        for fut in cf.as_completed(futs):
            m=futs[fut]
            try:
                meta,df,row=fut.result()
                rows.append(row)
                aid=asset_id(meta)
                raw_by_aid[aid]=df
                meta_by_code[(meta['code'],meta.get('listingDate'))]=meta
            except Exception as e:
                errors.append({'error':type(e).__name__})

    output=build_output(rows, errors, v3, 'HIDDEN')
    # map active code to asset id. Prefer exact listing-date match if present.
    aid_by_code={}
    for m in universe:
        aid_by_code[m['code']]=asset_id(m)

    candidates=[]
    for x in output.get('deepReviewQueue') or []:
        code=x.get('code')
        aid=aid_by_code.get(code)
        if not aid:
            continue
        repl={code:aid, str(x.get('name','')):aid}
        y=scrub(copy.deepcopy(x), cutoff, repl)
        y['assetId']=aid
        candidates.append(y)

    held=[]
    row_by_code={r.get('code'):r for r in rows if r.get('status')=='OK'}
    for aid in held_ids:
        meta=catalog.get(aid)
        if not meta:
            continue
        row=row_by_code.get(meta['code'])
        if row:
            repl={meta['code']:aid,meta['name']:aid}
            y=scrub(copy.deepcopy(row),cutoff,repl)
        else:
            y={'status':'NO_CURRENT_ANALYSIS'}
        df=raw_by_aid.get(aid)
        if df is None or df.empty:
            df=fetch_price(meta,hist_start,cutoff)
        y['assetId']=aid
        y['chartTrace']={
            'schema':['t','open','high','low','close','volumeRatio20'],
            'daily':simple_trace(df,100),
        }
        held.append(y)

    return {
        'coverage': {
            'universeReconstructed': len(universe),
            'analyzed': len(rows),
            'errors': len(errors),
            'machineCandidates': int((output.get('counts') or {}).get('candidates') or 0),
            'deepReviewCount': len(candidates),
        },
        'candidates': candidates,
        'heldAnalysis': held,
    }


def verify_pit_card(card, cutoff):
    """Independent post-scanner fail-closed guard against look-ahead."""
    if card.get("futureIncluded") is not False:
        raise RuntimeError("PIT_FLAG_BAD")
    if card.get("step") is None:
        raise RuntimeError("PIT_STEP_MISSING")
    for candidate in card.get("deepReviewCandidates", []):
        daily = (((candidate.get("review") or {}).get("chartTrace") or {}).get("daily") or [])
        for bar in daily:
            label = str(bar[0]) if bar else ""
            if re.fullmatch(r"T\+[1-9]\d*D", label):
                raise RuntimeError("PIT_FUTURE_TRACE_LABEL " + str(candidate.get("assetId")))
        if daily and abs(float(daily[-1][4]) - float(candidate["price"]["close"])) > 0.011:
            raise RuntimeError("PIT_CANDIDATE_LAST_PRICE_MISMATCH " + str(candidate.get("assetId")))
    held_now = {p["assetId"]: p for p in (card.get("portfolioState") or {}).get("positions", [])}
    for held in card.get("heldPositionAnalysis", []):
        aid = held.get("assetId")
        if aid not in held_now:
            raise RuntimeError("PIT_HELD_ASSET_NOT_IN_PORTFOLIO " + str(aid))
        px = (held.get("price") or {}).get("close")
        if px is not None and abs(float(px) - float(held_now[aid]["currentPrice"])) > 0.011:
            raise RuntimeError("PIT_HELD_PRICE_MISMATCH " + str(aid))
    return True


def market_context(cutoff):
    start=cutoff-dt.timedelta(days=140)
    out={}
    for symbol,label in [('KS11','KOSPI'),('KQ11','KOSDAQ')]:
        try:
            df=index_frame(symbol,start,cutoff)
            out[label]={'daily':simple_trace(df,60)}
        except Exception:
            out[label]={'daily':[]}
    return out


def benchmark_return(symbol, start, end):
    try:
        df=index_frame(symbol,start,end)
        if df.empty:return None
        return round((float(df.iloc[-1]['Close'])/float(df.iloc[0]['Close'])-1)*100,3)
    except Exception:
        return None


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    review_dates=episode_calendar()
    decs=decisions()
    max_decisions=CFG['episodeSessions']//CFG['stepSessions']
    if len(decs)>max_decisions:
        raise RuntimeError('too many decisions')
    cat=global_catalog()
    rep=replay(decs,review_dates,cat)
    step=len(decs)
    state={
        'schema':'KOREA_STOCK_BLIND_STATE',
        'episodeId':CFG['episodeId'],
        'step':step,
        'relativeSession':step*CFG['stepSessions'],
        'episodeCommitment':commitment(review_dates),
        'equityKrw':round(rep['equity'],2),
        'returnPct':round((rep['equity']/float(CFG['initialCapitalKrw'])-1)*100,3),
        'maxDrawdownPct':round(rep['mddPct'],3),
        'cashKrw':round(rep['cash'],2),
        'cashPct':round(rep['cash']/rep['equity']*100,2) if rep['equity'] else 0,
        'turnoverKrw':round(rep['turnoverKrw'],2),
        'transactionCostKrw':round(rep['costKrw'],2),
        'positions':rep['positions'],
        'pendingOrders':rep['pendingOrders'],
        'orderEvents':rep['orderEvents'],
        'previousInterval':rep['intervals'][-1] if rep['intervals'] else None,
        'decisionsLocked':step,
        'futureIncluded':False,
    }
    STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    if step<max_decisions:
        cutoff=review_dates[step*CFG['stepSessions']]
        held_ids=[x['assetId'] for x in rep['positions']]
        scan=scan_market(cutoff,held_ids,cat)
        card={
            'schema':'KOREA_STOCK_BLIND_CARD',
            'episodeId':CFG['episodeId'],
            'step':step,
            'relativeSession':step*CFG['stepSessions'],
            'futureIncluded':False,
            'mode':'FULL_MARKET_DISCOVERY_PLUS_POSITION_MANAGEMENT',
            'portfolioState':{
                'equityKrw':state['equityKrw'],
                'returnPct':state['returnPct'],
                'cashPct':state['cashPct'],
                'positions':state['positions'],
                'pendingOrders':state['pendingOrders'],
                'previousInterval':state['previousInterval'],
            },
            'marketContext':market_context(cutoff),
            'coverage':scan['coverage'],
            'deepReviewCandidates':scan['candidates'],
            'heldPositionAnalysis':scan['heldAnalysis'],
            'decisionContract':{
                'portfolioActions':['ENTER','HOLD','ADD','REDUCE','ROTATE_IN'],
                'exitActions':['EXIT','ROTATE_OUT'],
                'maxCapitalPct':100,
                'requireStructuralStopOrExplicitNull':True,
                'freshDiscoveryContinuesWhileHolding':True,
                'entryOrderType':'BUY_LIMIT_RESERVATION',
                'noDefaultNextOpenPurchase':True,
                'pendingOrdersSurviveReview':True,
            },
        }
        verify_pit_card(card, cutoff)
        text=json.dumps(card,ensure_ascii=False,separators=(',',':'))+'\n'
        if re.search(r'20\d{2}-\d{2}-\d{2}|20\d{6}',text):
            raise RuntimeError('blind guard failed: calendar date leaked into current card')
        CARD.write_text(text,encoding='utf-8')
        if FINAL.exists():FINAL.unlink()
        print(json.dumps({'status':'READY','episodeId':CFG['episodeId'],'step':step,'relativeSession':card['relativeSession'],'equityKrw':state['equityKrw'],'deepReviewCount':len(scan['candidates'])},ensure_ascii=False))
        return

    if CARD.exists():CARD.unlink()
    held_ids=sorted({x['assetId'] for d in decs for x in (d.get('portfolio') or [])})
    mapping=[]
    for aid in held_ids:
        m=cat.get(aid)
        if m:
            mapping.append({'assetId':aid,'code':m['code'],'name':m['name'],'market':m['market']})
    start,end=review_dates[0],review_dates[-1]
    result={
        'schema':'KOREA_STOCK_BLIND_FINAL',
        'episodeId':CFG['episodeId'],
        'episodeCommitment':commitment(review_dates),
        'revealedStartDate':start.isoformat(),
        'revealedEndDate':end.isoformat(),
        'initialCapitalKrw':CFG['initialCapitalKrw'],
        'finalCapitalKrw':round(rep['equity'],2),
        'totalReturnPct':round((rep['equity']/float(CFG['initialCapitalKrw'])-1)*100,3),
        'maxDrawdownPct':round(rep['mddPct'],3),
        'turnoverKrw':round(rep['turnoverKrw'],2),
        'transactionCostKrw':round(rep['costKrw'],2),
        'compositionChanges':rep['compositionChanges'],
        'benchmarks':{
            'KOSPI_returnPct':benchmark_return('KS11',start,end),
            'KOSDAQ_returnPct':benchmark_return('KQ11',start,end),
        },
        'heldAssetReveal':mapping,
        'intervals':rep['intervals'],
        'decisionCount':len(decs),
        'limitations':['historical fundamentals/revisions/news not point-in-time integrated','transaction costs are a simplified proxy','universe is reconstructed from current plus delisted KRX listings'],
    }
    FINAL.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'FINAL','episodeId':CFG['episodeId'],'finalCapitalKrw':result['finalCapitalKrw'],'returnPct':result['totalReturnPct'],'mddPct':result['maxDrawdownPct']},ensure_ascii=False))


if __name__=='__main__':
    main()
