#!/usr/bin/env python3
from __future__ import annotations
import argparse, io, json, re, urllib.request
from datetime import datetime
from pathlib import Path


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/154 Safari/537.36',
        'Referer': 'https://finance.naver.com/',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode('euc-kr', errors='replace')


def clean_num(s):
    s = re.sub(r'<[^>]+>', '', s).replace(',', '').replace('&nbsp;', '').strip()
    if not s or s in {'-', 'N/A'}:
        return None
    try:
        return float(s)
    except Exception:
        return s


def parse_rows(html: str):
    rows=[]
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', html, flags=re.I|re.S):
        tds=re.findall(r'<td[^>]*>(.*?)</td>', tr, flags=re.I|re.S)
        if len(tds) < 6:
            continue
        txt=[re.sub(r'<[^>]+>', '', x).replace('&nbsp;', ' ').strip() for x in tds]
        tm=txt[0]
        if not re.fullmatch(r'\d{2}:\d{2}', tm):
            continue
        vals=[clean_num(x) for x in tds[1:]]
        # Naver columns: 체결시각, 체결가, 전일비, 매도, 매수, 거래량, 변동량
        rows.append({
            'time': tm,
            'price': vals[0] if len(vals)>0 else None,
            'change': vals[1] if len(vals)>1 else None,
            'ask': vals[2] if len(vals)>2 else None,
            'bid': vals[3] if len(vals)>3 else None,
            'volume': vals[4] if len(vals)>4 else None,
            'volumeDelta': vals[5] if len(vals)>5 else None,
        })
    return rows


def recover(code: str, trade_date: str, end_hhmm='0940'):
    target=f'{trade_date}{end_hhmm}00'
    by_time={}
    raw_counts=[]
    for page in range(1, 8):
        url=f'https://finance.naver.com/item/sise_time.naver?code={code}&thistime={target}&page={page}'
        html=fetch_html(url)
        parsed=parse_rows(html)
        raw_counts.append(len(parsed))
        for r in parsed:
            if '09:00' <= r['time'] <= '09:40':
                by_time.setdefault(r['time'], r)
        if '09:00' in by_time and len(by_time)>=41:
            break
    expected=[f'09:{m:02d}' for m in range(41)]
    rows=[]
    for t in expected:
        if t in by_time:
            rr=dict(by_time[t]); rr['atKst']=f'{trade_date} {t.replace(":", "")}'
            rows.append(rr)
    missing=[t for t in expected if t not in by_time]
    return {
        'code':code,
        'status':'PASS' if not missing else 'FAIL',
        'source':'NAVER_SISE_TIME_HISTORICAL',
        'cutoffKst':f'{trade_date} {end_hhmm}',
        'history':{'count':len(rows),'from':rows[0]['atKst'] if rows else None,'to':rows[-1]['atKst'] if rows else None,'rows':rows},
        'missingMinutes':missing,
        'pageRowCounts':raw_counts,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--trade-date',required=True)
    ap.add_argument('--codes',required=True)
    ap.add_argument('--output',required=True)
    a=ap.parse_args()
    codes=[]
    for x in a.codes.split(','):
        x=x.strip()
        if re.fullmatch(r'\d{6}',x) and x not in codes: codes.append(x)
    results=[recover(c,a.trade_date) for c in codes]
    out={
      'schemaVersion':'V3_SHADOW_CATCHUP_INTRADAY_V1',
      'mode':'SHADOW_ONLY','replayMode':'CATCHUP_REPLAY','realTimeE2E':False,'productionWriteAllowed':False,
      'tradeDate':a.trade_date,'cutoffKst':f'{a.trade_date} 0940','codes':codes,
      'status':'PASS' if results and all(x['status']=='PASS' for x in results) else 'FAIL',
      'results':results,
    }
    Path(a.output).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in out.items() if k!='results'},ensure_ascii=False))
    for x in results:
        print(json.dumps({'code':x['code'],'status':x['status'],'count':x['history']['count'],'missing':x['missingMinutes']},ensure_ascii=False))
    if out['status']!='PASS': raise SystemExit(1)

if __name__=='__main__': main()
