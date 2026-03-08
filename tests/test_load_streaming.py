from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
WAREHOUSE_DIR = ROOT / "warehouse"
if str(WAREHOUSE_DIR) not in sys.path:
    sys.path.insert(0, str(WAREHOUSE_DIR))

import load_streaming


class FakeConnection:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class FakeCursor:
    def __init__(self, staged_rows: int, fact_rows: int) -> None:
        self.connection = FakeConnection()
        self.staged_rows = staged_rows
        self.fact_rows = fact_rows
        self.rowcount = 0
        self._fetchone_value: tuple[int] = (0,)
        self.executed_sql: list[str] = []

    def execute(self, sql: str) -> None:
        self.executed_sql.append(sql)
        normalized_sql = " ".join(sql.split())
        if "SELECT COUNT(*) FROM stg_prompt_events" in normalized_sql:
            self._fetchone_value = (self.staged_rows,)
            self.rowcount = 1
        elif "SELECT COUNT(*) FROM stg_model_comparisons" in normalized_sql:
            self._fetchone_value = (self.staged_rows,)
            self.rowcount = 1
        elif "INSERT INTO fact_promptexecution" in normalized_sql:
            self.rowcount = self.fact_rows
        elif "INSERT INTO fact_model_comparison" in normalized_sql:
            self.rowcount = self.fact_rows
        else:
            self.rowcount = 0

    def fetchone(self) -> tuple[int]:
        return self._fetchone_value

    def copy_expert(self, _sql: str, _buffer) -> None:
        return None


class LoadStreamingTests(unittest.TestCase):
    def test_normalize_prompt_record_backfills_hash_and_trims(self) -> None:
        normalized = load_streaming.normalize_prompt_record(
            {
                "prompt_text": "Hello\r\nworld",
                "prompt_hash": "  ",
                "model_name": " GPT-4 ",
                "dataset_name": " prompt_library ",
                "timestamp": "2026-03-07T12:00:00Z",
            }
        )
        self.assertIsNotNone(normalized)
        assert normalized is not None
        self.assertEqual(normalized["prompt_text"], "Hello\nworld")
        self.assertEqual(normalized["model_name"], "GPT-4")
        self.assertEqual(normalized["dataset_name"], "prompt_library")
        self.assertEqual(len(normalized["prompt_hash"]), 64)
        self.assertEqual(normalized["timestamp"].isoformat(sep=" "), "2026-03-07 12:00:00")

    def test_normalize_prompt_record_rejects_missing_identity(self) -> None:
        self.assertIsNone(
            load_streaming.normalize_prompt_record(
                {
                    "prompt_text": None,
                    "prompt_hash": None,
                    "dataset_name": "x",
                }
            )
        )

    def test_normalize_comparison_record_normalizes_hash_and_models(self) -> None:
        normalized = load_streaming.normalize_comparison_record(
            {
                "prompt_text": "Compare models",
                "prompt_hash": " ABCDEF ",
                "model_a": " vicuna-13b ",
                "model_b": " koala-13b ",
                "winner": " model_a ",
                "dataset_name": " chatbot_arena ",
            }
        )
        self.assertIsNotNone(normalized)
        assert normalized is not None
        self.assertEqual(normalized["prompt_hash"], "abcdef")
        self.assertEqual(normalized["model_a"], "vicuna-13b")
        self.assertEqual(normalized["model_b"], "koala-13b")
        self.assertEqual(normalized["winner"], "model_a")
        self.assertEqual(normalized["dataset_name"], "chatbot_arena")

    def test_merge_prompt_stage_uses_nullable_time_and_source_joins(self) -> None:
        cur = FakeCursor(staged_rows=5, fact_rows=4)
        stats = load_streaming.merge_prompt_stage(cur)
        sql_text = "\n".join(cur.executed_sql)
        self.assertIn("LEFT JOIN dim_time dt", sql_text)
        self.assertIn("LEFT JOIN dim_source src", sql_text)
        self.assertIn("EXTRACT(WEEK FROM s.timestamp)::INTEGER", sql_text)
        self.assertEqual(stats.staged_rows, 5)
        self.assertEqual(stats.fact_rows, 4)
        self.assertEqual(stats.rejected_rows, 1)

    def test_load_prompts_commits_each_chunk(self) -> None:
        cur = FakeCursor(staged_rows=1, fact_rows=1)
        rows = [{"prompt_text": "Hello", "timestamp": "2026-03-07T12:00:00Z"}]
        with mock.patch.object(load_streaming, "iter_jsonl", return_value=iter(rows * 2)):
            with mock.patch.object(
                load_streaming,
                "merge_prompt_stage",
                side_effect=[
                    load_streaming.ChunkMergeStats(staged_rows=1, fact_rows=1, rejected_rows=0),
                    load_streaming.ChunkMergeStats(staged_rows=1, fact_rows=1, rejected_rows=0),
                ],
            ):
                totals = load_streaming.load_prompts(cur, Path("unused"), chunk_size=1)
        self.assertEqual(totals.prompt_rows_processed, 2)
        self.assertEqual(totals.prompt_rows_loaded, 2)
        self.assertEqual(cur.connection.commits, 2)
        self.assertEqual(cur.connection.rollbacks, 0)

    def test_load_prompts_rolls_back_failed_chunk_only(self) -> None:
        cur = FakeCursor(staged_rows=1, fact_rows=1)
        rows = [{"prompt_text": "Hello", "timestamp": "2026-03-07T12:00:00Z"}]
        with mock.patch.object(load_streaming, "iter_jsonl", return_value=iter(rows * 2)):
            with mock.patch.object(
                load_streaming,
                "merge_prompt_stage",
                side_effect=[
                    load_streaming.ChunkMergeStats(staged_rows=1, fact_rows=1, rejected_rows=0),
                    RuntimeError("boom"),
                ],
            ):
                with self.assertRaises(RuntimeError):
                    load_streaming.load_prompts(cur, Path("unused"), chunk_size=1)
        self.assertEqual(cur.connection.commits, 1)
        self.assertEqual(cur.connection.rollbacks, 1)


if __name__ == "__main__":
    unittest.main()
