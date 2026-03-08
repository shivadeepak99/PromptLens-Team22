from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
TRANSFORMATION_DIR = ROOT / "transformation"
WAREHOUSE_DIR = ROOT / "warehouse"
TESTS_DIR = Path(__file__).resolve().parent
for candidate in [str(TRANSFORMATION_DIR), str(WAREHOUSE_DIR), str(TESTS_DIR)]:
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from fixtures import FIXED_TIMESTAMP, arena_row, code_interpreter_row, prompt_library_row, sharegpt_row
from run_pipeline import transform_dataset_rows
from load_to_postgres import stage_records


def metadata(dataset_name: str) -> dict[str, str]:
    return {"dataset_name": dataset_name, "collection_method": "fixture", "version": "test"}


class WarehouseLoaderTests(unittest.TestCase):
    def test_stage_records_deduplicates_dimensions(self) -> None:
        prompt_records: list[dict] = []
        comparison_records: list[dict] = []
        for dataset_name, row in [
            ("sharegpt_conversation_chronicles", sharegpt_row()),
            ("sharegpt_code_interpreter", code_interpreter_row()),
            ("chatbot_arena", arena_row()),
            ("prompt_library", prompt_library_row()),
        ]:
            prompts, comparisons = transform_dataset_rows(
                dataset_name,
                [row],
                source_metadata=metadata(dataset_name),
                run_started_at=FIXED_TIMESTAMP,
            )
            prompt_records.extend(prompts)
            comparison_records.extend(comparisons)

        staged = stage_records(prompt_records, comparison_records)
        self.assertEqual(len(staged.prompt_facts), 6)
        self.assertEqual(len(staged.comparison_facts), 1)
        self.assertEqual(len(staged.sources), 4)
        self.assertEqual(len(staged.sessions), 4)
        self.assertGreaterEqual(len(staged.prompts), 4)
        self.assertEqual(len(staged.models), 2)


if __name__ == "__main__":
    unittest.main()
