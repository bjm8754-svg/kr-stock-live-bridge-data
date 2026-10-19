#!/usr/bin/env python3
"""Small offline smoke tests for memory integrity."""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import validate as gate

class IntegrityTest(unittest.TestCase):
    def test_repository_gate(self):
        m, lessons = gate.validate()
        self.assertGreaterEqual(m["revision"], 1)
        self.assertEqual(len(lessons), m["lessonCount"])

    def test_readme_and_agent_start_here(self):
        for filename in ("README.md", "AGENTS.md", "ASSISTANT_CHART_DEEP_REVIEW_PROTOCOL.md"):
            content = (gate.ROOT / filename).read_text(encoding="utf-8")
            self.assertIn("research/chart_learning/START_HERE.md", content)

    def test_original_sources_are_registered_not_falsely_verified(self):
        m = gate.load_manifest()
        self.assertEqual(m["externalSourceInventory"]["chartStudyOriginalImages"]["expectedCount"], 91)
        self.assertEqual(m["externalSourceInventory"]["yangbongmanText"]["originalPictureCompleteness"], "UNVERIFIED")
        self.assertIn("YBM_METHOD_AUDIT.md", (gate.BASE / "SOURCE_REGISTRY.md").read_text(encoding="utf-8"))

    def test_no_privileged_teacher(self):
        master = (gate.BASE / "MASTER.md").read_text(encoding="utf-8")
        manifest = gate.load_manifest()
        self.assertIn("### R-010 — Analytical pluralism", master)
        self.assertIn({"id": "R-010", "status": "CANONICAL"}, manifest["rules"])
        self.assertIn("Yangbongman (YBM) is ONE VIEW among many", master)

    def test_minimum_expert_competence_requires_independent_proof(self):
        m = gate.load_manifest()
        self.assertEqual(m["minimumCompetence"]["acceptanceStatus"], "NOT_DEMONSTRATED")
        self.assertEqual(m["minimumCompetence"]["expertRealizedPerformance"], "UNKNOWN")
        benchmark = (gate.BASE / "MINIMUM_COMPETENCE_BENCHMARK.md").read_text(encoding="utf-8")
        for i in range(1, 8):
            self.assertIn(f"M-{i:02d}", benchmark)
        self.assertIn("independent", benchmark.lower())
        self.assertIn("Yangbongman is **one view among many**", benchmark)

    def test_swing_horizon_not_equal_review_cadence(self):
        m = gate.load_manifest()
        master = (gate.BASE / "MASTER.md").read_text(encoding="utf-8")
        self.assertIn({"id": "R-011", "status": "CANONICAL"}, m["rules"])
        self.assertIn("3-trading-day decision/review cadence", master)
        self.assertIn("right-censored", master)
        self.assertIn("L-010", (gate.BASE / "LESSONS.jsonl").read_text(encoding="utf-8"))
        self.assertIn("30-session episode", master)

    def test_legacy_hold_drift_known_and_not_claimed_fixed(self):
        m = gate.load_manifest()
        master = (gate.BASE / "MASTER.md").read_text(encoding="utf-8")
        self.assertEqual(m["knownExecutionLimitation"]["status"], "UNFIXED_IN_EXISTING_S01")
        self.assertIn({"id": "R-012", "status": "CANONICAL"}, m["rules"])
        self.assertIn("HOLD", master)
        self.assertIn("L-011", (gate.BASE / "LESSONS.jsonl").read_text(encoding="utf-8"))
        self.assertIn("ORDER_SEMANTICS_V2.md", master)

    def test_future_data_leak_quarantines_s01(self):
        m = gate.load_manifest()
        self.assertEqual(m["knownTemporalLeak"]["status"], "QUARANTINED")
        self.assertFalse(m["knownTemporalLeak"]["cleanPerformanceVerified"])
        self.assertIn({"id": "R-013", "status": "CANONICAL"}, m["rules"])
        cases = (gate.BASE / "CASES.md").read_text(encoding="utf-8")
        self.assertIn("18,810", cases)
        self.assertIn("19,000", cases)

    def test_patient_limit_swings_replace_forced_open_buys(self):
        m = gate.load_manifest()
        self.assertIn({"id": "R-014", "status": "CANONICAL"}, m["rules"])
        self.assertEqual(m["swingBuyExecution"]["buyType"], "RESTING_BUY_LIMIT")
        self.assertFalse(m["swingBuyExecution"]["defaultNextOpenMarketBuy"])
        self.assertIn("L-013", (gate.BASE / "LESSONS.jsonl").read_text(encoding="utf-8"))

    def test_goal_cannot_be_redefined_as_a_validation_tool(self):
        m = gate.load_manifest()
        self.assertIn({"id": "R-015", "status": "CANONICAL"}, m["rules"])
        self.assertEqual(m["finalObjective"]["goalType"], "DEVELOP_INDEPENDENT_PROFIT_SEEKING_AI_TRADER_THEN_AUTOMATE")
        self.assertEqual(m["finalObjective"]["validationRole"], "INTERMEDIATE_TRAINING_AND_EVALUATION_NOT_END_GOAL")
        self.assertFalse(m["finalObjective"]["competenceAchieved"])
        self.assertIn("L-014", (gate.BASE / "LESSONS.jsonl").read_text(encoding="utf-8"))
        self.assertIn("C-009", (gate.BASE / "CASES.md").read_text(encoding="utf-8"))
        self.assertIn("R-015", (gate.BASE / "START_HERE.md").read_text(encoding="utf-8"))

    def test_methodology_first_priorities_survive_new_chat(self):
        m = gate.load_manifest()
        phase = m["currentResearchPhase"]
        self.assertEqual(phase["name"], "METHODOLOGY_FIRST_SOURCE_STUDY")
        self.assertTrue(phase["existingScannerCompleted"])
        self.assertFalse(phase["routineBlindTradingAuthorized"])
        self.assertEqual(phase["s02Progression"], "PAUSED_AFTER_D03")
        self.assertEqual(phase["primaryCorpus"], "91_CHAT_SAGE_ORIGINAL_PNG")
        self.assertFalse(phase["methodologyCompetenceVerified"])
        self.assertIn({"id": "R-016", "status": "CANONICAL"}, m["rules"])
        self.assertIn("L-015", (gate.BASE / "LESSONS.jsonl").read_text(encoding="utf-8"))
        self.assertIn("91-photo PRIMARY STUDY CORPUS", (gate.BASE / "START_HERE.md").read_text(encoding="utf-8"))

    def test_fresh_chat_boot_is_persisted_but_not_falsely_claimed(self):
        m = gate.load_manifest()
        boot = m["bootProtocol"]
        self.assertEqual(boot["activation"], "USER_PASTED_SELF_CONTAINED_MESSAGE")
        self.assertFalse(boot["realFreshChatTrialVerified"])
        self.assertIn({"id": "R-017", "status": "CANONICAL"}, m["rules"])
        boot_message = (gate.BASE / "BOOT_PROTOCOL.md").read_text(encoding="utf-8")
        self.assertIn("차트연구 부팅", boot_message)
        self.assertIn("NOT VERIFIED", boot_message)
        self.assertIn("STUDY_PROGRESS.json", boot_message)
        pr = json.loads((gate.BASE / "STUDY_PROGRESS.json").read_text(encoding="utf-8"))
        self.assertEqual(pr["researchPhase"], m["currentResearchPhase"]["name"])
        self.assertEqual(pr["s02"]["progression"], "PAUSED_AFTER_D03")
        self.assertFalse(pr["learningStatus"]["unseenChartTransferDemonstrated"])
        self.assertFalse(pr["learningStatus"]["economicEdgeVerified"])

    def test_video_source_study_preserves_attribution_and_limitations(self):
        m = gate.load_manifest()
        self.assertEqual(m["supplementalVideoSourceRegistry"], "research/chart_learning/VIDEO_STUDIES.md")
        v = (gate.BASE / "VIDEO_STUDIES.md").read_text(encoding="utf-8")
        self.assertIn("JSYuRdYKo2M", v)
        self.assertIn("RETURN UNVERIFIED", v)
        progress = json.loads((gate.BASE / "STUDY_PROGRESS.json").read_text(encoding="utf-8"))
        self.assertFalse(progress["learningStatus"]["unseenChartTransferDemonstrated"])
        self.assertEqual(progress["supplementaryVideoStudies"][0]["newCanonicalRulesPromoted"], 0)
        self.assertEqual(progress["s02"]["progression"], "PAUSED_AFTER_D03")

    def test_user_uploaded_lectures_are_not_mistaken_for_watched_videos(self):
        manifest = gate.load_manifest()
        self.assertEqual(manifest["userLectureResearchLedger"], "research/chart_learning/USER_SOURCE_STUDIES.md")
        source = (gate.BASE / "USER_SOURCE_STUDIES.md").read_text(encoding="utf-8")
        self.assertIn("U-001", source)
        self.assertIn("U-002", source)
        self.assertIn("M_box", source)
        self.assertIn("C_adjust", source)
        progress = json.loads((gate.BASE / "STUDY_PROGRESS.json").read_text(encoding="utf-8"))
        self.assertEqual(progress["learningStatus"]["methodologyVersion"], manifest["revision"])
        self.assertFalse(progress["learningStatus"]["unseenChartTransferDemonstrated"])
        self.assertFalse(progress["learningStatus"]["economicEdgeVerified"])
        for item in progress["userUploadedStudies"]:
            self.assertFalse(item["fullVisualVerification"])

    def test_recovered_root_screenshots_are_cataloged_without_overclaiming(self):
        m = gate.load_manifest()
        self.assertEqual(m["recoveredScreenshotLedger"], "research/chart_learning/RECOVERED_SCREENSHOT_CATALOG.md")
        catalog = (gate.BASE / "RECOVERED_SCREENSHOT_CATALOG.md").read_text(encoding="utf-8")
        for x in ("B-001", "1000059344.jpg", "1000059380.png", "KakaoTalkChats.txt", "144058", "35", "EXPIRED ORIGINAL PREVIEW"):
            self.assertIn(x, catalog)
        p = json.loads((gate.BASE / "STUDY_PROGRESS.json").read_text(encoding="utf-8"))
        batches = p["sourceRecovery"]["completedBatches"]
        self.assertEqual([(b["id"], b["rootImageEntriesDirectlyOpened"]) for b in batches], [("B-001", 35), ("B-002", 3), ("B-003", 4)])
        self.assertIn("B-002", catalog)
        self.assertIn("B-003", catalog)
        self.assertIn("1000059374.jpg", catalog)
        self.assertIn("EXPIRED", catalog)
        latest = p["sourceRecovery"]["latestManuallyInspectedBatch"]
        self.assertEqual(latest["id"], "B-003")
        self.assertEqual(latest["rootImageEntriesDirectlyOpened"], 4)
        self.assertEqual(latest["distinctVisualSources"], 3)
        self.assertFalse(latest["originalImageRecoveryComplete"])
        self.assertFalse(latest["duplicateHashVerified"])
        self.assertEqual(p["sourceRecovery"]["reviewedRootImageEntriesAcrossLoggedBatches"], 42)
        self.assertFalse(p["learningStatus"]["economicEdgeVerified"])

    def test_bulk_source_triage_overrides_microbatch_stopping(self):
        m = gate.load_manifest()
        p = json.loads((gate.BASE / "STUDY_PROGRESS.json").read_text(encoding="utf-8"))
        sr = p["sourceRecovery"]
        self.assertEqual(m["revision"], p["learningStatus"]["methodologyVersion"])
        self.assertGreaterEqual(sr["metadataInventory"]["rootEntries"], 1616)
        self.assertFalse(sr["metadataInventory"]["rootContentClassifiedComplete"])
        self.assertEqual(sr["metadataInventory"]["pages"], 9)
        self.assertGreaterEqual(sr["totalRootImagesActuallyOpenedAllLoggedWork"], 57)
        self.assertEqual(sr["bulkStudies"][0]["actualRootImagesOpened"], 15)
        self.assertEqual(sr["bulkStudies"][0]["sourceGroups"], 4)
        self.assertEqual(sr["inspectPolicy"]["old3to5BatchStopGate"], "SUPERSEDED")
        self.assertIn("BULK-META-001", (gate.BASE / "RECOVERED_SCREENSHOT_CATALOG.md").read_text(encoding="utf-8"))
        self.assertFalse(p["learningStatus"]["unseenChartTransferDemonstrated"])
        self.assertEqual(p["s02"]["progression"], "PAUSED_AFTER_D03")

    def test_bulk002_actual_source_trace_and_no_trade_promotion(self):
        p = json.loads((gate.BASE / "STUDY_PROGRESS.json").read_text(encoding="utf-8"))
        m = gate.load_manifest()
        root = p["sourceRecovery"]
        self.assertEqual(m["revision"], p["learningStatus"]["methodologyVersion"])
        self.assertGreaterEqual(root["totalRootImagesActuallyOpenedAllLoggedWork"], 102)
        self.assertEqual(root["bulkStudies"][0]["actualRootImagesOpened"], 15)
        self.assertEqual(root["bulkStudies"][1]["actualRootImagesOpened"], 45)
        self.assertEqual(root["bulkStudies"][1]["marketBeforeAfterPairs"], 5)
        self.assertEqual(root["bulkStudies"][1]["actualExpertTradeOutcomesVerified"], 0)
        self.assertEqual(len(root["bulkStudies"][1]["rootFilnameInventory"]["september23"]), 20)
        self.assertEqual(len(root["bulkStudies"][1]["rootFilnameInventory"]["september28"]), 25)
        self.assertFalse(root["metadataInventory"]["rootContentClassifiedComplete"])
        self.assertEqual(len(p["primarySource"]["directlyOpenedOriginalNumbers"]), 21)
        self.assertFalse(p["learningStatus"]["unseenChartTransferDemonstrated"])
        self.assertFalse(p["learningStatus"]["economicEdgeVerified"])
        self.assertEqual(p["s02"]["progression"], "PAUSED_AFTER_D03")
        ledger = (gate.BASE / "ROOT_IMAGE_STUDIES_BULK002.md").read_text(encoding="utf-8")
        for word in ("1000059241.jpg", "1000059615.jpg", "20260928-143436", "KakaoTalkChats.txt", "NOT VERIFIED"):
            self.assertIn(word, ledger)

    def test_three_closed_root_date_cohorts_and_evidence_limits(self):
        m = gate.load_manifest()
        p = json.loads((gate.BASE / "STUDY_PROGRESS.json").read_text(encoding="utf-8"))
        sr = p["sourceRecovery"]
        self.assertEqual(m["revision"], p["learningStatus"]["methodologyVersion"])
        self.assertEqual([x["allRootEntries"] for x in sr["dateCohortCoverage"][:3]], [65, 98, 39])
        self.assertGreaterEqual(sr["rootEntriesWithinFullyClassifiedCohorts"], 202)
        self.assertTrue(sr["totalRootCountIsConservativeLowerBound"])
        self.assertFalse(sr["deduplicatedAcrossAllHistoricalBatchesVerified"])
        self.assertEqual(sr["bulkStudies"][2]["id"], "BULK-003")
        self.assertEqual(sr["bulkStudies"][3]["id"], "BULK-004")
        self.assertEqual(sr["bulkStudies"][3]["actualRootImagesOpened"], 73)
        self.assertEqual(sr["bulkStudies"][3]["linkedTeachingGraphics"], 69)
        self.assertEqual(len(p["primarySource"]["directlyOpenedOriginalNumbers"]), 21)
        self.assertEqual(p["primarySource"]["imagesIndependentlyMasteredCount"], 0)
        self.assertFalse(p["learningStatus"]["unseenChartTransferDemonstrated"])
        self.assertFalse(p["learningStatus"]["economicEdgeVerified"])
        self.assertFalse(m["productionWriteAllowed"])
        self.assertEqual(p["s02"]["progression"], "PAUSED_AFTER_D03")

    def test_bulk005_preserves_partial_vs_complete_source_evidence(self):
        m = gate.load_manifest()
        p = json.loads((gate.BASE / "STUDY_PROGRESS.json").read_text(encoding="utf-8"))
        sr = p["sourceRecovery"]
        self.assertEqual(m["revision"], p["learningStatus"]["methodologyVersion"])
        self.assertGreaterEqual(sr["rootEntriesWithinFullyClassifiedCohorts"], 230)
        self.assertEqual([x["allRootEntries"] for x in sr["dateCohortCoverage"][:7]], [65,98,39,16,3,4,5])
        self.assertEqual(sr["bulkStudies"][4]["visuallyOpenedInPartialCohortSamples"], 38)
        self.assertEqual(sr["bulkStudies"][4]["totalImagesActuallyReadThisSession"], 66)
        self.assertGreaterEqual(sr["bulkStudies"][4]["totalImagesActuallyReadThisSession"], 66)
        self.assertFalse(sr["deduplicatedAcrossAllHistoricalBatchesVerified"])
        self.assertEqual(len(p["primarySource"]["directlyOpenedOriginalNumbers"]), 21)
        self.assertEqual(p["primarySource"]["imagesIndependentlyMasteredCount"], 0)
        self.assertFalse(p["learningStatus"]["economicEdgeVerified"])
        self.assertFalse(p["learningStatus"]["unseenChartTransferDemonstrated"])
        self.assertEqual(p["s02"]["progression"], "PAUSED_AFTER_D03")
        self.assertFalse(m["productionWriteAllowed"])

    def test_bulk006_root_group_accounting(self):
        m = gate.load_manifest()
        p = json.loads((gate.BASE / "STUDY_PROGRESS.json").read_text(encoding="utf-8"))
        r = p["sourceRecovery"]
        self.assertGreaterEqual(m["revision"], 28)
        self.assertGreaterEqual(p["learningStatus"]["methodologyVersion"], 28)
        self.assertGreaterEqual(r["completedCohortDateCount"], 9)
        self.assertGreaterEqual(r["rootEntriesWithinFullyClassifiedCohorts"], 379)
        self.assertEqual(r["bulkStudies"][4]["visuallyOpenedInPartialCohortSamples"], 38)
        self.assertGreaterEqual(r["totalRootImagesActuallyOpenedAllLoggedWork"], 384)
        self.assertEqual([x["allRootEntries"] for x in r["dateCohortCoverage"][7:9]], [111,38])
        self.assertGreaterEqual(len(r["partialDateCohortSamples"]), 1)
        self.assertEqual(r["bulkStudies"][5]["additionalActualReadsThisTurn"], 116)
        self.assertEqual(p["primarySource"]["imagesIndependentlyMasteredCount"], 0)
        self.assertEqual(p["s02"]["progression"], "PAUSED_AFTER_D03")
        self.assertFalse(m["productionWriteAllowed"])

    def test_bulk007_image_backing_failures_are_not_counted_as_study(self):
        m = gate.load_manifest()
        p = json.loads((gate.BASE / "STUDY_PROGRESS.json").read_text(encoding="utf-8"))
        r = p["sourceRecovery"]
        self.assertGreaterEqual(m["revision"], 29)
        self.assertGreaterEqual(p["learningStatus"]["methodologyVersion"], 29)
        self.assertGreaterEqual(r["metadataInventory"]["rootEntries"], 1623)
        self.assertEqual(r["metadataInventory"]["previousRootEntries"], 1623)
        self.assertGreaterEqual(r["completedCohortDateCount"], 11)
        self.assertGreaterEqual(r["rootEntriesWithinFullyClassifiedCohorts"], 508)
        self.assertEqual([x["visuallyOpened"] for x in r["partialDateCohortSamples"]], [72,103])
        self.assertGreaterEqual(r["totalRootImagesActuallyOpenedAllLoggedWork"], 688)
        self.assertGreaterEqual(r["rootEntriesAssignedVisualOrAccessOutcome"], 696)
        self.assertEqual(r["rootEntryAccessFailedCount"], 8)
        self.assertEqual(r["rootImageCountUnaccountedForInCurrentInventory"], r["metadataInventory"]["rootEntries"] - r["rootEntriesAssignedVisualOrAccessOutcome"])
        self.assertEqual([x["allRootEntries"] for x in r["dateCohortCoverage"][9:11]], [83,46])
        self.assertEqual(r["bulkStudies"][6]["rootEntriesSourceMetadataAudited"], 312)
        self.assertEqual(r["bulkStudies"][6]["actualNativeImagesRendered"], 304)
        self.assertEqual(r["bulkStudies"][6]["rootContentInaccessible"], 8)
        self.assertEqual([x["visuallyOpened"] for x in r["partialDateCohortSamples"]], [72,103])
        self.assertFalse(r["metadataInventory"]["rootContentClassifiedComplete"])
        self.assertEqual(len(p["primarySource"]["directlyOpenedOriginalNumbers"]), 21)
        self.assertEqual(p["primarySource"]["imagesIndependentlyMasteredCount"], 0)
        self.assertFalse(p["learningStatus"]["unseenChartTransferDemonstrated"])
        self.assertFalse(p["learningStatus"]["economicEdgeVerified"])
        self.assertEqual(p["s02"]["progression"], "PAUSED_AFTER_D03")
        self.assertFalse(m["productionWriteAllowed"])

    def test_bulk008_october14_closed_while_inaccessible_sources_preserved(self):
        p = json.loads((gate.BASE / "STUDY_PROGRESS.json").read_text(encoding="utf-8"))
        m = gate.load_manifest()
        sr = p["sourceRecovery"]
        self.assertEqual(m["revision"], p["learningStatus"]["methodologyVersion"])
        self.assertGreaterEqual(m["revision"], 30)
        self.assertGreaterEqual(sr["rootEntriesWithinFullyClassifiedCohorts"], 560)
        self.assertEqual(sr["dateCohortCoverage"][11]["uploadDate"], "2026-10-14")
        self.assertEqual(sr["dateCohortCoverage"][11]["newVisualRead"], 47)
        self.assertEqual(sr["dateCohortCoverage"][11]["actualTradingChartFiles"], 0)
        self.assertEqual(len(sr["partialDateCohortSamples"]), 2)
        self.assertEqual(p["s02"]["progression"], "PAUSED_AFTER_D03")
        self.assertFalse(m["productionWriteAllowed"])

    def test_bulk009_native_tiff_recovery_and_cumulative_correction(self):
        m = gate.load_manifest()
        p = json.loads((gate.BASE / "STUDY_PROGRESS.json").read_text(encoding="utf-8"))
        s = p["sourceRecovery"]
        self.assertEqual(m["revision"], 31)
        self.assertEqual(p["learningStatus"]["methodologyVersion"], 31)
        self.assertEqual(s["metadataInventory"]["rootEntries"], 1639)
        self.assertEqual(s["metadataInventory"]["entriesAddedSincePreviousSnapshot"], 16)
        self.assertEqual(s["completedCohortDateCount"], 21)
        self.assertEqual([x["allRootEntries"] for x in s["dateCohortCoverage"][-9:]], [30,12,6,2,13,2,8,10,33])
        self.assertEqual(s["rootEntriesWithinFullyClassifiedCohorts"], 676)
        self.assertEqual(s["totalRootImagesActuallyOpenedAllLoggedWork"], 851)
        self.assertEqual(sum(x["visuallyOpened"] for x in s["partialDateCohortSamples"]), 175)
        self.assertEqual(s["rootEntryAccessFailedCount"], 8)
        self.assertEqual(s["rootEntriesAssignedVisualOrAccessOutcome"], 859)
        self.assertEqual(s["rootImageCountUnaccountedForInCurrentInventory"], 780)
        self.assertEqual(851 + 8 + 780, 1639)
        self.assertEqual(s["bulkStudies"][-1]["rootFilesTiffConvertedFromRawBytes"], 16)
        self.assertEqual(s["bulkStudies"][-1]["newDirectlyOpenedImages"], 116)
        self.assertFalse(s["metadataInventory"]["rootContentClassifiedComplete"])
        self.assertFalse(s["deduplicatedAcrossAllHistoricalBatchesVerified"])
        self.assertEqual(len(p["primarySource"]["directlyOpenedOriginalNumbers"]), 21)
        self.assertEqual(p["primarySource"]["imagesIndependentlyMasteredCount"], 0)
        self.assertFalse(p["learningStatus"]["unseenChartTransferDemonstrated"])
        self.assertFalse(p["learningStatus"]["economicEdgeVerified"])
        self.assertEqual(p["s02"]["progression"], "PAUSED_AFTER_D03")
        self.assertFalse(m["productionWriteAllowed"])
        self.assertIn("## BULK-009", (gate.BASE / "RECOVERED_SCREENSHOT_CATALOG.md").read_text(encoding="utf-8"))

    def test_no_research_production_write(self):
        m = gate.load_manifest()
        self.assertFalse(m["productionWriteAllowed"])
        wf = (gate.ROOT / ".github/workflows/chart-learning-integrity.yml").read_text(encoding="utf-8")
        self.assertIn("contents: read", wf)
        self.assertNotIn("schedule:", wf)
        self.assertNotIn("workflow_dispatch", wf.split("jobs:")[1])

if __name__ == "__main__":
    unittest.main()
