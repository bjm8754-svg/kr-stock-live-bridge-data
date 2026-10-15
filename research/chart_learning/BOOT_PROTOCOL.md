# BOOT_PROTOCOL — fresh-chat, user-triggered V3 methodology research

**BOOT_PROTOCOL_VERSION:** 1
**Intent:** user-invoked, reproducible **methodology research** entrypoint. The ChatGPT model weights do not retrain. A GitHub file cannot autonomously force every new conversation to read it. This protocol works only when a user supplies its self-contained prompt (or the assistant actually discovers and follows this file). Passing CI does not prove cross-chat compliance.

## Copy/paste startup message (Korean; preserve meaning)

```text
[차트연구 부팅 / 연구 전용]
GitHub bjm8754-svg/kr-stock-live-bridge-data의 최신 main에서 research/chart_learning/BOOT_PROTOCOL.md를 실제로 읽고 그 절차를 실행해. 관련 MASTER·LESSONS·STUDY_PROGRESS와 차트술사 원본 91장 연구 맥락을 복원한 뒤, HEAD SHA·학습 버전·복원 상태·다음 연구 과제를 먼저 보고해. 목적은 이미 완성된 스캐너 사용이나 모의매매 반복이 아니라 외부에 축적되는 독자적 차트 분석 방법론을 연구·검증·개선하는 것. S02는 중단. 자료를 못 읽으면 추측하지 말고 NOT VERIFIED로 멈춰. 검증되면 최신 진도에서 공부를 이어가되, 승인 없이 신규 스캔·D04·실주문·운영 변경은 하지 마.
```

**Stable link:** https://github.com/bjm8754-svg/kr-stock-live-bridge-data/blob/main/research/chart_learning/BOOT_PROTOCOL.md

## Startup transaction — do this before research, code, scanning or paper decisions

1. Actually fetch latest `main` HEAD SHA from connected GitHub (do not assume a stored SHA). Then read this exact `BOOT_PROTOCOL.md` from the same HEAD. If GitHub is not connected or fetch fails, announce `NOT VERIFIED`, state missing access, and **do not silently fall back to remembered text or start a scan/test/trading job**.
2. Read the **current committed versions** of `START_HERE.md`, `MANIFEST.json`, `MASTER.md`, `LESSONS.jsonl`, `SOURCE_REGISTRY.md`, `STUDY_PROGRESS.json`, `CASES.md`, `EXPERIMENTS.md`, `MINIMUM_COMPETENCE_BENCHMARK.md`, and root `ASSISTANT_CHART_DEEP_REVIEW_PROTOCOL.md`. Inspect `AGENTS.md`. Do not replace actual reads with summaries copied from earlier chats.
3. **Consistency check**: all reads must share a single HEAD commit or else reread at one revision. Confirm MANIFEST revision and currentResearchPhase.name=`METHODOLOGY_FIRST_SOURCE_STUDY`; status `productionWriteAllowed=false`, `existingScannerCompleted=true`, `routineBlindTradingAuthorized=false`, `s02Progression=PAUSED_AFTER_D03`. Confirm recorded source locator and next study question. Any conflict => `INCONSISTENT`; stop and report discrepancy rather than choosing a convenient version.
4. **Primary sources**: all 91 original numbered `차트술사` PNGs are in ChatGPT Library `/차트공부_원자료_20260928/images/`; final indexed DOCX `차트공부_CANONICAL_MASTER_FINAL_20260929.docx`. Locate and actually read the relevant originals for the intended study. An inventory check or condensed master is **not** visual comprehension. Source access may be separately `SOURCE_NOT_VERIFIED` if Library is unavailable; do not invent that source's observations. Study the already supplied corpus first; research external alternatives ONLY for real gaps, contradictions or falsification. Five expert plans are comparative examples, not numbers to reverse-engineer. Yangbongman is an optional school, not the controlling doctrine.
5. **Phase lock**: user has existing human expert guidance and a complete full-market scanner; the present goal is a **durable, independent, evidence-tested external chart-analysis methodology** eventually executable by unchanged GPT. Do not create a new screener, perform routine daily/3-day stock picking, advance S02 to D04, initiate another paper portfolio, modify production/Worker/watchlist or send live orders. These require separately explicit instruction, not mere `ㄱㄱ`. Reviewing frozen previous experiments as **case evidence** is permitted; never unlock unrevealed masked future results without user approval.
6. **Non-regression gate**: choose the next unresolved question from `STUDY_PROGRESS.json` and justify why it matters to independent judgement. Before saying skill or methodology improved, demonstrate the updated interpretation on an unfamiliar, cutoff-respecting case and compare to the prior method; document counterarguments, misses, costs, and source provenance. Merely reading, archiving, committing, or generating a plan = **NOT PROVEN**. Carry tested improvements to MASTER/LESSONS/CASES and update progress only when actions actually completed. The progress file is not itself a model upgrade.
7. **First user-facing boot report**: `BOOT PASS | NOT VERIFIED | INCONSISTENT`, current HEAD SHA, learning revision, research phase, source access status, S02 pause, actual next study question, and any genuine limitation. If PASS, begin the next specific *research* action (read real originals, analyze a discrepancy) instead of asking the user to restate project purpose. Do not claim entire 91-image mastery without case-level evidence.

## Drift detection during a long chat

Before each new tool-heavy workstream and especially when the user says `ㄱㄱ`:
- Re-check whether the proposed action **improves the chart methodology** rather than operating a tool for its own sake.
- Compare it to `STUDY_PROGRESS.json` unresolved question and the evidence ladder.
- If it would resume serial scan/backtest/trading without a distinct, explicit scope change: **STOP**, explain why, return to an original-image study/contradiction.
- If the GitHub learning revision moved, reread authoritative changed records before proceeding. If source access disappears, downgrade verification and state limits.

## Progress accounting

`STUDY_PROGRESS.json` tracks **research task state**, not model-weight updates or prediction skill. Source inspection, conceptual comprehension, independent transfer validation, and economic outcome validation are separate fields. Never mark an image `MASTERED` because it was listed or opened. The 2026-10-15 initial progress reflects known source inventory and earlier limited direct image inspection; it does not assert comprehensive 91-image assimilation or independent profitable trading.

## Confirming this protocol actually worked

A repository integrity action verifies that required boot/progress records remain complete and self-consistent; it **cannot launch a fresh ChatGPT session or verify that GPT obeyed**. A real cross-chat trial is needed: paste the message above in a brand new chat, inspect whether current HEAD/version, pause state, and the correct next study are recovered **before** research. Log `PASS` only when that behavior is observed; otherwise log `FAIL`, preserve the counterexample and correct the bootstrap process. No operation beyond research is authorized here.
