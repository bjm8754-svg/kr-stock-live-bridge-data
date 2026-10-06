#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

INDEX_SCHEMA = "MARKET_STRUCTURE_V3_REVIEW_INDEX_V1"
SHARD_SCHEMA = "MARKET_STRUCTURE_V3_REVIEW_SHARD_V1"
SOURCE_SCHEMA = "MARKET_STRUCTURE_V3_REVIEW_PACKET"
CONNECTOR_SAFE_MAX_BYTES = 40000


def encode(obj: dict) -> bytes:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def wrapper(source: dict, rows: list[dict], shard_index: int, shard_count: int) -> dict:
    codes = [str(row.get("code") or "") for row in rows]
    return {
        "schemaVersion": SHARD_SCHEMA,
        "mode": "SHADOW_ONLY",
        "productionWriteAllowed": False,
        "status": source["status"],
        "sourceSchemaVersion": source["sourceSchemaVersion"],
        "reviewPacketSchemaVersion": source["schemaVersion"],
        "tradeDate": source["tradeDate"],
        "generatedAtKst": source["generatedAtKst"],
        "methodologyVersion": source["methodologyVersion"],
        "shardIndex": shard_index,
        "shardCount": shard_count,
        "count": len(rows),
        "codes": codes,
        "deepReviewQueue": rows,
    }


def validate_source(data: dict) -> list[dict]:
    required = ["status", "schemaVersion", "methodologyVersion", "generatedAtKst", "tradeDate", "sourceSchemaVersion", "count", "deepReviewQueue"]
    missing = [key for key in required if key not in data]
    if missing:
        raise SystemExit(f"review packet missing keys: {missing}")
    if data["schemaVersion"] != SOURCE_SCHEMA:
        raise SystemExit(f"unexpected review schema: {data['schemaVersion']}")
    if data["status"] != "PASS":
        raise SystemExit(f"review packet status must be PASS: {data['status']}")
    if data["sourceSchemaVersion"] != "MARKET_STRUCTURE_V3":
        raise SystemExit(f"unexpected source schema: {data['sourceSchemaVersion']}")
    rows = data["deepReviewQueue"]
    if not isinstance(rows, list):
        raise SystemExit("deepReviewQueue must be an array")
    if int(data["count"]) != len(rows):
        raise SystemExit(f"review count mismatch: declared={data['count']} actual={len(rows)}")
    codes = [str(row.get("code") or "") for row in rows]
    if any(len(code) != 6 or not code.isdigit() for code in codes):
        raise SystemExit("review packet contains invalid candidate code")
    if len(codes) != len(set(codes)):
        raise SystemExit("review packet contains duplicate candidate codes")
    return rows


def build_chunks(source: dict, rows: list[dict], max_bytes: int) -> list[list[dict]]:
    if max_bytes < 30000:
        raise SystemExit("max shard bytes is too small")
    chunks: list[list[dict]] = []
    current: list[dict] = []
    for row in rows:
        trial = current + [row]
        size = len(encode(wrapper(source, trial, 99, 99)))
        if size <= max_bytes:
            current = trial
            continue
        if not current:
            code = str(row.get("code") or "?")
            raise SystemExit(f"single candidate exceeds shard cap: code={code} bytes={size} cap={max_bytes}")
        chunks.append(current)
        current = [row]
        size = len(encode(wrapper(source, current, 99, 99)))
        if size > max_bytes:
            code = str(row.get("code") or "?")
            raise SystemExit(f"single candidate exceeds shard cap: code={code} bytes={size} cap={max_bytes}")
    if current:
        chunks.append(current)
    return chunks


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--review", required=True)
    p.add_argument("--index-output", default="market-structure-v3-review-index.json")
    p.add_argument("--output-dir", default=".")
    p.add_argument("--prefix", default="market-structure-v3-review-shard")
    p.add_argument("--max-shard-bytes", type=int, default=CONNECTOR_SAFE_MAX_BYTES)
    args = p.parse_args()

    requested_max_bytes = int(args.max_shard_bytes)
    effective_max_bytes = min(requested_max_bytes, CONNECTOR_SAFE_MAX_BYTES)

    source = json.loads(Path(args.review).read_text(encoding="utf-8"))
    rows = validate_source(source)
    chunks = build_chunks(source, rows, effective_max_bytes)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for old in out_dir.glob(f"{args.prefix}-*.json"):
        old.unlink()

    shard_meta = []
    total = len(chunks)
    flattened_codes: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        payload = wrapper(source, chunk, i, total)
        raw = encode(payload)
        if len(raw) > effective_max_bytes:
            raise SystemExit(f"final shard exceeds cap: shard={i} bytes={len(raw)} cap={effective_max_bytes}")
        path = out_dir / f"{args.prefix}-{i:02d}.json"
        path.write_bytes(raw + b"\n")
        codes = payload["codes"]
        flattened_codes.extend(codes)
        shard_meta.append({
            "path": path.name,
            "shardIndex": i,
            "count": len(chunk),
            "codes": codes,
            "byteSize": len(raw) + 1,
            "sha256": hashlib.sha256(raw + b"\n").hexdigest(),
        })

    expected_codes = [str(row["code"]) for row in rows]
    if flattened_codes != expected_codes:
        raise SystemExit("sharded candidate order/codes mismatch source review packet")

    index = {
        "schemaVersion": INDEX_SCHEMA,
        "mode": "SHADOW_ONLY",
        "productionWriteAllowed": False,
        "status": source["status"],
        "sourceSchemaVersion": source["sourceSchemaVersion"],
        "reviewPacketSchemaVersion": source["schemaVersion"],
        "tradeDate": source["tradeDate"],
        "generatedAtKst": source["generatedAtKst"],
        "methodologyVersion": source["methodologyVersion"],
        "totalCount": len(rows),
        "shardCount": total,
        "codes": expected_codes,
        "requestedMaxShardBytes": requested_max_bytes,
        "maxShardBytes": effective_max_bytes,
        "shards": shard_meta,
    }
    Path(args.index_output).write_bytes(encode(index) + b"\n")

    loaded_index = json.loads(Path(args.index_output).read_text(encoding="utf-8"))
    if loaded_index["schemaVersion"] != INDEX_SCHEMA or loaded_index["totalCount"] != len(rows):
        raise SystemExit("review shard index read-back validation failed")
    reconstructed: list[str] = []
    for meta in loaded_index["shards"]:
        path = out_dir / meta["path"]
        raw = path.read_bytes()
        if len(raw) != int(meta["byteSize"]):
            raise SystemExit(f"shard size read-back mismatch: {path}")
        if hashlib.sha256(raw).hexdigest() != meta["sha256"]:
            raise SystemExit(f"shard sha256 read-back mismatch: {path}")
        shard = json.loads(raw.decode("utf-8"))
        for key in ("tradeDate", "generatedAtKst", "methodologyVersion"):
            if shard.get(key) != loaded_index.get(key):
                raise SystemExit(f"shard linkage mismatch: {path} key={key}")
        if shard.get("shardCount") != loaded_index["shardCount"]:
            raise SystemExit(f"shard count metadata mismatch: {path}")
        if shard.get("codes") != meta["codes"]:
            raise SystemExit(f"shard codes mismatch: {path}")
        reconstructed.extend(shard["codes"])
    if reconstructed != loaded_index["codes"]:
        raise SystemExit("review shard reconstruction mismatch")

    print(json.dumps({
        "status": "PASS",
        "tradeDate": source["tradeDate"],
        "totalCount": len(rows),
        "shardCount": total,
        "requestedMaxShardBytes": requested_max_bytes,
        "maxShardBytes": effective_max_bytes,
        "largestShardBytes": max((x["byteSize"] for x in shard_meta), default=0),
        "indexOutput": args.index_output,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
