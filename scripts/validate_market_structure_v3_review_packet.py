#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


DAILY_SCHEMA=["date","open","high","low","close","volumeRatio20","tradingValueRatio20","rsi"]
HIGHER_SCHEMA=["date","open","high","low","close","volumeRatio","tradingValueRatio"]


def main():
    p=argparse.ArgumentParser()
    p.add_argument("path")
    p.add_argument("--config", default="market-structure-v3-config.json")
    args=p.parse_args()

    data=json.loads(Path(args.path).read_text(encoding="utf-8"))
    cfg=json.loads(Path(args.config).read_text(encoding="utf-8"))
    errors=[]

    if data.get("schemaVersion")!="MARKET_STRUCTURE_V3_REVIEW_PACKET":
        errors.append("wrong review packet schemaVersion")
    if data.get("sourceSchemaVersion")!="MARKET_STRUCTURE_V3":
        errors.append("wrong sourceSchemaVersion")

    queue=data.get("deepReviewQueue")
    if not isinstance(queue,list):
        errors.append("deepReviewQueue is not array")
        queue=[]

    if int(data.get("count") or 0)!=len(queue):
        errors.append("review packet count mismatch")

    max_review=int(cfg.get("maxDeepReviewCandidates",36))
    if len(queue)>max_review:
        errors.append(f"review queue exceeds bound: {len(queue)}>{max_review}")

    seen=set()
    for row in queue:
        code=str(row.get("code") or "?")
        def err(msg): errors.append(f"{code}: {msg}")

        if code in seen:
            err("duplicate candidate")
        seen.add(code)

        review=row.get("review") or {}
        if review.get("assistantReviewRequired") is not True:
            err("assistantReviewRequired must be true")
        if review.get("machineScope")!="PREFILTER_AND_EVIDENCE_ONLY":
            err("machine scope must be prefilter/evidence only")

        trace=review.get("chartTrace")
        if not isinstance(trace,dict):
            err("missing multi-timeframe chartTrace")
            continue

        if trace.get("dailySchema")!=DAILY_SCHEMA:
            err("bad daily schema")
        if trace.get("weeklySchema")!=HIGHER_SCHEMA:
            err("bad weekly schema")
        if trace.get("monthlySchema")!=HIGHER_SCHEMA:
            err("bad monthly schema")

        daily=trace.get("daily")
        weekly=trace.get("weekly")
        monthly=trace.get("monthly")
        if not isinstance(daily,list) or not daily:
            err("daily trace missing")
        elif len(daily)>int(cfg.get("reviewDailyTraceSessions",120)):
            err("daily trace exceeds configured bound")
        if not isinstance(weekly,list) or not weekly:
            err("weekly trace missing")
        elif len(weekly)>int(cfg.get("reviewWeeklyTracePeriods",156)):
            err("weekly trace exceeds configured bound")
        if not isinstance(monthly,list) or not monthly:
            err("monthly trace missing")
        elif len(monthly)>int(cfg.get("reviewMonthlyTracePeriods",72)):
            err("monthly trace exceeds configured bound")

        if (row.get("setups") or {}).get("primary") is None:
            err("review candidate missing machine hypothesis")

    out={"status":"PASS" if not errors else "FAIL","count":len(queue),"errorCount":len(errors),"errors":errors[:100]}
    print(json.dumps(out,ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__=="__main__":
    main()
