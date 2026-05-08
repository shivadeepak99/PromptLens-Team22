"""Loader for transformed PromptLens prompt/comparison records into PostgreSQL."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent


def _import_validation():
    import sys

    validation_dir = ROOT_DIR / "validation"
    if str(validation_dir) not in sys.path:
        sys.path.insert(0, str(validation_dir))
    from validation_checks import validate_comparison_record, validate_prompt_record

    return validate_prompt_record, validate_comparison_record


def get_connection():
    try:
        import psycopg2
    except ImportError as exc:
        raise RuntimeError(
            "psycopg2 is required to load PromptLens records into PostgreSQL. "
            "Install dependencies from requirements.txt first."
        ) from exc
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return psycopg2.connect(url)


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str):
        raise ValueError(f"Unsupported timestamp value: {value!r}")
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(candidate)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _utc_naive(value: Any) -> datetime:
    return _parse_timestamp(value).astimezone(timezone.utc).replace(tzinfo=None)


def _session_id(record: dict) -> str:
    provided = record.get("session_id")
    if provided:
        return str(provided)
    conversation_id = str(record.get("conversation_id") or "")
    return hashlib.sha256(conversation_id.encode("utf-8")).hexdigest()


def _task_identity(record: dict) -> tuple[Any, ...]:
    return (
        record.get("task_type"),
        record.get("domain"),
        record.get("language"),
        record.get("programming_lang"),
        record.get("difficulty"),
        record.get("benchmark_id"),
        record.get("task_category") or record.get("category"),
    )


def _has_task_data(record: dict) -> bool:
    return any(value not in (None, "") for value in _task_identity(record))


def _prompt_identity(record: dict) -> tuple[str, str]:
    return str(record["prompt_hash"]), str(record["prompt_text"])


def _source_identity(record: dict) -> str:
    return str(record["dataset_name"])


def _winner_model_name(record: dict) -> str | None:
    winner = str(record.get("winner") or "").strip().lower()
    if winner == "model_a":
        return record.get("model_a")
    if winner == "model_b":
        return record.get("model_b")
    return None


@dataclass
class StagedWarehouseData:
    prompts: dict[tuple[str, str], dict] = field(default_factory=dict)
    models: dict[str, dict] = field(default_factory=dict)
    tasks: dict[tuple[Any, ...], dict] = field(default_factory=dict)
    times: dict[datetime, dict] = field(default_factory=dict)
    sessions: dict[str, dict] = field(default_factory=dict)
    sources: dict[str, dict] = field(default_factory=dict)
    prompt_facts: list[dict] = field(default_factory=list)
    comparison_facts: list[dict] = field(default_factory=list)


def stage_records(prompt_records: list[dict], comparison_records: list[dict]) -> StagedWarehouseData:
    validate_prompt_record, validate_comparison_record = _import_validation()
    staged = StagedWarehouseData()

    for record in prompt_records:
        if not validate_prompt_record(record):
            raise ValueError(f"Invalid prompt record: {record}")
        prompt_key = _prompt_identity(record)
        staged.prompts.setdefault(
            prompt_key,
            {
                "prompt_text": record["prompt_text"],
                "prompt_hash": record["prompt_hash"],
                "prompt_length": int(record["prompt_length"]),
                "token_estimate": int(record["token_estimate"]),
                "prompt_type": record.get("prompt_type") or "standard",
                "contains_code": bool(record.get("contains_code")),
                "contains_examples": bool(record.get("contains_examples")),
                "contains_constraints": bool(record.get("contains_constraints")),
                "language": record.get("language") or "unknown",
                "complexity_score": float(record.get("complexity_score") or 0.0),
                "instruction_density": float(record.get("instruction_density") or 0.0),
                "length": int(record.get("length") or record["prompt_length"]),
                "token_count": int(record.get("token_count") or record["token_estimate"]),
                "type": record.get("type") or record.get("prompt_type") or "standard",
            },
        )
        model_name = str(record.get("model_name") or "").strip()
        if model_name:
            staged.models.setdefault(model_name, {"model_name": model_name})
        if _has_task_data(record):
            identity = _task_identity(record)
            staged.tasks.setdefault(
                identity,
                {
                    "task_type": record.get("task_type"),
                    "domain": record.get("domain"),
                    "language": record.get("language"),
                    "programming_lang": record.get("programming_lang"),
                    "difficulty": record.get("difficulty"),
                    "benchmark_id": record.get("benchmark_id"),
                    "category": record.get("task_category") or record.get("category"),
                },
            )
        timestamp = _utc_naive(record["timestamp"])
        staged.times.setdefault(
            timestamp,
            {
                "ts": timestamp,
                "year": timestamp.year,
                "quarter": ((timestamp.month - 1) // 3) + 1,
                "month": timestamp.month,
                "day": timestamp.day,
                "day_of_week": timestamp.isoweekday(),
                "week_number": int(timestamp.strftime("%W")),
                "is_weekend": timestamp.isoweekday() >= 6,
            },
        )
        session_id = _session_id(record)
        staged.sessions.setdefault(session_id, {"session_id": session_id})
        source_name = _source_identity(record)
        staged.sources.setdefault(
            source_name,
            {
                "dataset_name": source_name,
                "collection_method": record.get("collection_method"),
                "version": record.get("version"),
                "ingest_timestamp": _utc_naive(record.get("ingest_timestamp") or record["timestamp"]),
                "batch_id": record.get("batch_id"),
            },
        )
        staged.prompt_facts.append(dict(record))

    for record in comparison_records:
        if not validate_comparison_record(record):
            raise ValueError(f"Invalid comparison record: {record}")
        prompt_key = _prompt_identity(record)
        staged.prompts.setdefault(
            prompt_key,
            {
                "prompt_text": record["prompt_text"],
                "prompt_hash": record["prompt_hash"],
                "prompt_length": int(record["prompt_length"]),
                "token_estimate": int(record["token_estimate"]),
                "prompt_type": record.get("prompt_type") or "standard",
                "contains_code": bool(record.get("contains_code")),
                "contains_examples": bool(record.get("contains_examples")),
                "contains_constraints": bool(record.get("contains_constraints")),
                "language": record.get("language") or "unknown",
                "complexity_score": float(record.get("complexity_score") or 0.0),
                "instruction_density": float(record.get("instruction_density") or 0.0),
                "length": int(record.get("length") or record["prompt_length"]),
                "token_count": int(record.get("token_count") or record["token_estimate"]),
                "type": record.get("type") or record.get("prompt_type") or "standard",
            },
        )
        staged.models.setdefault(record["model_a"], {"model_name": record["model_a"]})
        staged.models.setdefault(record["model_b"], {"model_name": record["model_b"]})
        winner_model = _winner_model_name(record)
        if winner_model:
            staged.models.setdefault(winner_model, {"model_name": winner_model})
        timestamp = _utc_naive(record["timestamp"])
        staged.times.setdefault(
            timestamp,
            {
                "ts": timestamp,
                "year": timestamp.year,
                "quarter": ((timestamp.month - 1) // 3) + 1,
                "month": timestamp.month,
                "day": timestamp.day,
                "day_of_week": timestamp.isoweekday(),
                "week_number": int(timestamp.strftime("%W")),
                "is_weekend": timestamp.isoweekday() >= 6,
            },
        )
        source_name = _source_identity(record)
        staged.sources.setdefault(
            source_name,
            {
                "dataset_name": source_name,
                "collection_method": record.get("collection_method"),
                "version": record.get("version"),
                "ingest_timestamp": _utc_naive(record.get("ingest_timestamp") or record["timestamp"]),
                "batch_id": record.get("batch_id"),
            },
        )
        staged.comparison_facts.append(dict(record))

    return staged


class WarehouseLoader:
    def __init__(self, conn) -> None:
        self.conn = conn
        self.prompt_cache: dict[str, int] = {}
        self.model_cache: dict[str, int] = {}
        self.task_cache: dict[tuple[Any, ...], int] = {}
        self.time_cache: dict[datetime, int] = {}
        self.session_cache: dict[str, int] = {}
        self.source_cache: dict[str, int] = {}

    def ensure_prompt_key(self, cur, row: dict) -> int:
        identity = row["prompt_hash"]
        if identity in self.prompt_cache:
            return self.prompt_cache[identity]
        cur.execute(
            """
            INSERT INTO dim_prompt (
                prompt_text, prompt_hash, prompt_length, token_estimate, prompt_type,
                contains_code, contains_examples, contains_constraints, language,
                complexity_score, instruction_density, length, token_count, type
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (prompt_hash)
            DO UPDATE SET
                prompt_text = EXCLUDED.prompt_text,
                prompt_length = EXCLUDED.prompt_length,
                token_estimate = EXCLUDED.token_estimate,
                prompt_type = EXCLUDED.prompt_type,
                contains_code = EXCLUDED.contains_code,
                contains_examples = EXCLUDED.contains_examples,
                contains_constraints = EXCLUDED.contains_constraints,
                language = EXCLUDED.language,
                complexity_score = EXCLUDED.complexity_score,
                instruction_density = EXCLUDED.instruction_density,
                length = EXCLUDED.length,
                token_count = EXCLUDED.token_count,
                type = EXCLUDED.type
            RETURNING prompt_key
            """,
            (
                row["prompt_text"],
                row["prompt_hash"],
                row["prompt_length"],
                row["token_estimate"],
                row.get("prompt_type") or "standard",
                row.get("contains_code", False),
                row.get("contains_examples", False),
                row.get("contains_constraints", False),
                row.get("language") or "unknown",
                row.get("complexity_score", 0.0),
                row.get("instruction_density"),
                row.get("length"),
                row.get("token_count"),
                row.get("type"),
            ),
        )
        prompt_key = cur.fetchone()[0]
        self.prompt_cache[identity] = prompt_key
        return prompt_key

    def ensure_model_key(self, cur, model_name: str) -> int:
        if model_name in self.model_cache:
            return self.model_cache[model_name]
        cur.execute(
            """
            INSERT INTO dim_model (model_name)
            VALUES (%s)
            ON CONFLICT (model_name)
            DO UPDATE SET model_name = EXCLUDED.model_name
            RETURNING model_key
            """,
            (model_name,),
        )
        model_key = cur.fetchone()[0]
        self.model_cache[model_name] = model_key
        return model_key

    def ensure_task_key(self, cur, row: dict) -> int:
        identity = _task_identity(row)
        if identity in self.task_cache:
            return self.task_cache[identity]
        cur.execute(
            """
            SELECT task_key
            FROM dim_task
            WHERE task_type IS NOT DISTINCT FROM %s
              AND domain IS NOT DISTINCT FROM %s
              AND language IS NOT DISTINCT FROM %s
              AND programming_lang IS NOT DISTINCT FROM %s
              AND difficulty IS NOT DISTINCT FROM %s
              AND benchmark_id IS NOT DISTINCT FROM %s
              AND category IS NOT DISTINCT FROM %s
            """,
            identity,
        )
        existing = cur.fetchone()
        if existing:
            task_key = existing[0]
        else:
            cur.execute(
                """
                INSERT INTO dim_task (
                    task_type, domain, language, programming_lang, difficulty, benchmark_id, category
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING task_key
                """,
                identity,
            )
            task_key = cur.fetchone()[0]
        self.task_cache[identity] = task_key
        return task_key

    def ensure_time_key(self, cur, row: dict) -> int:
        timestamp = row["ts"]
        if timestamp in self.time_cache:
            return self.time_cache[timestamp]
        cur.execute(
            """
            INSERT INTO dim_time (ts, year, quarter, month, day, day_of_week, week_number, is_weekend)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ts)
            DO UPDATE SET ts = EXCLUDED.ts
            RETURNING time_key
            """,
            (
                row["ts"],
                row["year"],
                row["quarter"],
                row["month"],
                row["day"],
                row["day_of_week"],
                row["week_number"],
                row["is_weekend"],
            ),
        )
        time_key = cur.fetchone()[0]
        self.time_cache[timestamp] = time_key
        return time_key

    def ensure_session_key(self, cur, row: dict) -> int:
        session_id = row["session_id"]
        if session_id in self.session_cache:
            return self.session_cache[session_id]
        cur.execute(
            """
            INSERT INTO dim_session (session_id)
            VALUES (%s)
            ON CONFLICT (session_id)
            DO UPDATE SET session_id = EXCLUDED.session_id
            RETURNING session_key
            """,
            (session_id,),
        )
        session_key = cur.fetchone()[0]
        self.session_cache[session_id] = session_key
        return session_key

    def ensure_source_key(self, cur, row: dict) -> int:
        dataset_name = row["dataset_name"]
        if dataset_name in self.source_cache:
            return self.source_cache[dataset_name]
        cur.execute(
            """
            INSERT INTO dim_source (dataset_name, collection_method, version, ingest_timestamp, batch_id)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (dataset_name)
            DO UPDATE SET
                collection_method = EXCLUDED.collection_method,
                version = EXCLUDED.version,
                ingest_timestamp = EXCLUDED.ingest_timestamp,
                batch_id = EXCLUDED.batch_id
            RETURNING source_key
            """,
            (
                dataset_name,
                row.get("collection_method"),
                row.get("version"),
                row.get("ingest_timestamp"),
                row.get("batch_id"),
            ),
        )
        source_key = cur.fetchone()[0]
        self.source_cache[dataset_name] = source_key
        return source_key

    def load(self, staged: StagedWarehouseData) -> dict[str, int]:
        with self.conn.cursor() as cur:
            for row in staged.prompts.values():
                self.ensure_prompt_key(cur, row)
            for row in staged.models.values():
                self.ensure_model_key(cur, row["model_name"])
            for row in staged.tasks.values():
                self.ensure_task_key(cur, row)
            for row in staged.times.values():
                self.ensure_time_key(cur, row)
            for row in staged.sessions.values():
                self.ensure_session_key(cur, row)
            for row in staged.sources.values():
                self.ensure_source_key(cur, row)

            for fact in staged.prompt_facts:
                prompt_key = self.ensure_prompt_key(cur, staged.prompts[_prompt_identity(fact)])
                model_key = None
                if fact.get("model_name"):
                    model_key = self.ensure_model_key(cur, str(fact["model_name"]))
                task_key = None
                if _has_task_data(fact):
                    task_key = self.ensure_task_key(cur, fact)
                time_key = self.ensure_time_key(cur, staged.times[_utc_naive(fact["timestamp"])])
                session_key = self.ensure_session_key(cur, staged.sessions[_session_id(fact)])
                source_key = self.ensure_source_key(cur, staged.sources[_source_identity(fact)])
                cur.execute(
                    """
                    INSERT INTO fact_promptexecution (
                        conversation_id, turn_number, prompt_key, model_key, task_key, time_key,
                        session_key, source_key, response_text, tokens, response_tokens, latency,
                        quality_label, success_score
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        fact["conversation_id"],
                        int(fact["turn_number"]),
                        prompt_key,
                        model_key,
                        task_key,
                        time_key,
                        session_key,
                        source_key,
                        fact.get("response_text"),
                        int(fact["tokens"]),
                        int(fact["response_tokens"]) if fact.get("response_tokens") is not None else None,
                        fact.get("latency"),
                        fact.get("quality_label"),
                        float(fact["success_score"]) if fact.get("success_score") is not None else None,
                    ),
                )

            for fact in staged.comparison_facts:
                prompt_key = self.ensure_prompt_key(cur, staged.prompts[_prompt_identity(fact)])
                model_a_key = self.ensure_model_key(cur, fact["model_a"])
                model_b_key = self.ensure_model_key(cur, fact["model_b"])
                winner_model_key = None
                winner_model_name = _winner_model_name(fact)
                if winner_model_name:
                    winner_model_key = self.ensure_model_key(cur, winner_model_name)
                time_key = self.ensure_time_key(cur, staged.times[_utc_naive(fact["timestamp"])])
                source_key = self.ensure_source_key(cur, staged.sources[_source_identity(fact)])
                cur.execute(
                    """
                    INSERT INTO fact_model_comparison (
                        conversation_id, prompt_key, model_a_key, model_b_key, winner_model_key, time_key, source_key
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        fact["conversation_id"],
                        prompt_key,
                        model_a_key,
                        model_b_key,
                        winner_model_key,
                        time_key,
                        source_key,
                    ),
                )
        self.conn.commit()
        return {
            "prompt_dimensions": len(staged.prompts),
            "model_dimensions": len(staged.models),
            "task_dimensions": len(staged.tasks),
            "time_dimensions": len(staged.times),
            "session_dimensions": len(staged.sessions),
            "source_dimensions": len(staged.sources),
            "prompt_facts": len(staged.prompt_facts),
            "comparison_facts": len(staged.comparison_facts),
        }


def read_jsonl(path: str | None) -> list[dict]:
    if not path:
        return []
    records: list[dict] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load PromptLens transformed records into PostgreSQL")
    parser.add_argument("--input", required=True, help="Path to prompt_events.jsonl")
    parser.add_argument("--comparisons-input", help="Path to model_comparisons.jsonl")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    prompt_records = read_jsonl(args.input)
    comparison_records = read_jsonl(args.comparisons_input)
    staged = stage_records(prompt_records, comparison_records)
    conn = get_connection()
    stats = WarehouseLoader(conn).load(staged)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
