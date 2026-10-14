# START HERE — V3 chart learning continuity gate

**Status:** ACTIVE RESEARCH CONTINUITY CONTRACT
**Learning revision:** 11
**Established:** 2026-10-14 (KST)
**Repository:** bjm8754-svg/kr-stock-live-bridge-data

## Why this exists

The user has repeatedly taught the assistant advanced chart judgement, yet a changed or truncated chat can cause a return to weak, previously corrected behaviour. Creating a document is not learning; **loading it, applying it, testing it on unseen evidence, and recording improvement** are required.

## Non-negotiable mission (R-015 / L-014)

**Independent AI trader → verified economic judgement → user-approved profit-oriented automation.** V3 exists to develop the assistant's independent whole-market discovery, chart reasoning, executable swing trade construction and position management to expert-or-better quality, and ultimately use proven, sustainable risk-adjusted economic judgement in user-approved automation. Research tools, code, GitHub commits, S02 walk-forward testing and SHADOW measurements are **instruments**, never the final product. Explicitly recover this mission BEFORE characterizing V3 or proposing system changes. A new-chat answer which recasts V3's goal as simply validating chart plans is a regression, even if the latest GitHub files happen to be correct. Verify this preflight is actually performed; documents do not self-execute.

## Mandatory new-session opening — ordered

1. Read the current default-branch GitHub files: this file, MANIFEST.json, MASTER.md, MINIMUM_COMPETENCE_BENCHMARK.md, LESSONS.jsonl, SOURCE_REGISTRY.md, EXPERIMENTS.md, CASES.md, and ASSISTANT_CHART_DEEP_REVIEW_PROTOCOL.md. For important historical claims, open the linked original file/data.
2. Report: **learning revision**, **repository HEAD SHA actually fetched**, **latest validated experiment**, **outstanding known failure**, and whether the gate PASSED or is NOT VERIFIED.
3. **Do not privilege Yangbongman or any other named methodology:** each is one perspective, selected only when evidence supports its usefulness for this setup. Begin with independent price, participation, structure and regime analysis; document conflicts. Before accepting a machine EXECUTABLE label, consult all relevant CANONICAL rules and known failures. Distinguish candidate, conditionally executable plan, actually filled trade, simulation, and verified financial result.
4. Any new analysis has a cutoff, source provenance, candidate-selection procedure, precommitted entry/add/stop/target and invalidation, **thesis-dependent holding horizon distinct from review cadence**, outcome stage, and limitations. Do not treat a 3-session S01 review as a 3-session trade expiration. Never blend ex-ante and hindsight data. Never blend ex-ante and hindsight data.
5. On new insight: log an evidence-backed lesson (append only), update experiment record, then propose or amend a MASTER rule and CHANGELOG with an incremented MANIFEST revision. Do not silently replace old knowledge.
6. Verify the changed records using the lightweight research validator; if a verification is unrun/fails, say so. No production write by implication.

**Hard stop:** if first-read GitHub access fails, explain that continuity was not verified. You may answer general questions, but you may not claim to be using the full prior V3 research or quietly fill gaps from memory.

## Files and responsibility

| Artifact | Purpose |
| --- | --- |
| MANIFEST.json | Current learning revision, required paths and rule registry |
| SOURCE_REGISTRY.md | **Original image study (91 PNG), canonical DOCX, Yangbongman KakaoTalk text and YBM audit source locator** |
| MASTER.md | Canonical judgements vs tentative hypotheses; what carries forward |
| MINIMUM_COMPETENCE_BENCHMARK.md | User's **minimum standard**: the five-plan expert's judgement quality, independently proven; not an algorithm to copy |
| LESSONS.jsonl | Append-only, structured error/correction evidence |
| CASES.md | Detailed counterexamples with source links |
| EXPERIMENTS.md | Honest study outcomes, selection bias, what remains untested |
| CHANGELOG.md | Why the learning standard changed |
| RESEARCH_PROTOCOL.md | Rules for clean tests, rule promotion and non-regression |
| validate.py | Static correctness and append-only checks |
| AGENTS.md (root) | Discovered by repo-aware tools/agents; instructs the first read |
| ASSISTANT_CHART_DEEP_REVIEW_PROTOCOL.md (root) | Pre-existing chart judgement protocol |

## Source-of-truth recovery is mandatory

**Never assume the short GitHub MASTER includes all earlier picture-based study.** Read SOURCE_REGISTRY.md first. The 91/91 image archive and original DOCX were separately verified in ChatGPT Library on 2026-10-14; the Yangbongman chat text and GitHub method audits exist, but every referenced original YBM screenshot is **not verified as archived**. Source access in the next chat must be verified anew. Do not claim an all-source continuous education if the original sources were not inspected where needed.

## Immediate research state (2026-10-14)

- **User-required swing entry semantics (L-013 / R-014)**: assistant must independently decide entry/optional second-buy prices, then REST a limit buy and wait; no automatic next-open buying, no interpreting non-fills as positions. Original S02 had no locked trade when corrected. The executable reservation contract is in `research/stock_blind/PROTOCOL_V2.md`, validated offline by `test_reservation_engine.py`. A 3-day review must not cancel reserved bids by default. **No completed market-performance evidence yet.**

- **Critical look-ahead discovery (L-012 / C-007)**: S01 state at D05 held closes A91=18,810 and A0E=86,100 while the newly published D05 `current_card.json` included A91=19,000 and A0E=86,800, plus one extra index day. The provider may return end+1 bars; scanner did not trim at cutoff. **S01 is contaminated, not clean blind.** Do not use its D05 card for another supposedly blind decision. S02 clean engine is separate and must pass point-in-time guards.
- Critical S01 execution-semantic issue (L-011): the legacy 3-session simulator **automatically rebalances every selected position to a target weight even when action=HOLD**. Its results therefore do NOT cleanly establish unchanged-share multi-week swing holding. Keep existing S01 immutable and study the isolated strict-HOLD v2 spec/prototype before any new episode.
- Machine V3 can compress a market universe, but execution references can be unrealistic (e.g., non-tick prices and structurally tiny stops).
- The expert's five plans are a **quality benchmark**; their levels are not algorithms to clone, and suggested buys are not historical executions.
- The 2026-09-18 replay of **33 candidates selected on 2026-10-13** was a hindsight-contaminated, restricted-universe diagnostic, **not a clean 2,590-stock point-in-time test**. It screened six; three provisional plans were described; one (HVM) reached targets when filled, two were unfilled. This does **not** establish predictive edge.
- The next genuine test must freeze a whole-market historical universe and all candidate decisions before opening future prices, then include non-fills, stops, risk, costs and benchmark.

## Resources / safety boundaries

These are lightweight Markdown/JSONL documents, not full market price dumps. Integrity workflow runs **only on updates to the learning documentation or manual dispatch**, with no cron, live-quote request or production write. Scheduled market-scanner workflows are separate and untouched.

The repository can preserve evidence; it does **not** make ChatGPT weights learn, ensure automatic GitHub access by a fresh chat, or guarantee non-regression without applying the gate. Report missing checks clearly.
