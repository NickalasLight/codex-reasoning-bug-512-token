import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "aggregate_blind_review.py"
SPEC = importlib.util.spec_from_file_location("aggregate_blind_review", SCRIPT_PATH)
aggregate = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["aggregate_blind_review"] = aggregate
SPEC.loader.exec_module(aggregate)


class AggregateBlindReviewTests(unittest.TestCase):
    def test_majority_and_phase_summary(self):
        answer_key = {
            "BR001": {"case_id": "BR001", "phase": "before", "reasoning_output_tokens": 516},
            "BR002": {"case_id": "BR002", "phase": "after", "reasoning_output_tokens": 1034},
            "BR003": {"case_id": "BR003", "phase": "after", "reasoning_output_tokens": 516},
        }
        reviews = {
            "R1": {
                "BR001": {
                    "verdict": "yes",
                    "category": "tooling/platform integration mistake or brittle orchestration",
                },
                "BR002": {
                    "verdict": "no",
                    "category": "routine progress/status or completed work",
                },
                "BR003": {
                    "verdict": "probably",
                    "category": "security, compliance, or secret-sensitive work",
                },
            },
            "R2": {
                "BR001": {
                    "verdict": "probably",
                    "category": "tooling/platform integration mistake or brittle orchestration",
                },
                "BR002": {
                    "verdict": "no",
                    "category": "routine progress/status or completed work",
                },
                "BR003": {
                    "verdict": "unclear",
                    "category": "other/unclear",
                },
            },
            "R3": {
                "BR001": {
                    "verdict": "yes",
                    "category": "diagnostic/evidence collection",
                },
                "BR002": {
                    "verdict": "no",
                    "category": "routine progress/status or completed work",
                },
                "BR003": {
                    "verdict": "probably",
                    "category": "security, compliance, or secret-sensitive work",
                },
            },
        }

        summary = aggregate.build_summary(answer_key, reviews)

        self.assertEqual(summary["case_count"], 3)
        self.assertEqual(summary["majority_counts"]["verdict"]["yes"], 1)
        self.assertEqual(summary["majority_counts"]["verdict"]["no"], 1)
        self.assertEqual(summary["majority_counts"]["verdict"]["probably"], 1)
        self.assertEqual(summary["phase_counts"]["before"]["concern"], 1)
        self.assertEqual(summary["phase_counts"]["after"]["concern"], 1)
        self.assertEqual(summary["phase_counts"]["after"]["no_concern"], 1)
        self.assertIn("concern_fleiss_kappa", summary["agreement"])

    def test_load_review_rejects_missing_case(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "review.jsonl"
            path.write_text(
                json.dumps(
                    {
                        "case_id": "BR001",
                        "category": "routine progress/status or completed work",
                        "verdict": "no",
                        "confidence": 4,
                        "rationale_public": "Routine status update.",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                aggregate.load_review_jsonl(path, {"BR001", "BR002"})


if __name__ == "__main__":
    unittest.main()
