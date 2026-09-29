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

    sections=("executable","watchTrigger","radar","deepReviewQueue","structureWarnings")
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

        review=row.get("review") or {}
        if review.get("assistantReviewRequired") is not True:
            err("assistant deep review must be required for every surfaced candidate")
        if review.get("machineScope") != "PREFILTER_AND_EVIDENCE_ONLY":
            err("machine scope must remain prefilter/evidence only")
        if "chartTrace" in review:
            err("heavy chartTrace must not be committed in canonical output")

        setups=row.get("setups") or {}
        for setup in setups.get("all") or []:
            if "maturity" in setup or "score" in setup:
                err("numeric setup quality field forbidden")

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

        nearest=execution.get("nearestAcceptedSupport")
        if nearest is not None:
            matched=False
            for lv in levels:
                if lv.get("importance") != "CORE":
                    continue
                role=(lv.get("role") or {}).get("state")
                line=lv.get("line")
                if role in ("ACCEPTED_SUPPORT","SPRING_RECLAIM") and finite(line) and abs(float(line)-float(nearest)) <= max(0.03, abs(float(nearest))*0.0005):
                    matched=True
                    break
            if not matched:
                err(f"nearestAcceptedSupport not traceable to CORE accepted level: {nearest}")

        price=row.get("price") or {}
        close=price.get("close")
        entry=execution.get("entryReference")
        inv=execution.get("invalidation")
        target=execution.get("nextResistance")
        risk=execution.get("riskPct")
        reward=execution.get("rewardPct")
        rr=execution.get("structuralRR")
        current_vs_entry=execution.get("currentVsEntryPct")

        if finite(close) and finite(entry) and float(entry)>0:
            expected_current_vs_entry=(float(close)/float(entry)-1.0)*100.0
            if not finite(current_vs_entry) or abs(float(current_vs_entry)-expected_current_vs_entry)>0.06:
                err(f"currentVsEntryPct inconsistent: {current_vs_entry} vs {expected_current_vs_entry:.4f}")

        if finite(entry) and finite(inv) and float(entry)>0 and float(inv)<float(entry):
            expected_risk=(float(entry)-float(inv))/float(entry)*100.0
            if not finite(risk) or abs(float(risk)-expected_risk)>0.06:
                err(f"riskPct inconsistent with planned entry: {risk} vs {expected_risk:.4f}")
        elif risk is not None:
            err("riskPct emitted without valid entry-above-invalidation geometry")

        if finite(entry) and finite(target) and float(entry)>0 and float(target)>float(entry):
            expected_reward=(float(target)-float(entry))/float(entry)*100.0
            if not finite(reward) or abs(float(reward)-expected_reward)>0.06:
                err(f"rewardPct inconsistent with planned entry: {reward} vs {expected_reward:.4f}")
            if finite(risk) and float(risk)>0:
                # Compare R/R from the unrounded price geometry. riskPct/rewardPct are
                # rounded display fields and must not be re-used as validator inputs.
                expected_rr=(float(target)-float(entry))/(float(entry)-float(inv))
                if not finite(rr) or abs(float(rr)-expected_rr)>0.06:
                    err(f"structuralRR inconsistent: {rr} vs {expected_rr:.4f}")
        elif reward is not None or rr is not None:
            err("reward/RR emitted without valid overhead target geometry")

        if readiness=="EXECUTABLE":
            if not (setups.get("primary")):
                err("executable without primary setup")
            inv=execution.get("invalidation")
            entry=execution.get("entryReference")
            if inv is None or not finite(inv):
                err("executable without finite invalidation")
            if entry is None or not finite(entry) or float(inv) >= float(entry):
                err("executable without valid planned-entry/invalidation geometry")
            if "FAILED_BREAKOUT" in (execution.get("warnings") or []):
                err("executable despite failed breakout")
            rr=execution.get("structuralRR")
            if rr is not None and (not finite(rr) or float(rr)<=0):
                err(f"bad structuralRR={rr}")

    philosophy=data.get("philosophy") or {}
    if "final chart judgement requires assistant deep review" not in str(philosophy.get("machineRole") or ""):
        errors.append("root philosophy does not preserve assistant deep-review authority")

    candidate_ratio=float((data.get("coverage") or {}).get("candidateRatio") or 0)
    if candidate_ratio > 0.30:
        errors.append(f"candidate explosion ratio={candidate_ratio}")

    out={"status":"PASS" if not errors else "FAIL","errorCount":len(errors),"errors":errors[:100]}
    print(json.dumps(out,ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__=="__main__":
    main()
