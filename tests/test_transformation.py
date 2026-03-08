from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
TRANSFORMATION_DIR = ROOT / "transformation"
if str(TRANSFORMATION_DIR) not in sys.path:
    sys.path.insert(0, str(TRANSFORMATION_DIR))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from fixtures import FIXED_TIMESTAMP, arena_row, code_interpreter_row, prompt_library_row, sharegpt_row
from run_pipeline import transform_dataset_rows


def metadata(dataset_name: str) -> dict[str, str]:
    return {"dataset_name": dataset_name, "collection_method": "fixture", "version": "test"}


class TransformationTests(unittest.TestCase):
    def test_sharegpt_pairs_adjacent_messages_only(self) -> None:
        prompt_records, comparison_records = transform_dataset_rows(
            "sharegpt_conversation_chronicles",
            [sharegpt_row()],
            source_metadata=metadata("sharegpt_conversation_chronicles"),
            run_started_at=FIXED_TIMESTAMP,
        )
        self.assertEqual(len(comparison_records), 0)
        self.assertEqual(len(prompt_records), 2)
        self.assertEqual([record["turn_number"] for record in prompt_records], [1, 2])
        self.assertEqual(prompt_records[0]["response_text"], "Recursion is when a function calls itself.")
        self.assertEqual(prompt_records[1]["task_type"], "explanation")
        self.assertTrue(prompt_records[1]["contains_constraints"])
        self.assertTrue(prompt_records[1]["contains_code"] is False)

    def test_code_interpreter_detects_task_and_language(self) -> None:
        prompt_records, _ = transform_dataset_rows(
            "sharegpt_code_interpreter",
            [code_interpreter_row()],
            source_metadata=metadata("sharegpt_code_interpreter"),
            run_started_at=FIXED_TIMESTAMP,
        )
        self.assertEqual(len(prompt_records), 1)
        self.assertEqual(prompt_records[0]["task_type"], "code_generation")
        self.assertEqual(prompt_records[0]["programming_lang"], "python")
        self.assertTrue(prompt_records[0]["contains_code"])

    def test_chatbot_arena_emits_prompt_and_comparison_records(self) -> None:
        prompt_records, comparison_records = transform_dataset_rows(
            "chatbot_arena",
            [arena_row()],
            source_metadata=metadata("chatbot_arena"),
            run_started_at=FIXED_TIMESTAMP,
        )
        self.assertEqual(len(prompt_records), 2)
        self.assertEqual(len(comparison_records), 1)
        self.assertEqual(prompt_records[0]["quality_label"], "winner")
        self.assertEqual(prompt_records[1]["quality_label"], "loser")
        self.assertEqual(prompt_records[0]["success_score"], 1.0)
        self.assertEqual(prompt_records[1]["success_score"], 0.0)
        self.assertEqual(prompt_records[0]["language"], "en")
        self.assertEqual(comparison_records[0]["model_a"], "vicuna-13b")

    def test_chatbot_arena_handles_tie_and_both_bad(self) -> None:
        tie_payload = arena_row()
        tie_payload["winner"] = "tie"
        tie_prompts, _ = transform_dataset_rows(
            "chatbot_arena",
            [tie_payload],
            source_metadata=metadata("chatbot_arena"),
            run_started_at=FIXED_TIMESTAMP,
        )
        self.assertEqual([record["quality_label"] for record in tie_prompts], ["tie", "tie"])
        self.assertEqual([record["success_score"] for record in tie_prompts], [0.5, 0.5])

        both_bad_payload = arena_row()
        both_bad_payload["winner"] = "tie (bothbad)"
        both_bad_prompts, _ = transform_dataset_rows(
            "chatbot_arena",
            [both_bad_payload],
            source_metadata=metadata("chatbot_arena"),
            run_started_at=FIXED_TIMESTAMP,
        )
        self.assertEqual([record["quality_label"] for record in both_bad_prompts], ["both_bad", "both_bad"])
        self.assertEqual([record["success_score"] for record in both_bad_prompts], [0.0, 0.0])

    def test_prompt_library_maps_prompt_type_and_category(self) -> None:
        prompt_records, comparison_records = transform_dataset_rows(
            "prompt_library",
            [prompt_library_row()],
            source_metadata=metadata("prompt_library"),
            run_started_at=FIXED_TIMESTAMP,
        )
        self.assertEqual(len(comparison_records), 0)
        self.assertEqual(len(prompt_records), 1)
        prompt_record = prompt_records[0]
        self.assertEqual(prompt_record["task_type"], "linux_terminal")
        self.assertEqual(prompt_record["task_category"], "developer")
        self.assertEqual(prompt_record["prompt_type"], "roleplay")
        self.assertTrue(prompt_record["contains_examples"])
        self.assertTrue(prompt_record["contains_constraints"])


if __name__ == "__main__":
    unittest.main()
