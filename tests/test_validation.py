from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
TRANSFORMATION_DIR = ROOT / "transformation"
VALIDATION_DIR = ROOT / "validation"
TESTS_DIR = Path(__file__).resolve().parent
for candidate in [str(TRANSFORMATION_DIR), str(VALIDATION_DIR), str(TESTS_DIR)]:
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from fixtures import FIXED_TIMESTAMP, arena_row, sharegpt_row
from run_pipeline import transform_dataset_rows
from validation_checks import validate_comparison_record, validate_prompt_record


def metadata(dataset_name: str) -> dict[str, str]:
    return {"dataset_name": dataset_name, "collection_method": "fixture", "version": "test"}


class ValidationTests(unittest.TestCase):
    def test_valid_prompt_record_passes(self) -> None:
        prompt_records, _ = transform_dataset_rows(
            "sharegpt_conversation_chronicles",
            [sharegpt_row()],
            source_metadata=metadata("sharegpt_conversation_chronicles"),
            run_started_at=FIXED_TIMESTAMP,
        )
        self.assertTrue(validate_prompt_record(prompt_records[0]))

    def test_valid_comparison_record_passes(self) -> None:
        _, comparison_records = transform_dataset_rows(
            "chatbot_arena",
            [arena_row()],
            source_metadata=metadata("chatbot_arena"),
            run_started_at=FIXED_TIMESTAMP,
        )
        self.assertTrue(validate_comparison_record(comparison_records[0]))

    def test_invalid_prompt_record_fails(self) -> None:
        prompt_records, _ = transform_dataset_rows(
            "sharegpt_conversation_chronicles",
            [sharegpt_row()],
            source_metadata=metadata("sharegpt_conversation_chronicles"),
            run_started_at=FIXED_TIMESTAMP,
        )
        invalid = dict(prompt_records[0])
        invalid.pop("prompt_hash")
        self.assertFalse(validate_prompt_record(invalid))


if __name__ == "__main__":
    unittest.main()
