import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "analyze_reasoning_tokens.py"
SPEC = importlib.util.spec_from_file_location("analyze_reasoning_tokens", SCRIPT_PATH)
analyzer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["analyze_reasoning_tokens"] = analyzer
SPEC.loader.exec_module(analyzer)


class AnalyzeReasoningTokensTests(unittest.TestCase):
    def test_before_after_and_cluster_summary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            transcript = temp / "rollout-sample.jsonl"
            transcript.write_text(
                "\n".join(
                    json.dumps(item)
                    for item in [
                        {
                            "timestamp": "2026-07-06T14:00:00Z",
                            "type": "session_meta",
                            "payload": {
                                "session_id": "s1",
                                "timestamp": "2026-07-06T14:00:00Z",
                                "cwd": "C:\\repo",
                                "cli_version": "0.test",
                                "model_provider": "openai",
                                "base_instructions": {
                                    "text": "Header\n## Intermediary updates\nBody"
                                },
                            },
                        },
                        {
                            "timestamp": "2026-07-06T14:01:00Z",
                            "type": "turn_context",
                            "payload": {
                                "turn_id": "t1",
                                "cwd": "C:\\repo",
                                "model": "gpt-5.5",
                                "effort": "high",
                            },
                        },
                        {
                            "timestamp": "2026-07-06T14:10:00Z",
                            "type": "event_msg",
                            "payload": {
                                "type": "token_count",
                                "info": {
                                    "last_token_usage": {
                                        "input_tokens": 10,
                                        "cached_input_tokens": 2,
                                        "output_tokens": 20,
                                        "reasoning_output_tokens": 516,
                                        "total_tokens": 30,
                                    },
                                    "total_token_usage": {
                                        "input_tokens": 10,
                                        "output_tokens": 20,
                                        "reasoning_output_tokens": 516,
                                        "total_tokens": 30,
                                    },
                                    "model_context_window": 258400,
                                },
                            },
                        },
                        {
                            "timestamp": "2026-07-06T15:01:00Z",
                            "type": "turn_context",
                            "payload": {
                                "turn_id": "t2",
                                "cwd": "C:\\repo",
                                "model": "gpt-5.5",
                                "effort": "xhigh",
                            },
                        },
                        {
                            "timestamp": "2026-07-06T15:10:00Z",
                            "type": "event_msg",
                            "payload": {
                                "type": "token_count",
                                "info": {
                                    "last_token_usage": {
                                        "input_tokens": 11,
                                        "cached_input_tokens": 3,
                                        "output_tokens": 21,
                                        "reasoning_output_tokens": 600,
                                        "total_tokens": 32,
                                    },
                                    "total_token_usage": {
                                        "input_tokens": 21,
                                        "output_tokens": 41,
                                        "reasoning_output_tokens": 1116,
                                        "total_tokens": 62,
                                    },
                                    "model_context_window": 258400,
                                },
                            },
                        },
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            summary = analyzer.run_analysis(
                input_paths=[transcript],
                out_dir=temp / "out",
                cutoff_utc=analyzer.parse_iso_datetime("2026-07-06T15:00:00Z", require_timezone=True),
                phase_basis="event",
                cluster_values=[516, 1034, 1552],
            )

            self.assertEqual(summary["usage_event_count"], 2)
            by_phase = {
                (item["phase"], item["model"]): item
                for item in summary["summary_by_model_phase"]
            }
            self.assertEqual(by_phase[("before", "gpt-5.5")]["cluster_hits"], 1)
            self.assertEqual(by_phase[("before", "gpt-5.5")]["cluster_516"], 1)
            self.assertEqual(by_phase[("after", "gpt-5.5")]["cluster_hits"], 0)
            self.assertTrue(summary["sessions"][0]["base_instructions_has_intermediary_updates"])
            self.assertTrue((temp / "out" / analyzer.EVENTS_CSV).exists())
            self.assertTrue((temp / "out" / analyzer.SUMMARY_JSON).exists())


if __name__ == "__main__":
    unittest.main()
