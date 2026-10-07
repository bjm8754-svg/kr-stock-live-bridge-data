#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

INDEX_SCHEMA = "MARKET_STRUCTURE_V3_REVIEW_INDEX_V1"
HANDOFF_SCHEMA = "MARKET_STRUCTURE_V3_HANDOFF_V1"
BATCH_SCHEMA = "V3_EOD_DEEP_REVIEW_BATCH_V1"
FINAL_SCHEMA = "V3_EOD_DEEP_REVIEW_V1"
BATCH_COUNT = 3
BATCH_WIDTH = 12
ALLOWED_STATES = {"ATTACK_CANDIDATE", "PROBE_CANDIDATE", "WATCH", "REJECT"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_review(row: dict, code: str, where: str) -> None:
    if str(row.get("code") or "") != code:
        raise RuntimeError(f"{where}:code_mismatch")
    state = row.get("chartState")
    if state not in ALLOWED_STATES:
        raise RuntimeError(f"{where}:bad_chartState={state}")
    if not row.get("thesis"):
        raise RuntimeError(f"{where}:thesis_missing")
    if state != "REJECT":
        for key in ("importantZone", "confirmation", "invalidation", "chaseJudgement", "counterargument"):
            if row.get(key) in (None, ""):
                raise RuntimeError(f"{where}:{key}_missing")


def expected_slice(codes: list[str], batch_index: int) -> list[str]:
    start = (batch_index - 1) * BATCH_WIDTH
    return codes[start : start + BATCH_WIDTH]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--output", default="v3-eod-deep-review.json")
    ap.add_argument("--allow-incomplete", action="store_true")
    args = ap.parse_args()
    root = Path(args.root)

    handoff_path = root / "market-structure-v3-handoff.json"
    index_path = root / "market-structure-v3-review-index.json"
    handoff = load(handoff_path)
    index = load(index_path)

    if handoff.get("schemaVersion") != HANDOFF_SCHEMA or handoff.get("status") != "PASS":
        raise RuntimeError("HANDOFF_INVALID")
    if index.get("schemaVersion") != INDEX_SCHEMA or index.get("status") != "PASS":
        raise RuntimeError("INDEX_INVALID")
    for key in ("tradeDate", "generatedAtKst", "methodologyVersion"):
        if handoff.get(key) != index.get(key):
            raise RuntimeError(f"HANDOFF_INDEX_MISMATCH:{key}")

    codes = [str(x) for x in (index.get("codes") or [])]
    if len(codes) != int(index.get("totalCount") or 0):
        raise RuntimeError("INDEX_CODE_COUNT_MISMATCH")
    if len(codes) > 36 or len(codes) != len(set(codes)):
        raise RuntimeError("INDEX_CODES_INVALID")

    batch_paths = [root / f"v3-eod-deep-review-batch-{i}.json" for i in range(1, BATCH_COUNT + 1)]
    batches: list[dict] = []
    incomplete: list[str] = []

    for i, path in enumerate(batch_paths, start=1):
        if not path.exists():
            incomplete.append(f"missing:{path.name}")
            continue
        try:
            batch = load(path)
        except Exception as exc:
            incomplete.append(f"parse:{path.name}:{type(exc).__name__}")
            continue

        expected = expected_slice(codes, i)
        problems = []
        if batch.get("schemaVersion") != BATCH_SCHEMA:
            problems.append("schema")
        if batch.get("mode") != "SHADOW_ONLY" or batch.get("productionWriteAllowed") is not False:
            problems.append("mode")
        if batch.get("status") != "PASS":
            problems.append("status")
        if batch.get("sourceTradeDate") != index.get("tradeDate"):
            problems.append("tradeDate")
        if batch.get("sourceIndexGeneratedAtKst") != index.get("generatedAtKst"):
            problems.append("indexGeneratedAt")
        if batch.get("methodologyVersion") != index.get("methodologyVersion"):
            problems.append("methodology")
        if int(batch.get("sourceWorkflowRunId") or -1) != int((handoff.get("source") or {}).get("workflowRunId") or -2):
            problems.append("workflowRunId")
        if int(batch.get("batchIndex") or 0) != i or int(batch.get("batchCount") or 0) != BATCH_COUNT:
            problems.append("batchMeta")
        if [str(x) for x in (batch.get("candidateCodes") or [])] != expected:
            problems.append("candidateCodes")
        reviews = batch.get("reviews")
        if not isinstance(reviews, list) or len(reviews) != len(expected):
            problems.append("reviewCount")
        if problems:
            incomplete.append(f"invalid:{path.name}:{','.join(problems)}")
            continue

        for pos, (code, review) in enumerate(zip(expected, reviews), start=1):
            validate_review(review, code, f"{path.name}[{pos}]")
        batches.append(batch)

    if incomplete:
        out = {"status": "INCOMPLETE", "sourceTradeDate": index.get("tradeDate"), "reasons": incomplete}
        print(json.dumps(out, ensure_ascii=False))
        if args.allow_incomplete:
            p = root / args.output
            if p.exists():
                p.unlink()
            return
        raise SystemExit(2)

    merged_reviews: list[dict] = []
    merged_codes: list[str] = []
    batch_meta = []
    for i, (path, batch) in enumerate(zip(batch_paths, batches), start=1):
        merged_reviews.extend(batch["reviews"])
        merged_codes.extend(batch["candidateCodes"])
        batch_meta.append({
            "path": path.name,
            "batchIndex": i,
            "count": len(batch["candidateCodes"]),
            "sha256": sha256(path),
            "reviewedAtKst": batch.get("reviewedAtKst"),
        })

    if merged_codes != codes:
        raise RuntimeError("MERGED_CODE_ORDER_MISMATCH")
    if len(merged_reviews) != len(codes):
        raise RuntimeError("MERGED_REVIEW_COUNT_MISMATCH")

    result = {
        "schemaVersion": FINAL_SCHEMA,
        "mode": "SHADOW_ONLY",
        "productionWriteAllowed": False,
        "status": "PASS",
        "sourceTradeDate": index.get("tradeDate"),
        "sourceWorkflowRunId": (handoff.get("source") or {}).get("workflowRunId"),
        "sourceIndexGeneratedAtKst": index.get("generatedAtKst"),
        "methodologyVersion": index.get("methodologyVersion"),
        "assistantDeepReviewCompleted": True,
        "batchCount": BATCH_COUNT,
        "reviewCount": len(merged_reviews),
        "codes": merged_codes,
        "reviews": merged_reviews,
        "batches": batch_meta,
    }
    out_path = root / args.output
    out_path.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "sourceTradeDate": result["sourceTradeDate"], "reviewCount": result["reviewCount"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
