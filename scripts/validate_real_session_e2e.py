#!/usr/bin/env python3
import argparse, json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

KST=ZoneInfo("Asia/Seoul")
BUILD="worker_v3_hardened_money_scan_v1"

def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--cutoff", choices=["0935","0940"], required=True)
    ap.add_argument("--asof-date", default=None)
    ap.add_argument("--live", default="live.json")
    ap.add_argument("--watchlist", default="watchlist.json")
    ap.add_argument("--health", default="live-health.json")
    a=ap.parse_args()
    date=a.asof_date or datetime.now(KST).strftime("%Y%m%d")
    live, watch, health = load(a.live), load(a.watchlist), load(a.health)
    critical=[]; operational=[]
    expected_count=36 if a.cutoff=="0935" else 41
    expected_to=f"{date} {a.cutoff}"

    if live.get("tradeDate")!=date: critical.append("LIVE_TRADE_DATE_MISMATCH")
    if watch.get("tradeDate")!=date: critical.append("WATCHLIST_TRADE_DATE_MISMATCH")
    if live.get("watchlist")!=(watch.get("codes") or []): critical.append("WATCHLIST_CODES_MISMATCH")
    hist=live.get("history") or {}; rows=hist.get("rows") or []
    if hist.get("count")!=expected_count or len(rows)!=expected_count: critical.append("HISTORY_COUNT_MISMATCH")
    if hist.get("from")!=f"{date} 0900" or hist.get("to")!=expected_to: critical.append("HISTORY_RANGE_MISMATCH")
    times=[r.get("atKst") for r in rows]
    expected=[f"{date} 09{m:02d}" for m in range(expected_count)]
    if times!=expected: critical.append("NONCONTIGUOUS_HISTORY")
    pub=live.get("publisher") or {}
    if pub.get("type")!="CLOUDFLARE_WORKER_GITHUB_CONTENTS_API": critical.append("PUBLISHER_TYPE_MISMATCH")
    if pub.get("version")!=BUILD: critical.append("PUBLISHER_BUILD_MISMATCH")
    if health.get("status")!="PASS": critical.append("LIVE_HEALTH_NOT_PASS")
    if health.get("expectedTradeDate")!=date: critical.append("HEALTH_DATE_MISMATCH")
    if health.get("livePublishedAtKst")!=live.get("publishedAtKst"): critical.append("HEALTH_LIVE_PUBLISH_MISMATCH")

    scan=live.get("scan") or {}
    if scan.get("status")!="PASS": operational.append("MARKET_SCAN_NOT_PASS")
    for key in ("turnoverTop","volumeTop","risingLiquid"):
        if not isinstance(scan.get(key),list) or not scan.get(key): operational.append(f"{key.upper()}_MISSING")
    cov=scan.get("coverage") or {}
    if int(cov.get("successfulConfigs") or 0)<4: operational.append("MARKET_SCAN_COVERAGE_INCOMPLETE")
    delta=live.get("scanDelta")
    if not isinstance(delta,dict): operational.append("SCAN_DELTA_MISSING")
    else:
        if int(delta.get("comparedCount") or 0)<=0: operational.append("SCAN_DELTA_EMPTY")
        if not isinstance(delta.get("turnoverAcceleration"),list): operational.append("TURNOVER_ACCELERATION_MISSING")
        expected_from=f"{date} {'0930' if a.cutoff=='0935' else '0935'}"
        if delta.get("fromAtKst")!=expected_from or delta.get("toAtKst")!=expected_to:
            operational.append("SCAN_DELTA_RANGE_MISMATCH")

    out={
      "status":"PASS" if not critical and not operational else "FAIL",
      "criticalStatus":"PASS" if not critical else "FAIL",
      "operationalStatus":"PASS" if not operational else "FAIL",
      "tradeDate":date,"cutoff":a.cutoff,
      "criticalReasons":critical,"operationalReasons":operational,
      "historyCount":len(rows),
      "publisher":pub,
      "scanStatus":scan.get("status"),
      "scanComparedCount": (delta or {}).get("comparedCount") if isinstance(delta,dict) else None,
    }
    print(json.dumps(out,ensure_ascii=False))
    raise SystemExit(0 if out["status"]=="PASS" else 1)

if __name__=="__main__": main()
