#!/usr/bin/env python3
import argparse
import json
import math
from pathlib import Path


ALLOWED_INVALIDATION_SOURCES = {
    "RECENT_REFERENCE_LOW",
    "PRIOR_REFERENCE_LOW",
    "CORE_ZONE_LOW",
}


def finite_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(float(v))


def close_enough(a, b, tol=0.03):
    return abs(float(a) - float(b)) <= tol


def main():
    p = argparse.ArgumentParser(description="Cross-sectional invariants for scanner execution levels.")
    p.add_argument("path")
    args = p.parse_args()

    data = json.loads(Path(args.path).read_text(encoding="utf-8"))
    rows = data.get("allCandidates") or []
    errors = []
    checked = 0
    rr_checked = 0
    invalidation_above_ranking_support = 0

    for row in rows:
        code = str(row.get("code") or "?")
        close = row.get("close")
        plan = row.get("entryPlan")
        if not isinstance(plan, dict) or not finite_number(close) or float(close) <= 0:
            continue

        checked += 1
        close = float(close)
        nearest = plan.get("nearestSupport")
        invalidation = plan.get("invalidationCandidate")
        invalidation_source = plan.get("invalidationSource")
        nxt = plan.get("nextResistance")
        rr = plan.get("structuralRR")
        hierarchy = plan.get("supportHierarchy") or {}

        def err(msg):
            errors.append(f"{code}: {msg}")

        if nearest is not None:
            if not finite_number(nearest) or not (0 < float(nearest) <= close):
                err(f"invalid nearestSupport={nearest} close={close}")

        if invalidation is not None:
            if not finite_number(invalidation) or not (0 < float(invalidation) <= close):
                err(f"invalid invalidation={invalidation} close={close}")
            if invalidation_source not in ALLOWED_INVALIDATION_SOURCES:
                err(f"invalid invalidationSource={invalidation_source}")
            if nearest is not None and finite_number(nearest) and float(invalidation) > float(nearest) + 0.01:
                # The ranking support intentionally ignores levels that are too close to current
                # price. A valid reference-low invalidation can therefore sit above that deeper
                # ranking support; this is diagnostic, not a structural error.
                invalidation_above_ranking_support += 1

            if invalidation_source in ("RECENT_REFERENCE_LOW", "PRIOR_REFERENCE_LOW"):
                ref_low = hierarchy.get("referenceLowInvalidationCandidate")
                if ref_low is None or not finite_number(ref_low) or not close_enough(invalidation, ref_low):
                    err(f"reference invalidation not traceable to hierarchy: {invalidation} vs {ref_low}")
            elif invalidation_source == "CORE_ZONE_LOW":
                core = row.get("coreResistance") or {}
                zone_low = core.get("zoneLow")
                if zone_low is None or not finite_number(zone_low) or not close_enough(invalidation, zone_low):
                    err(f"core invalidation not traceable to zoneLow: {invalidation} vs {zone_low}")
        elif invalidation_source is not None:
            err(f"invalidationSource without invalidation={invalidation_source}")

        if nxt is not None:
            if not finite_number(nxt) or float(nxt) <= close:
                err(f"invalid nextResistance={nxt} close={close}")

        for key in (
            "primaryReferenceSupport",
            "referenceLowInvalidationCandidate",
            "coreSupport",
            "longMaSupport",
        ):
            value = hierarchy.get(key)
            if value is not None and (not finite_number(value) or not (0 < float(value) <= close)):
                err(f"invalid hierarchy {key}={value} close={close}")

        if rr is not None:
            rr_checked += 1
            if not finite_number(rr) or float(rr) <= 0:
                err(f"invalid structuralRR={rr}")
            elif invalidation is None or nxt is None:
                err("structuralRR exists without invalidation/nextResistance")
            elif finite_number(invalidation) and finite_number(nxt):
                risk = close / float(invalidation) - 1.0
                reward = float(nxt) / close - 1.0
                if risk <= 0 or reward <= 0:
                    err(f"nonpositive R/R legs risk={risk} reward={reward}")
                else:
                    expected = reward / risk
                    if not close_enough(float(rr), expected):
                        err(f"structuralRR mismatch got={rr} expected={expected:.4f}")

        # Never infer a hard stop from a long MA alone.
        if invalidation_source and invalidation_source.startswith("MA"):
            err(f"long-MA-only invalidation forbidden: {invalidation_source}")

    out = {
        "status": "PASS" if not errors else "FAIL",
        "candidateCount": len(rows),
        "entryPlanChecked": checked,
        "rrChecked": rr_checked,
        "invalidationAboveRankingSupportCount": invalidation_above_ranking_support,
        "errorCount": len(errors),
        "errors": errors[:100],
    }
    print(json.dumps(out, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
