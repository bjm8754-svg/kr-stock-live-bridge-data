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

    def test_no_research_production_write(self):
        m = gate.load_manifest()
        self.assertFalse(m["productionWriteAllowed"])
        wf = (gate.ROOT / ".github/workflows/chart-learning-integrity.yml").read_text(encoding="utf-8")
        self.assertIn("contents: read", wf)
        self.assertNotIn("schedule:", wf)
        self.assertNotIn("workflow_dispatch", wf.split("jobs:")[1])

if __name__ == "__main__":
    unittest.main()
