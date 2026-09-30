#!/usr/bin/env python3
import argparse
import json
import math
from pathlib import Path

CHART_STATES = {"ATTACK_CANDIDATE", "PROBE_CANDIDATE", "WATCH", "REJECT"}
PLAN_STATES = {"ATTACK_PLAN", "PROBE_PLAN", "WATCH", "PASS"}
LANES = {
    "companyQuality": {"SUPPORTIVE", "MIXED", "ADVERSE", "UNKNOWN"},
    "earningsRevision": {"UP_REVISION", "STABLE", "DOWN_REVISION", "UNKNOWN"},
    "catalyst": {"ACTIVE", "UPCOMING", "NONE_IDENTIFIED", "UNKNOWN"},
    "industryMacro": {"TAILWIND", "NEUTRAL", "HEADWIND", "UNKNOWN"},
    "globalUsLead": {"CONFIRMING", "NEUTRAL", "CONTRADICTING", "NOT_MATERIAL", "UNKNOWN"},
    "eventRisk": {"LOW", "MODERATE", "HIGH", "UNKNOWN"},
}


def finite(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(float(v))


def walk_forbidden(obj, path="root", errors=None):
    if errors is None:
        errors = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            lk = str(k).lower()
            if lk in {"score", "actionscore", "maturityscore", "rankscore"}:
                errors.append(f"{path}.{k}: aggregate score field forbidden")
            walk_forbidden(v, f"{path}.{k}", errors)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk_forbidden(v, f"{path}[{i}]", errors)
    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    a = ap.parse_args()
    d = json.loads(Path(a.path).read_text(encoding="utf-8"))
    errors = []

    if d.get("schemaVersion") != "V3_0815_SHADOW_PLAN_V1":
        errors.append("wrong schemaVersion")
    if d.get("mode") != "SHADOW_ONLY":
        errors.append("mode must be SHADOW_ONLY")
    if d.get("productionWriteAllowed") is not False:
        errors.append("productionWriteAllowed must be false")

    src = d.get("source") or {}
    if src.get("freshnessStatus") != "PASS":
        errors.append("source freshness must PASS")
    if not str(src.get("methodologyVersion") or "").startswith("MARKET_STRUCTURE_V3_"):
        errors.append("unexpected V3 methodology")
    if not src.get("tradeDate"):
        errors.append("source tradeDate missing")
    if src.get("reviewPacketValidated") is not True:
        errors.append("review packet not validated")
    if src.get("canonicalValidated") is not True:
        errors.append("canonical not validated")

    reviews = d.get("chartReview")
    if not isinstance(reviews, list):
        errors.append("chartReview must be array")
        reviews = []
    if len(reviews) > 36:
        errors.append("chartReview exceeds 36")

    review_by_code = {}
    for i, r in enumerate(reviews):
        code = str(r.get("code") or "")
        if not code:
            errors.append(f"chartReview[{i}]: code missing")
            continue
        if code in review_by_code:
            errors.append(f"chartReview[{i}]: duplicate code={code}")
        review_by_code[code] = r
        st = r.get("chartState")
        if st not in CHART_STATES:
            errors.append(f"chartReview:{code}: bad chartState={st}")
        if st != "REJECT":
            for k in ("thesis", "importantZone", "confirmation", "invalidation", "chaseJudgement", "counterargument"):
                if r.get(k) in (None, ""):
                    errors.append(f"chartReview:{code}: {k} missing")

    plans = d.get("plans")
    if not isinstance(plans, list):
        errors.append("plans must be array")
        plans = []

    for i, p in enumerate(plans):
        code = str(p.get("code") or "")
        st = p.get("planState")
        if not code:
            errors.append(f"plans[{i}]: code missing")
            continue
        if st not in PLAN_STATES:
            errors.append(f"plan:{code}: bad planState={st}")

        cr = review_by_code.get(code)
        if cr and cr.get("chartState") == "REJECT" and st in {"ATTACK_PLAN", "PROBE_PLAN"}:
            errors.append(f"plan:{code}: chart REJECT cannot become {st}")

        ev = p.get("externalEvidence") or {}
        for lane, allowed in LANES.items():
            state = (ev.get(lane) or {}).get("state") if isinstance(ev.get(lane), dict) else ev.get(lane)
            if state not in allowed:
                errors.append(f"plan:{code}: {lane} invalid/missing state={state}")

        if st in {"ATTACK_PLAN", "PROBE_PLAN"}:
            for k in ("actionableZone", "trigger", "invalidation", "noChase", "counterargument"):
                if p.get(k) in (None, ""):
                    errors.append(f"plan:{code}: {k} missing")
            inv = p.get("invalidation")
            if isinstance(inv, (int, float)) and not finite(inv):
                errors.append(f"plan:{code}: invalid invalidation")

        rr = p.get("structuralRR")
        if rr is not None and (not finite(rr) or float(rr) <= 0):
            errors.append(f"plan:{code}: bad structuralRR={rr}")

    errors.extend(walk_forbidden(d))
    out = {"status": "PASS" if not errors else "FAIL", "errorCount": len(errors), "errors": errors[:100]}
    print(json.dumps(out, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
