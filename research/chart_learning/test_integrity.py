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

    def test_no_research_production_write(self):
        m = gate.load_manifest()
        self.assertFalse(m["productionWriteAllowed"])
        wf = (gate.ROOT / ".github/workflows/chart-learning-integrity.yml").read_text(encoding="utf-8")
        self.assertIn("contents: read", wf)
        self.assertNotIn("schedule:", wf)
        self.assertNotIn("workflow_dispatch", wf.split("jobs:")[1])

if __name__ == "__main__":
    unittest.main()
