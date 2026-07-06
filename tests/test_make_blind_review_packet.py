import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "make_blind_review_packet.py"
SPEC = importlib.util.spec_from_file_location("make_blind_review_packet", SCRIPT_PATH)
packet_maker = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["make_blind_review_packet"] = packet_maker
SPEC.loader.exec_module(packet_maker)


class MakeBlindReviewPacketTests(unittest.TestCase):
    def test_redacts_and_blinds_phase(self):
        rows = [
            {
                "sample_id": "A002",
                "phase": "after",
                "model": "gpt-5.5",
                "event_timestamp_utc": "2026-07-06T14:00:00Z",
                "reasoning_output_tokens": 1034,
                "category": "security, compliance, or secret-sensitive work",
                "verdict": "probably",
                "tools": ["shell_command"],
                "recent_user_private": "Use C:\\Users\\NickL\\repo and token=abc123.",
                "recent_assistant_private": "Contact Nickalas at test@example.com",
                "recent_tool_output_private": "secret=shh",
                "transcript_hash": "hash-2",
            },
            {
                "sample_id": "A001",
                "phase": "before",
                "model": "gpt-5.5",
                "event_timestamp_utc": "2026-07-06T13:00:00Z",
                "reasoning_output_tokens": 516,
                "category": "routine progress/status or completed work",
                "verdict": "no",
                "tools": [],
                "recent_user_private": "Status?",
                "recent_assistant_private": "Done.",
                "recent_tool_output_private": "",
                "transcript_hash": "hash-1",
            },
        ]

        packet, answer_key = packet_maker.build_packet(rows, seed="unit", max_chars=200)

        self.assertEqual(len(packet), 2)
        self.assertEqual(len(answer_key), 2)
        self.assertEqual({row["case_id"] for row in packet}, {"BR001", "BR002"})
        self.assertNotIn("phase", packet[0])
        serialized = json.dumps(packet)
        self.assertNotIn("NickL", serialized)
        self.assertNotIn("Nickalas", serialized)
        self.assertNotIn("test@example.com", serialized)
        self.assertNotIn("abc123", serialized)
        self.assertIn("[USER_HOME]", serialized)
        self.assertIn("[EMAIL]", serialized)
        self.assertIn("[REDACTED]", serialized)

    def test_cli_writes_expected_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            input_path = temp / "private.json"
            out_dir = temp / "out"
            input_path.write_text(
                json.dumps(
                    [
                        {
                            "sample_id": "A001",
                            "phase": "before",
                            "reasoning_output_tokens": 516,
                            "recent_user_private": "hello",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            # Exercise lower-level file writers instead of mutating sys.argv in this unit test.
            out_dir.mkdir()
            packet, answer_key = packet_maker.build_packet(packet_maker.load_rows(input_path), "unit", 900)
            packet_maker.write_jsonl(packet, out_dir / "blind-review-packet.jsonl")
            (out_dir / "blind-review-answer-key-private.json").write_text(json.dumps(answer_key), encoding="utf-8")
            packet_maker.write_rubric(out_dir / "blind-review-rubric.md")

            self.assertTrue((out_dir / "blind-review-packet.jsonl").exists())
            self.assertTrue((out_dir / "blind-review-answer-key-private.json").exists())
            self.assertTrue((out_dir / "blind-review-rubric.md").exists())


if __name__ == "__main__":
    unittest.main()
