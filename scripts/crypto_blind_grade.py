#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt, json, math, time, subprocess
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen

BASE='https://data-api.binance.vision/api/v3/klines'
DEC=Path('research/crypto_blind/decisions.json')
OUT=Path('research/crypto_blind/results.json')
SUMMARY=Path('research/crypto_blind/RESULTS.md')
SYMS=('BTCUSDT','ETHUSDT')

def ms(d): return int(dt.datetime(d.year,d.month,d.day,tzinfo=dt.timezone.utc).timestamp()*1000)
def fetch_all(symbol,start,end):
    rows=[]; cursor=ms(start); end_ms=ms(end+dt.timedelta(days=1))-1
    while cursor<=end_ms:
        q=urlencode({'symbol':symbol,'interval':'1d','startTime':cursor,'endTime':end_ms,'limit':1000})
        req=Request(f'{BASE}?{q}',headers={'User-Agent':'crypto-blind-grade/1.0'})
        with urlopen(req,timeout=30) as r: batch=json.loads(r.read().decode())
        if not batch: break
        for x in batch:
            d=dt.datetime.fromtimestamp(x[0]/1000,tz=dt.timezone.utc).date()
            rows.append({'date':d.isoformat(),'open':float(x[1]),'high':float(x[2]),'low':float(x[3]),'close':float(x[4])})
        nxt=int(batch[-1][0])+86400000
        if nxt<=cursor: break
        cursor=nxt; time.sleep(.03)
    return rows

def date_range(a,b):
    d=a
    while d<=b:
        yield d; d+=dt.timedelta(days=1)

def round2(x): return round(float(x),2)

def decision_sha():
    try:return subprocess.check_output(['git','log','-1','--format=%H','--',str(DEC)],text=True).strip()
    except:return None

def main():
    dec=json.load(open(DEC,encoding='utf-8'))
    ds=dec['decisions']; first=dt.date.fromisoformat(ds[0]['cutoff'])+dt.timedelta(days=1); last=dt.date.fromisoformat(ds[-1]['cutoff'])+dt.timedelta(days=35)
    raw={s:fetch_all(s,first-dt.timedelta(days=2),last) for s in SYMS}
    maps={s:{dt.date.fromisoformat(r['date']):r for r in rows} for s,rows in raw.items()}
    capital=float(dec['initialCapitalKrw']); initial=capital
    equity=[]; cases=[]; trades=[]
    for i,d in enumerate(ds):
        cutoff=dt.date.fromisoformat(d['cutoff']); entry_date=cutoff+dt.timedelta(days=1)
        natural_end=cutoff+dt.timedelta(days=int(dec['rules']['maxHoldDays']))
        next_cut=dt.date.fromisoformat(ds[i+1]['cutoff']) if i+1<len(ds) else None
        end_date=min(natural_end,next_cut) if next_cut else natural_end
        start_cap=capital
        allocations=[]
        for p in d['portfolio']:
            alloc=start_cap*float(p['capitalPct'])/100
            allocations.append({**p,'initialKrw':alloc,'value':alloc,'stopped':False,'exitDate':None,'entryPrice':None,'exitPrice':None,'prevClose':None,'mfePct':0.0,'maePct':0.0})
        cash=start_cap*float(d['cashPct'])/100
        # Entry occurs at next UTC daily open. If the market gaps through the precommitted stop, skip that sleeve instead of entering an already-invalid trade.
        for a in allocations:
            bar=maps[a['symbol']].get(entry_date)
            if not bar: raise RuntimeError(f'missing entry bar {a["symbol"]} {entry_date}')
            a['entryPrice']=bar['open']
            a['prevClose']=bar['open']
            if bar['open']<=float(a['stop']):
                a['stopped']=True; a['exitDate']=entry_date.isoformat(); a['exitPrice']=bar['open']; cash+=a['value']; a['value']=0.0; a['skipInvalidAtOpen']=True
        for day in date_range(entry_date,end_date):
            nav=cash
            for a in allocations:
                if a['value']<=0: continue
                if a['stopped']:
                    nav+=a['value']; continue
                bar=maps[a['symbol']].get(day)
                if not bar: raise RuntimeError(f'missing bar {a["symbol"]} {day}')
                stop=float(a['stop']); veh=a['vehicle']; entry=float(a['entryPrice'])
                if veh=='SPOT':
                    a['mfePct']=max(a['mfePct'],(bar['high']/entry-1)*100)
                    a['maePct']=min(a['maePct'],(bar['low']/entry-1)*100)
                    if bar['open']<=stop:
                        exitp=bar['open']; a['value']=a['initialKrw']*(exitp/entry); a['stopped']=True; a['exitDate']=day.isoformat(); a['exitPrice']=exitp
                    elif bar['low']<=stop:
                        exitp=stop; a['value']=a['initialKrw']*(exitp/entry); a['stopped']=True; a['exitDate']=day.isoformat(); a['exitPrice']=exitp
                    else:
                        a['value']=a['initialKrw']*(bar['close']/entry)
                        if day==end_date: a['exitDate']=day.isoformat(); a['exitPrice']=bar['close']
                elif veh=='DAILY_2X':
                    ref=float(a['prevClose'])
                    if bar['open']<=stop:
                        px=bar['open']; r=px/ref-1; a['value']*=max(0.0,1+2*r); a['stopped']=True; a['exitDate']=day.isoformat(); a['exitPrice']=px
                    elif bar['low']<=stop:
                        px=stop; r=px/ref-1; a['value']*=max(0.0,1+2*r); a['stopped']=True; a['exitDate']=day.isoformat(); a['exitPrice']=px
                    else:
                        r=bar['close']/ref-1; a['value']*=max(0.0,1+2*r); a['prevClose']=bar['close']
                        if day==end_date: a['exitDate']=day.isoformat(); a['exitPrice']=bar['close']
                    ret=(a['value']/a['initialKrw']-1)*100
                    a['mfePct']=max(a['mfePct'],ret); a['maePct']=min(a['maePct'],ret)
                else: raise RuntimeError('bad vehicle')
                nav+=a['value']
            equity.append({'date':day.isoformat(),'navKrw':round2(nav),'caseId':d['caseId']})
        capital=cash+sum(a['value'] for a in allocations)
        cr=(capital/start_cap-1)*100
        cases.append({'caseId':d['caseId'],'cutoff':d['cutoff'],'entryDate':entry_date.isoformat(),'endDate':end_date.isoformat(),'verdict':d['verdict'],'startCapitalKrw':round2(start_cap),'endCapitalKrw':round2(capital),'returnPct':round(cr,3),'cashPct':d['cashPct']})
        for a in allocations:
            pnl=a['value']-a['initialKrw'] if not a.get('skipInvalidAtOpen') else 0.0
            tr={'caseId':d['caseId'],'symbol':a['symbol'],'vehicle':a['vehicle'],'capitalPct':a['capitalPct'],'entryDate':entry_date.isoformat(),'entryPrice':a['entryPrice'],'exitDate':a['exitDate'],'exitPrice':a['exitPrice'],'stop':a['stop'],'stopped':a['stopped'],'pnlKrw':round2(pnl),'returnPct':round((a['value']/a['initialKrw']-1)*100,3) if a['initialKrw'] else 0,'mfePct':round(a['mfePct'],3),'maePct':round(a['maePct'],3)}
            trades.append(tr)
    # metrics
    trade_pnls=[t['pnlKrw'] for t in trades if abs(t['pnlKrw'])>1e-9]
    wins=[x for x in trade_pnls if x>0]; losses=[x for x in trade_pnls if x<0]
    pf=(sum(wins)/abs(sum(losses))) if losses else None
    case_active=[c for c in cases if any(t['caseId']==c['caseId'] for t in trades)]
    case_wins=[c for c in case_active if c['returnPct']>0]
    peak=initial; mdd=0.0
    for e in equity:
        v=e['navKrw']; peak=max(peak,v); mdd=min(mdd,(v/peak-1)*100)
    # continuous buy/hold BTC benchmark from first entry open to last end close
    b0=maps['BTCUSDT'][first]['open']; bend=maps['BTCUSDT'][dt.date.fromisoformat(cases[-1]['endDate'])]['close']; btc_bh=(bend/b0-1)*100
    out={
      'schema':'CRYPTO_BLIND_REPLAY_RESULT_V1','decisionCommit':decision_sha(),'initialCapitalKrw':initial,'finalCapitalKrw':round2(capital),'totalReturnPct':round((capital/initial-1)*100,3),'maxDrawdownPct':round(mdd,3),
      'tradeCount':len(trades),'tradeWinRatePct':round(len(wins)/len(trade_pnls)*100,2) if trade_pnls else None,'caseActiveCount':len(case_active),'caseWinRatePct':round(len(case_wins)/len(case_active)*100,2) if case_active else None,'profitFactor':None if pf is None else round(pf,3),'btcBuyHoldPctSameCalendarSpan':round(btc_bh,3),
      'assumptions':['No fees/slippage/taxes.','DAILY_2X is a generic daily-reset 2x underlying proxy, not literal BITU/ETHU historical prices.','Stops execute at stop unless the daily open gaps through the stop, in which case exit is at the open.','Positions are held up to 30 calendar days or until the next blind decision cutoff, whichever comes first.'],
      'cases':cases,'trades':trades,'equity':equity
    }
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Crypto Blind Replay Results','',f"- Decision commit: `{out['decisionCommit']}`",f"- Initial: {initial:,.0f} KRW",f"- Final: {capital:,.0f} KRW",f"- Total return: {out['totalReturnPct']:.2f}%",f"- Max drawdown: {out['maxDrawdownPct']:.2f}%",f"- Trade win rate: {out['tradeWinRatePct']}% ({len(wins)}/{len(trade_pnls)})",f"- Active-case win rate: {out['caseWinRatePct']}% ({len(case_wins)}/{len(case_active)})",f"- Profit factor: {out['profitFactor']}",f"- BTC buy/hold over same calendar span: {out['btcBuyHoldPctSameCalendarSpan']:.2f}%",'', '## Cases','', '|Case|Verdict|Return|Start KRW|End KRW|','|---|---|---:|---:|---:|']
    for c in cases: lines.append(f"|{c['caseId']}|{c['verdict']}|{c['returnPct']:.2f}%|{c['startCapitalKrw']:,.0f}|{c['endCapitalKrw']:,.0f}|")
    lines+=['','## Trades','', '|Case|Asset|Vehicle|Return|MFE|MAE|Stopped|','|---|---|---|---:|---:|---:|---|']
    for t in trades: lines.append(f"|{t['caseId']}|{t['symbol']}|{t['vehicle']}|{t['returnPct']:.2f}%|{t['mfePct']:.2f}%|{t['maePct']:.2f}%|{t['stopped']}|")
    SUMMARY.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:out[k] for k in ('finalCapitalKrw','totalReturnPct','maxDrawdownPct','tradeWinRatePct','caseWinRatePct','profitFactor','btcBuyHoldPctSameCalendarSpan')},ensure_ascii=False))
if __name__=='__main__': main()
