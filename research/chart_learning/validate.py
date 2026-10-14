#!/usr/bin/env python3
"""Persistent chart-learning document integrity gate. Stdlib only; no network."""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "research" / "chart_learning"

def fail(msg: str) -> None:
    raise RuntimeError("CHART_LEARNING_INTEGRITY_FAIL: " + msg)

def load_manifest() -> dict:
    return json.loads((BASE / "MANIFEST.json").read_text(encoding="utf-8"))

def validate() -> tuple[dict, list[dict]]:
    m = load_manifest()
    if m.get("schema") != "V3_CHART_LEARNING_MANIFEST_V1":
        fail("wrong manifest schema")
    if type(m.get("revision")) is not int or m["revision"] < 1:
        fail("invalid learning revision")
    if m.get("productionWriteAllowed") is not False or m.get("manualGateRequired") is not True:
        fail("production isolation or mandatory session gate missing")
    if m.get("performanceVerified") is not False and m.get("latestEvidenceStatus") == "DIAGNOSTIC_NOT_CLEAN_BLIND":
        fail("diagnostic is not validated predictive performance")
    paths = m.get("requiredPaths")
    if not isinstance(paths, list) or len(paths) < 12 or len(paths) != len(set(paths)):
        fail("requiredPaths missing/duplicate")
    for p in paths:
        path = ROOT / p
        if not path.is_file() or path.stat().st_size == 0:
            fail("missing/empty mandatory artifact: " + p)
        if path.resolve() != path and not path.resolve().is_relative_to(ROOT.resolve()):
            fail("path traversal: " + p)
    master = (BASE / "MASTER.md").read_text(encoding="utf-8")
    changelog = (BASE / "CHANGELOG.md").read_text(encoding="utf-8")
    startup = (BASE / "START_HERE.md").read_text(encoding="utf-8")
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    protocol = (ROOT / "ASSISTANT_CHART_DEEP_REVIEW_PROTOCOL.md").read_text(encoding="utf-8")
    for path_label, body in (("AGENTS.md", agents), ("README.md", readme), ("deep-review protocol", protocol)):
        if "research/chart_learning/START_HERE.md" not in body:
            fail("startup gate not linked in " + path_label)
    if f"Learning revision:** {m['revision']}" not in startup:
        fail("startup revision differs from manifest")
    if f"Revision {m['revision']}" not in changelog:
        fail("changelog missing declared revision")
    rule_ids = []
    for rule in m.get("rules", []):
        rid = rule.get("id", "")
        if not re.fullmatch(r"(R|H)-\d{3}", rid):
            fail("bad rule id: " + rid)
        if rule.get("status") not in ("CANONICAL", "HYPOTHESIS", "SUPERSEDED"):
            fail("unknown rule status: " + rid)
        if "### " + rid not in master:
            fail("manifest rule absent from MASTER: " + rid)
        rule_ids.append(rid)
    if len(rule_ids) != len(set(rule_ids)):
        fail("duplicate rule IDs")
    lesson_path = BASE / "LESSONS.jsonl"
    lesson_lines = lesson_path.read_text(encoding="utf-8").splitlines()
    if not lesson_lines or any(not line.strip() for line in lesson_lines):
        fail("empty lesson or blank line")
    lessons = [json.loads(line) for line in lesson_lines]
    ids = []
    for entry in lessons:
        lid = entry.get("id", "")
        if not re.fullmatch(r"L-\d{3}", lid):
            fail("invalid lesson id: " + lid)
        if not all(entry.get(k) for k in ("date", "status", "title", "evidence", "change", "nextTest")):
            fail("incomplete lesson: " + lid)
        if not set(entry.get("rules", [])).issubset(set(rule_ids)):
            fail("lesson references nonexistent rule: " + lid)
        ids.append(lid)
    if len(ids) != len(set(ids)) or len(ids) != m.get("lessonCount"):
        fail("lesson ID uniqueness/count mismatch")
    cases = (BASE / "CASES.md").read_text(encoding="utf-8")
    for lid in ids:
        if lid not in cases and lid not in master and lid not in (BASE / "EXPERIMENTS.md").read_text(encoding="utf-8"):
            fail("lesson never referenced outside ledger: " + lid)
    registry = (BASE / "SOURCE_REGISTRY.md").read_text(encoding="utf-8")
    if m.get("sourceRegistry") != "research/chart_learning/SOURCE_REGISTRY.md":
        fail("original source registry must be manifest-authoritative")
    for token in ("91", "001–091", "/차트공부_원자료_20260928/images/", "차트공부_CANONICAL_MASTER_FINAL_20260929.docx", "KakaoTalkChats.txt", "YBM_METHOD_AUDIT.md", "UNVERIFIED"):
        if token not in registry:
            fail("missing original source inventory: " + token)
    if "SOURCE_REGISTRY.md" not in startup or "SOURCE_REGISTRY.md" not in agents or "SOURCE_REGISTRY.md" not in master:
        fail("original source recovery not linked in startup/agent/master")
    inv = m.get("externalSourceInventory", {})
    if inv.get("chartStudyOriginalImages", {}).get("expectedCount") != 91:
        fail("image archive expected count drift")
    if inv.get("yangbongmanText", {}).get("originalPictureCompleteness") != "UNVERIFIED":
        fail("Yangbongman photo completeness cannot be claimed from text")
    if any(v.get("ciCanVerify") is not False for v in inv.values()):
        fail("CI cannot verify ChatGPT Library contents")
    if "### R-010 — Analytical pluralism" not in master:
        fail("missing no-privileged-view canonical rule")
    if "ONE VIEW" not in master or "YBM is a view among many" not in registry:
        fail("source methodology incorrectly elevated above independent market analysis")
    if "one perspective" not in startup or "ONE historical view among many" not in agents:
        fail("new-session pluralism boundary disconnected")
    bmk = (BASE / "MINIMUM_COMPETENCE_BENCHMARK.md").read_text(encoding="utf-8")
    mc = m.get("minimumCompetence", {})
    if mc.get("path") != "research/chart_learning/MINIMUM_COMPETENCE_BENCHMARK.md" or mc.get("acceptanceStatus") != "NOT_DEMONSTRATED":
        fail("minimum competence benchmark not registered or falsely marked achieved")
    if mc.get("expertRealizedPerformance") != "UNKNOWN":
        fail("expert's realized record cannot be invented")
    if mc.get("criteria") != [f"M-{i:02d}" for i in range(1, 8)]:
        fail("minimum competence criteria drift")
    for criterion in mc["criteria"]:
        if criterion not in bmk:
            fail("minimum benchmark lacks " + criterion)
    if "five expert" not in bmk.lower() or "MINIMUM" not in bmk:
        fail("user-defined minimum expert standard missing")
    if "MINIMUM_COMPETENCE_BENCHMARK.md" not in startup or "MINIMUM_COMPETENCE_BENCHMARK.md" not in master or "MINIMUM_COMPETENCE_BENCHMARK.md" not in agents:
        fail("minimum benchmark not linked into new-session preflight")
    if "### R-011 — Review interval is NOT swing holding horizon" not in master:
        fail("swing holding horizon confused with review interval")
    if "3-trading-day decision/review cadence" not in master or "right-censored" not in master:
        fail("3-session review and open trade disposition must be distinguished")
    if "C-005 — Three-session review cadence" not in cases:
        fail("S01 horizon regression case missing")
    if "### R-012 — A HOLD decision must preserve share count" not in master:
        fail("true HOLD shares-invariance guard missing")
    if m.get("knownExecutionLimitation", {}).get("status") != "UNFIXED_IN_EXISTING_S01":
        fail("legacy S01 HOLD semantics must remain flagged UNFIXED until full integration verified")
    if "C-006 — Legacy S01 HOLD label" not in cases:
        fail("legacy HOLD-rebalance regression case missing")
    if m.get("entrypoint") != "research/chart_learning/START_HERE.md":
        fail("incorrect startup entrypoint")
    return m, lessons

def git_show(path: str) -> str | None:
    try:
        p = subprocess.run(["git", "show", "HEAD^:" + path], cwd=ROOT, capture_output=True, text=True, check=False)
    except OSError:
        return None
    return p.stdout if p.returncode == 0 else None

def check_prior_revision(new_m: dict, lessons: list[dict]) -> None:
    old_raw = git_show("research/chart_learning/MANIFEST.json")
    if old_raw is None:
        return
    old_m = json.loads(old_raw)
    prior_rules = {r["id"] for r in old_m.get("rules", [])}
    current_rules = {r["id"] for r in new_m.get("rules", [])}
    if not prior_rules.issubset(current_rules):
        fail("previous rule ID deleted; preserve and SUPERSEDE instead")
    older_ledger = git_show("research/chart_learning/LESSONS.jsonl")
    current_ledger = (BASE / "LESSONS.jsonl").read_text(encoding="utf-8")
    if older_ledger is not None and not current_ledger.startswith(older_ledger):
        fail("lesson ledger was deleted/rewritten; append only")
    if old_raw != (BASE / "MANIFEST.json").read_text(encoding="utf-8"):
        if new_m["revision"] <= int(old_m["revision"]):
            fail("manifest changed without revision increment")
    else:
        changed = subprocess.run(
            ["git", "diff", "--name-only", "HEAD^", "HEAD", "--", "research/chart_learning", "AGENTS.md", "README.md", "ASSISTANT_CHART_DEEP_REVIEW_PROTOCOL.md"],
            cwd=ROOT, capture_output=True, text=True, check=False
        )
        if changed.returncode == 0 and changed.stdout.strip():
            fail("research artifacts changed without manifest revision increment")

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-append-only", action="store_true", help="compare with preceding commit if available")
    args = ap.parse_args()
    try:
        m, lessons = validate()
        if args.check_append_only:
            check_prior_revision(m, lessons)
        print(f"CHART_LEARNING_INTEGRITY: PASS revision={m['revision']} lessons={len(lessons)} rules={len(m['rules'])} productionWriteAllowed=false")
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)

if __name__ == "__main__":
    main()
