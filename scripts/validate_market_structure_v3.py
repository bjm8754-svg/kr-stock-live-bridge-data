#!/usr/bin/env python3
import argparse
import json
import math
from pathlib import Path


ALLOWED_READINESS = {"EXECUTABLE","WATCH_TRIGGER","RADAR","REJECT"}
ALLOWED_ROLE_STATES = {
    "NONE","FAILED_BREAKOUT","SPRING_RECLAIM","DECISION_ZONE",
    "ACCEPTED_SUPPORT","BREAKOUT_PENDING","SUPPORT_CANDIDATE",
    "ACCEPTED_RESISTANCE","BREAKDOWN_PENDING","RESISTANCE_CANDIDATE",
}


def finite(v):
    return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(float(v))


def main():
    p=argparse.ArgumentParser()
    p.add_argument("path")
    args=p.parse_args()
    data=json.loads(Path(args.path).read_text(encoding="utf-8"))
    errors=[]

    if data.get("schemaVersion")!="MARKET_STRUCTURE_V3":
        errors.append("wrong schemaVersion")
    if "score" in data or "actionScore" in data:
        errors.append("aggregate score leaked into root output")

    sections=("executable","watchTrigger","radar","structureWarnings")
    rows=[]
    for section in sections:
        xs=data.get(section)
        if not isinstance(xs,list):
            errors.append(f"{section} is not array")
            continue
        rows.extend((section,x) for x in xs)

    for section,row in rows:
        code=str(row.get("code") or "?")
        def err(msg): errors.append(f"{section}:{code}: {msg}")

        if "score" in row or "actionScore" in row:
            err("aggregate score field forbidden")
        execution=row.get("execution") or {}
        readiness=execution.get("readiness")
        if readiness not in ALLOWED_READINESS:
            err(f"bad readiness={readiness}")
        if section=="executable" and readiness!="EXECUTABLE":
            err("executable section/readiness mismatch")
        if section=="watchTrigger" and readiness!="WATCH_TRIGGER":
            err("watchTrigger section/readiness mismatch")
        if section=="radar" and readiness!="RADAR":
            err("radar section/readiness mismatch")

        confirmation=row.get("confirmation") or {}
        rsi=confirmation.get("rsi") or {}
        if rsi.get("auto7030Trigger") is not False:
            err("RSI 70/30 auto trigger must be false")

        structure=row.get("structure") or {}
        levels=structure.get("levels") or []
        for lv in levels:
            role=(lv.get("role") or {}).get("state")
            if role not in ALLOWED_ROLE_STATES:
                err(f"unknown role state={role}")

        if readiness=="EXECUTABLE":
            if not ((row.get("setups") or {}).get("primary")):
                err("executable without primary setup")
            inv=execution.get("invalidation")
            if inv is None or not finite(inv):
                err("executable without finite invalidation")
            if "FAILED_BREAKOUT" in (execution.get("warnings") or []):
                err("executable despite failed breakout")
            rr=execution.get("structuralRR")
            if rr is not None and (not finite(rr) or float(rr)<=0):
                err(f"bad structuralRR={rr}")

    candidate_ratio=float((data.get("coverage") or {}).get("candidateRatio") or 0)
    if candidate_ratio > 0.30:
        errors.append(f"candidate explosion ratio={candidate_ratio}")

    out={"status":"PASS" if not errors else "FAIL","errorCount":len(errors),"errors":errors[:100]}
    print(json.dumps(out,ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__=="__main__":
    main()
