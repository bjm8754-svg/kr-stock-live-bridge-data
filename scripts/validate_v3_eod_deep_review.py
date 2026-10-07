#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

SCHEMA="V3_EOD_DEEP_REVIEW_V1"
ALLOWED={"ATTACK_CANDIDATE","PROBE_CANDIDATE","WATCH","REJECT"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--source-trade-date", default=None)
    a=ap.parse_args()
    d=json.loads(Path(a.path).read_text(encoding="utf-8"))
    e=[]
    if d.get("schemaVersion")!=SCHEMA: e.append("schema")
    if d.get("mode")!="SHADOW_ONLY": e.append("mode")
    if d.get("productionWriteAllowed") is not False: e.append("productionWriteAllowed")
    if d.get("status")!="PASS": e.append("status")
    if d.get("assistantDeepReviewCompleted") is not True: e.append("assistantDeepReviewCompleted")
    if a.source_trade_date and d.get("sourceTradeDate")!=a.source_trade_date: e.append("sourceTradeDate")
    codes=[str(x) for x in (d.get("codes") or [])]
    reviews=d.get("reviews") or []
    if len(codes)!=int(d.get("reviewCount") or -1) or len(reviews)!=len(codes): e.append("counts")
    if len(codes)>36 or len(codes)!=len(set(codes)): e.append("codes")
    for i,(code,r) in enumerate(zip(codes,reviews)):
        if str(r.get("code") or "")!=code: e.append(f"{i}:code")
        st=r.get("chartState")
        if st not in ALLOWED: e.append(f"{i}:state")
        if not r.get("thesis"): e.append(f"{i}:thesis")
        if st!="REJECT":
            for k in ("importantZone","confirmation","invalidation","chaseJudgement","counterargument"):
                if r.get(k) in (None,""): e.append(f"{i}:{k}")
    print(json.dumps({"status":"PASS" if not e else "FAIL","errors":e[:100]},ensure_ascii=False))
    if e: raise SystemExit(1)

if __name__=="__main__":
    main()
