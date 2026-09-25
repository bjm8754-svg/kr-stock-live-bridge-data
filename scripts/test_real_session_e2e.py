#!/usr/bin/env python3
import json, subprocess, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VAL=ROOT/"scripts"/"validate_real_session_e2e.py"
DATE="20260925"

def row(m):
    return {"atKst":f"{DATE} 09{m:02d}","stocks":{"000001":{"currentPrice":1000+m,"volume":100+m,"tradingValue":1000+m,"marketStatus":"OPEN"}}}

def fixture(cutoff="0935"):
    n=36 if cutoff=="0935" else 41
    published=f"2026-09-25 09:{35 if cutoff=='0935' else 40}:01.000 KST"
    live={
      "tradeDate":DATE,"publishedAtKst":published,
      "publisher":{"type":"CLOUDFLARE_WORKER_GITHUB_CONTENTS_API","version":"worker_v3_hardened_money_scan_v3"},
      "watchlist":["000001"],
      "history":{"count":n,"from":f"{DATE} 0900","to":f"{DATE} {cutoff}","rows":[row(i) for i in range(n)]},
      "scan":{"status":"PASS","coverage":{"successfulConfigs":4},"turnoverTop":[{"code":"000001"}],"volumeTop":[{"code":"000001"}],"risingLiquid":[{"code":"000001"}]},
      "scanDelta":{"fromAtKst":f"{DATE} {'0930' if cutoff=='0935' else '0935'}","toAtKst":f"{DATE} {cutoff}","comparedCount":1,"turnoverAcceleration":[{"code":"000001","deltaTradingValue":100}],"newEntries":[]}
    }
    watch={"tradeDate":DATE,"codes":["000001"]}
    health={"status":"PASS","expectedTradeDate":DATE,"livePublishedAtKst":published}
    return live,watch,health

def run(cutoff,live,watch,health):
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        for name,obj in [("live.json",live),("watchlist.json",watch),("live-health.json",health)]:
            (td/name).write_text(json.dumps(obj),encoding="utf-8")
        cp=subprocess.run(["python",str(VAL),"--cutoff",cutoff,"--asof-date",DATE,
                           "--live",str(td/"live.json"),"--watchlist",str(td/"watchlist.json"),"--health",str(td/"live-health.json")],
                           cwd=ROOT,capture_output=True,text=True)
        return cp.returncode,json.loads(cp.stdout)

class E2EValidatorTests(unittest.TestCase):
    def test_0935_pass(self):
        x=fixture("0935"); rc,out=run("0935",*x)
        self.assertEqual(rc,0); self.assertEqual(out["status"],"PASS")
    def test_0940_pass(self):
        x=fixture("0940"); rc,out=run("0940",*x)
        self.assertEqual(rc,0); self.assertEqual(out["status"],"PASS")
    def test_wrong_build_fails(self):
        live,watch,health=fixture("0935"); live["publisher"]["version"]="old"
        rc,out=run("0935",live,watch,health)
        self.assertNotEqual(rc,0); self.assertIn("PUBLISHER_BUILD_MISMATCH",out["criticalReasons"])
    def test_missing_scan_delta_fails_operational(self):
        live,watch,health=fixture("0935"); live["scanDelta"]=None
        rc,out=run("0935",live,watch,health)
        self.assertNotEqual(rc,0); self.assertEqual(out["criticalStatus"],"PASS"); self.assertEqual(out["operationalStatus"],"FAIL")

if __name__=="__main__": unittest.main()
