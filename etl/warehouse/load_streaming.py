"""High-throughput bulk loader for PromptLens warehouse tables."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import io
import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Callable, Iterable

import psycopg2


ROOT_DIR = Path(__file__).resolve().parent.parent
SCHEMA_FILE = ROOT_DIR / "warehouse" / "schema.sql"
DEFAULT_PROMPT_INPUT = ROOT_DIR / "transformed" / "prompt_events.jsonl"
DEFAULT_COMPARISON_INPUT = ROOT_DIR / "transformed" / "model_comparisons.jsonl"
DB_URL = os.getenv("DATABASE_URL") or os.getenv("DB_URL")
if not DB_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")
    
COPY_CHUNK_SIZE = int(os.getenv("COPY_CHUNK_SIZE", "50000"))
PROGRESS_INTERVAL_SECONDS = float(os.getenv("LOAD_PROGRESS_INTERVAL", "5"))

PROMPT_STAGE_COLUMNS = [
    "conversation_id",
    "turn_number",
    "prompt_text",
    "prompt_hash",
    "prompt_length",
    "token_estimate",
    "prompt_type",
    "contains_code",
    "contains_examples",
    "contains_constraints",
    "language",
    "complexity_score",
    "instruction_density",
    "length",
    "token_count",
    "type",
    "response_text",
    "response_tokens",
    "tokens",
    "latency",
    "quality_label",
    "success_score",
    "model_name",
    "task_type",
    "domain",
    "programming_lang",
    "difficulty",
    "benchmark_id",
    "task_category",
    "timestamp",
    "session_id",
    "dataset_name",
    "collection_method",
    "version",
    "ingest_timestamp",
    "batch_id",
]

COMPARISON_STAGE_COLUMNS = [
    "conversation_id",
    "prompt_text",
    "prompt_hash",
    "prompt_length",
    "token_estimate",
    "prompt_type",
    "contains_code",
    "contains_examples",
    "contains_constraints",
    "language",
    "complexity_score",
    "instruction_density",
    "length",
    "token_count",
    "type",
    "timestamp",
    "dataset_name",
    "collection_method",
    "version",
    "ingest_timestamp",
    "batch_id",
    "model_a",
    "model_b",
    "winner",
]

TRIM_FIELDS = {
    "conversation_id",
    "prompt_type",
    "language",
    "type",
    "quality_label",
    "task_type",
    "domain",
    "programming_lang",
    "difficulty",
    "benchmark_id",
    "task_category",
    "session_id",
    "dataset_name",
    "collection_method",
    "version",
    "batch_id",
    "model_name",
    "model_a",
    "model_b",
    "winner",
}

TEXT_PAYLOAD_FIELDS = {"prompt_text", "response_text"}


@dataclass
class ChunkMergeStats:
    staged_rows: int = 0
    fact_rows: int = 0
    rejected_rows: int = 0


@dataclass
class LoadTotals:
    prompt_rows_processed: int = 0
    prompt_rows_loaded: int = 0
    prompt_rows_rejected: int = 0
    comparison_rows_processed: int = 0
    comparison_rows_loaded: int = 0
    comparison_rows_rejected: int = 0


class ProgressReporter:
    def __init__(self, interval_seconds: float) -> None:
        self.interval_seconds = max(interval_seconds, 1.0)
        self.started_at = time.time()
        self.phase = "starting"
        self.prompt_rows = 0
        self.prompt_fact_rows = 0
        self.prompt_rejected_rows = 0
        self.comparison_rows = 0
        self.comparison_fact_rows = 0
        self.comparison_rejected_rows = 0
        self.current_chunk = 0
        self.current_target = "startup"
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()
        self.log_snapshot(force=True)

    def stop(self, final_phase: str = "finished") -> None:
        self.update(phase=final_phase)
        self.log_snapshot(force=True)
        self._stop_event.set()
        self._thread.join(timeout=self.interval_seconds + 1.0)

    def update(
        self,
        *,
        phase: str | None = None,
        prompt_rows: int | None = None,
        prompt_fact_rows: int | None = None,
        prompt_rejected_rows: int | None = None,
        comparison_rows: int | None = None,
        comparison_fact_rows: int | None = None,
        comparison_rejected_rows: int | None = None,
        current_chunk: int | None = None,
        current_target: str | None = None,
    ) -> None:
        with self._lock:
            if phase is not None:
                self.phase = phase
            if prompt_rows is not None:
                self.prompt_rows = prompt_rows
            if prompt_fact_rows is not None:
                self.prompt_fact_rows = prompt_fact_rows
            if prompt_rejected_rows is not None:
                self.prompt_rejected_rows = prompt_rejected_rows
            if comparison_rows is not None:
                self.comparison_rows = comparison_rows
            if comparison_fact_rows is not None:
                self.comparison_fact_rows = comparison_fact_rows
            if comparison_rejected_rows is not None:
                self.comparison_rejected_rows = comparison_rejected_rows
            if current_chunk is not None:
                self.current_chunk = current_chunk
            if current_target is not None:
                self.current_target = current_target

    def log_snapshot(self, force: bool = False) -> None:
        with self._lock:
            phase = self.phase
            prompt_rows = self.prompt_rows
            prompt_fact_rows = self.prompt_fact_rows
            prompt_rejected_rows = self.prompt_rejected_rows
            comparison_rows = self.comparison_rows
            comparison_fact_rows = self.comparison_fact_rows
            comparison_rejected_rows = self.comparison_rejected_rows
            current_chunk = self.current_chunk
            current_target = self.current_target
        elapsed = max(time.time() - self.started_at, 0.0)
        chunk_text = f", chunk={current_chunk}" if current_chunk else ""
        prefix = "[load_streaming]"
        if force:
            prefix = "[load_streaming][checkpoint]"
        print(
            f"{prefix} elapsed={elapsed:.1f}s phase={phase} target={current_target}{chunk_text} "
            f"prompt_rows={prompt_rows} prompt_facts={prompt_fact_rows} prompt_rejected={prompt_rejected_rows} "
            f"comparison_rows={comparison_rows} comparison_facts={comparison_fact_rows} "
            f"comparison_rejected={comparison_rejected_rows}",
            flush=True,
        )

    def _run(self) -> None:
        while not self._stop_event.wait(self.interval_seconds):
            self.log_snapshot()


def get_conn():
    return psycopg2.connect(DB_URL)


def apply_schema(conn) -> None:
    schema_sql = SCHEMA_FILE.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(schema_sql)
    conn.commit()


def set_utc_timezone(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("SET TIME ZONE 'UTC'")


def create_stage_tables(cur) -> None:
    cur.execute(
        """
        CREATE TEMP TABLE IF NOT EXISTS stg_prompt_events (
            conversation_id TEXT,
            turn_number INTEGER,
            prompt_text TEXT,
            prompt_hash CHAR(64),
            prompt_length INTEGER,
            token_estimate INTEGER,
            prompt_type TEXT,
            contains_code BOOLEAN,
            contains_examples BOOLEAN,
            contains_constraints BOOLEAN,
            language TEXT,
            complexity_score DOUBLE PRECISION,
            instruction_density DOUBLE PRECISION,
            length INTEGER,
            token_count INTEGER,
            type TEXT,
            response_text TEXT,
            response_tokens INTEGER,
            tokens INTEGER,
            latency DOUBLE PRECISION,
            quality_label TEXT,
            success_score DOUBLE PRECISION,
            model_name TEXT,
            task_type TEXT,
            domain TEXT,
            programming_lang TEXT,
            difficulty TEXT,
            benchmark_id TEXT,
            task_category TEXT,
            timestamp TIMESTAMP,
            session_id TEXT,
            dataset_name TEXT,
            collection_method TEXT,
            version TEXT,
            ingest_timestamp TIMESTAMP,
            batch_id TEXT
        ) ON COMMIT PRESERVE ROWS;

        CREATE TEMP TABLE IF NOT EXISTS stg_model_comparisons (
            conversation_id TEXT,
            prompt_text TEXT,
            prompt_hash CHAR(64),
            prompt_length INTEGER,
            token_estimate INTEGER,
            prompt_type TEXT,
            contains_code BOOLEAN,
            contains_examples BOOLEAN,
            contains_constraints BOOLEAN,
            language TEXT,
            complexity_score DOUBLE PRECISION,
            instruction_density DOUBLE PRECISION,
            length INTEGER,
            token_count INTEGER,
            type TEXT,
            timestamp TIMESTAMP,
            dataset_name TEXT,
            collection_method TEXT,
            version TEXT,
            ingest_timestamp TIMESTAMP,
            batch_id TEXT,
            model_a TEXT,
            model_b TEXT,
            winner TEXT
        ) ON COMMIT PRESERVE ROWS;
        """
    )


def iter_jsonl(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def chunked(records: Iterable[dict], chunk_size: int) -> Iterable[list[dict]]:
    chunk: list[dict] = []
    for record in records:
        chunk.append(record)
        if len(chunk) >= chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def normalize_text_field(value: Any, *, strip: bool = False) -> str | None:
    if value is None:
        return None
    text = str(value).replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if strip:
        text = text.strip()
    return text


def normalize_prompt_hash(value: Any) -> str | None:
    text = normalize_text_field(value, strip=True)
    if not text:
        return None
    return text.lower()


def normalize_timestamp_value(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        timestamp = value
    elif isinstance(value, (int, float)):
        try:
            timestamp = datetime.fromtimestamp(value, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    else:
        candidate = normalize_text_field(value, strip=True)
        if not candidate:
            return None
        candidate = candidate[:-1] + "+00:00" if candidate.endswith("Z") else candidate
        try:
            timestamp = datetime.fromisoformat(candidate)
        except ValueError:
            return None
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc).replace(tzinfo=None)


def ensure_prompt_hash(prompt_text: str | None, prompt_hash: str | None) -> str | None:
    if prompt_hash:
        return prompt_hash
    if prompt_text is None or prompt_text == "":
        return None
    return hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()


def normalize_prompt_record(record: dict[str, Any]) -> dict[str, Any] | None:
    normalized = dict(record)
    for field in TEXT_PAYLOAD_FIELDS:
        if field in normalized:
            normalized[field] = normalize_text_field(normalized.get(field))
    for field in TRIM_FIELDS:
        if field in normalized:
            normalized[field] = normalize_text_field(normalized.get(field), strip=True)

    normalized["prompt_hash"] = ensure_prompt_hash(
        normalized.get("prompt_text"),
        normalize_prompt_hash(normalized.get("prompt_hash")),
    )
    normalized["timestamp"] = normalize_timestamp_value(normalized.get("timestamp"))
    normalized["ingest_timestamp"] = normalize_timestamp_value(normalized.get("ingest_timestamp"))

    if normalized.get("prompt_hash") is None:
        return None
    return normalized


def normalize_comparison_record(record: dict[str, Any]) -> dict[str, Any] | None:
    normalized = dict(record)
    if "prompt_text" in normalized:
        normalized["prompt_text"] = normalize_text_field(normalized.get("prompt_text"))
    for field in TRIM_FIELDS:
        if field in normalized:
            normalized[field] = normalize_text_field(normalized.get(field), strip=True)

    normalized["prompt_hash"] = ensure_prompt_hash(
        normalized.get("prompt_text"),
        normalize_prompt_hash(normalized.get("prompt_hash")),
    )
    normalized["timestamp"] = normalize_timestamp_value(normalized.get("timestamp"))
    normalized["ingest_timestamp"] = normalize_timestamp_value(normalized.get("ingest_timestamp"))

    if normalized.get("prompt_hash") is None:
        return None
    return normalized


def prepare_stage_records(
    records: list[dict[str, Any]],
    normalizer: Callable[[dict[str, Any]], dict[str, Any] | None],
) -> tuple[list[dict[str, Any]], int]:
    normalized_records: list[dict[str, Any]] = []
    rejected_rows = 0
    for record in records:
        normalized = normalizer(record)
        if normalized is None:
            rejected_rows += 1
            continue
        normalized_records.append(normalized)
    return normalized_records, rejected_rows


def copy_value(value: Any):
    if value is None:
        return r"\N"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    return str(value)


def copy_chunk(cur, table_name: str, columns: list[str], records: list[dict[str, Any]]) -> int:
    if not records:
        return 0
    buffer = io.StringIO()
    writer = csv.writer(
        buffer,
        delimiter="\t",
        quotechar='"',
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )
    for record in records:
        writer.writerow([copy_value(record.get(column)) for column in columns])
    buffer.seek(0)
    copy_sql = (
        f"COPY {table_name} ({', '.join(columns)}) "
        "FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t', QUOTE '\"', ESCAPE '\"', NULL '\\N')"
    )
    cur.copy_expert(copy_sql, buffer)
    return len(records)


def _upsert_prompt_dimension(cur, stage_table: str) -> None:
    cur.execute(
        f"""
        WITH dedup_prompt AS (
            SELECT DISTINCT ON (s.prompt_hash)
                s.prompt_text,
                s.prompt_hash,
                s.prompt_length,
                s.token_estimate,
                s.prompt_type,
                s.contains_code,
                s.contains_examples,
                s.contains_constraints,
                s.language,
                s.complexity_score,
                s.instruction_density,
                s.length,
                s.token_count,
                s.type
            FROM {stage_table} s
            WHERE s.prompt_hash IS NOT NULL
            ORDER BY s.prompt_hash, s.prompt_length DESC NULLS LAST, s.prompt_text
        )
        INSERT INTO dim_prompt (
            prompt_text, prompt_hash, prompt_length, token_estimate, prompt_type,
            contains_code, contains_examples, contains_constraints, language,
            complexity_score, instruction_density, length, token_count, type
        )
        SELECT
            d.prompt_text,
            d.prompt_hash,
            d.prompt_length,
            d.token_estimate,
            COALESCE(d.prompt_type, 'standard'),
            COALESCE(d.contains_code, FALSE),
            COALESCE(d.contains_examples, FALSE),
            COALESCE(d.contains_constraints, FALSE),
            COALESCE(d.language, 'unknown'),
            COALESCE(d.complexity_score, 0),
            d.instruction_density,
            COALESCE(d.length, d.prompt_length),
            COALESCE(d.token_count, d.token_estimate),
            COALESCE(d.type, d.prompt_type, 'standard')
        FROM dedup_prompt d
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
        """
    )


def merge_prompt_stage(cur) -> ChunkMergeStats:
    cur.execute("ANALYZE stg_prompt_events")
    cur.execute("SELECT COUNT(*) FROM stg_prompt_events")
    staged_rows = int(cur.fetchone()[0])
    if staged_rows == 0:
        return ChunkMergeStats()

    _upsert_prompt_dimension(cur, "stg_prompt_events")

    cur.execute(
        """
        INSERT INTO dim_model (model_name)
        SELECT DISTINCT s.model_name
        FROM stg_prompt_events s
        WHERE s.model_name IS NOT NULL AND s.model_name <> ''
        ON CONFLICT (model_name) DO NOTHING
        """
    )

    cur.execute(
        """
        INSERT INTO dim_task (
            task_type, domain, language, programming_lang, difficulty, benchmark_id, category
        )
        SELECT DISTINCT
            s.task_type,
            s.domain,
            s.language,
            s.programming_lang,
            s.difficulty,
            s.benchmark_id,
            s.task_category
        FROM stg_prompt_events s
        LEFT JOIN dim_task d
          ON d.task_type IS NOT DISTINCT FROM s.task_type
         AND d.domain IS NOT DISTINCT FROM s.domain
         AND d.language IS NOT DISTINCT FROM s.language
         AND d.programming_lang IS NOT DISTINCT FROM s.programming_lang
         AND d.difficulty IS NOT DISTINCT FROM s.difficulty
         AND d.benchmark_id IS NOT DISTINCT FROM s.benchmark_id
         AND d.category IS NOT DISTINCT FROM s.task_category
        WHERE (
            s.task_type IS NOT NULL
            OR s.domain IS NOT NULL
            OR s.language IS NOT NULL
            OR s.programming_lang IS NOT NULL
            OR s.difficulty IS NOT NULL
            OR s.benchmark_id IS NOT NULL
            OR s.task_category IS NOT NULL
        )
          AND d.task_key IS NULL
        """
    )

    cur.execute(
        """
        INSERT INTO dim_time (ts, year, quarter, month, day, day_of_week, week_number, is_weekend)
        SELECT DISTINCT
            s.timestamp,
            EXTRACT(YEAR FROM s.timestamp)::INTEGER,
            EXTRACT(QUARTER FROM s.timestamp)::INTEGER,
            EXTRACT(MONTH FROM s.timestamp)::INTEGER,
            EXTRACT(DAY FROM s.timestamp)::INTEGER,
            EXTRACT(ISODOW FROM s.timestamp)::INTEGER,
            EXTRACT(WEEK FROM s.timestamp)::INTEGER,
            EXTRACT(ISODOW FROM s.timestamp) IN (6, 7)
        FROM stg_prompt_events s
        WHERE s.timestamp IS NOT NULL
        ON CONFLICT (ts) DO NOTHING
        """
    )

    cur.execute(
        """
        INSERT INTO dim_session (session_id)
        SELECT DISTINCT s.session_id
        FROM stg_prompt_events s
        WHERE s.session_id IS NOT NULL AND s.session_id <> ''
        ON CONFLICT (session_id) DO NOTHING
        """
    )

    cur.execute(
        """
        INSERT INTO dim_source (dataset_name, collection_method, version, ingest_timestamp, batch_id)
        SELECT DISTINCT ON (s.dataset_name)
            s.dataset_name,
            s.collection_method,
            s.version,
            s.ingest_timestamp,
            s.batch_id
        FROM stg_prompt_events s
        WHERE s.dataset_name IS NOT NULL AND s.dataset_name <> ''
        ORDER BY s.dataset_name, s.ingest_timestamp DESC NULLS LAST
        ON CONFLICT (dataset_name)
        DO UPDATE SET
            collection_method = EXCLUDED.collection_method,
            version = EXCLUDED.version,
            ingest_timestamp = EXCLUDED.ingest_timestamp,
            batch_id = EXCLUDED.batch_id
        """
    )

    cur.execute(
        """
        INSERT INTO fact_promptexecution (
            conversation_id, turn_number, prompt_key, model_key, task_key, time_key,
            session_key, source_key, response_text, tokens, response_tokens, latency,
            quality_label, success_score
        )
        SELECT
            s.conversation_id,
            s.turn_number,
            p.prompt_key,
            m.model_key,
            t.task_key,
            dt.time_key,
            ds.session_key,
            src.source_key,
            s.response_text,
            s.tokens,
            s.response_tokens,
            s.latency,
            s.quality_label,
            s.success_score
        FROM stg_prompt_events s
        JOIN dim_prompt p
          ON p.prompt_hash = s.prompt_hash
        LEFT JOIN dim_model m
          ON m.model_name = s.model_name
        LEFT JOIN dim_task t
          ON t.task_type IS NOT DISTINCT FROM s.task_type
         AND t.domain IS NOT DISTINCT FROM s.domain
         AND t.language IS NOT DISTINCT FROM s.language
         AND t.programming_lang IS NOT DISTINCT FROM s.programming_lang
         AND t.difficulty IS NOT DISTINCT FROM s.difficulty
         AND t.benchmark_id IS NOT DISTINCT FROM s.benchmark_id
         AND t.category IS NOT DISTINCT FROM s.task_category
        LEFT JOIN dim_session ds
          ON ds.session_id = s.session_id
        LEFT JOIN dim_time dt
          ON dt.ts = s.timestamp
        LEFT JOIN dim_source src
          ON src.dataset_name = s.dataset_name
        WHERE s.prompt_hash IS NOT NULL
        """
    )
    fact_rows = cur.rowcount

    cur.execute("TRUNCATE stg_prompt_events")
    rejected_rows = max(staged_rows - fact_rows, 0)
    return ChunkMergeStats(staged_rows=staged_rows, fact_rows=fact_rows, rejected_rows=rejected_rows)


def merge_comparison_stage(cur) -> ChunkMergeStats:
    cur.execute("ANALYZE stg_model_comparisons")
    cur.execute("SELECT COUNT(*) FROM stg_model_comparisons")
    staged_rows = int(cur.fetchone()[0])
    if staged_rows == 0:
        return ChunkMergeStats()

    _upsert_prompt_dimension(cur, "stg_model_comparisons")

    cur.execute(
        """
        INSERT INTO dim_model (model_name)
        SELECT DISTINCT model_name
        FROM (
            SELECT s.model_a AS model_name FROM stg_model_comparisons s
            UNION
            SELECT s.model_b AS model_name FROM stg_model_comparisons s
            UNION
            SELECT CASE
                WHEN LOWER(s.winner) = 'model_a' THEN s.model_a
                WHEN LOWER(s.winner) = 'model_b' THEN s.model_b
                ELSE NULL
            END AS model_name
            FROM stg_model_comparisons s
        ) models
        WHERE model_name IS NOT NULL AND model_name <> ''
        ON CONFLICT (model_name) DO NOTHING
        """
    )

    cur.execute(
        """
        INSERT INTO dim_time (ts, year, quarter, month, day, day_of_week, week_number, is_weekend)
        SELECT DISTINCT
            s.timestamp,
            EXTRACT(YEAR FROM s.timestamp)::INTEGER,
            EXTRACT(QUARTER FROM s.timestamp)::INTEGER,
            EXTRACT(MONTH FROM s.timestamp)::INTEGER,
            EXTRACT(DAY FROM s.timestamp)::INTEGER,
            EXTRACT(ISODOW FROM s.timestamp)::INTEGER,
            EXTRACT(WEEK FROM s.timestamp)::INTEGER,
            EXTRACT(ISODOW FROM s.timestamp) IN (6, 7)
        FROM stg_model_comparisons s
        WHERE s.timestamp IS NOT NULL
        ON CONFLICT (ts) DO NOTHING
        """
    )

    cur.execute(
        """
        INSERT INTO dim_source (dataset_name, collection_method, version, ingest_timestamp, batch_id)
        SELECT DISTINCT ON (s.dataset_name)
            s.dataset_name,
            s.collection_method,
            s.version,
            s.ingest_timestamp,
            s.batch_id
        FROM stg_model_comparisons s
        WHERE s.dataset_name IS NOT NULL AND s.dataset_name <> ''
        ORDER BY s.dataset_name, s.ingest_timestamp DESC NULLS LAST
        ON CONFLICT (dataset_name)
        DO UPDATE SET
            collection_method = EXCLUDED.collection_method,
            version = EXCLUDED.version,
            ingest_timestamp = EXCLUDED.ingest_timestamp,
            batch_id = EXCLUDED.batch_id
        """
    )

    cur.execute(
        """
        INSERT INTO fact_model_comparison (
            conversation_id, prompt_key, model_a_key, model_b_key, winner_model_key, time_key, source_key
        )
        SELECT
            s.conversation_id,
            p.prompt_key,
            ma.model_key,
            mb.model_key,
            mw.model_key,
            dt.time_key,
            src.source_key
        FROM stg_model_comparisons s
        JOIN dim_prompt p
          ON p.prompt_hash = s.prompt_hash
        JOIN dim_model ma
          ON ma.model_name = s.model_a
        JOIN dim_model mb
          ON mb.model_name = s.model_b
        LEFT JOIN dim_model mw
          ON mw.model_name = CASE
                WHEN LOWER(s.winner) = 'model_a' THEN s.model_a
                WHEN LOWER(s.winner) = 'model_b' THEN s.model_b
                ELSE NULL
             END
        LEFT JOIN dim_time dt
          ON dt.ts = s.timestamp
        LEFT JOIN dim_source src
          ON src.dataset_name = s.dataset_name
        WHERE s.prompt_hash IS NOT NULL
        """
    )
    fact_rows = cur.rowcount

    cur.execute("TRUNCATE stg_model_comparisons")
    rejected_rows = max(staged_rows - fact_rows, 0)
    return ChunkMergeStats(staged_rows=staged_rows, fact_rows=fact_rows, rejected_rows=rejected_rows)


def load_prompts(cur, prompt_path: Path, chunk_size: int, reporter: ProgressReporter | None = None) -> LoadTotals:
    totals = LoadTotals()
    for chunk_number, chunk in enumerate(chunked(iter_jsonl(prompt_path), chunk_size), start=1):
        normalized_chunk, rejected_chunk = prepare_stage_records(chunk, normalize_prompt_record)
        totals.prompt_rows_processed += len(chunk)
        totals.prompt_rows_rejected += rejected_chunk
        if reporter is not None:
            reporter.update(
                phase="copying prompt chunk",
                current_target="prompt_events",
                current_chunk=chunk_number,
                prompt_rows=totals.prompt_rows_processed,
                prompt_fact_rows=totals.prompt_rows_loaded,
                prompt_rejected_rows=totals.prompt_rows_rejected,
            )
        try:
            copy_chunk(cur, "stg_prompt_events", PROMPT_STAGE_COLUMNS, normalized_chunk)
            if reporter is not None:
                reporter.update(
                    phase="merging prompt chunk",
                    current_target="prompt_events",
                    current_chunk=chunk_number,
                    prompt_rows=totals.prompt_rows_processed,
                    prompt_fact_rows=totals.prompt_rows_loaded,
                    prompt_rejected_rows=totals.prompt_rows_rejected,
                )
            merge_stats = merge_prompt_stage(cur)
            totals.prompt_rows_loaded += merge_stats.fact_rows
            totals.prompt_rows_rejected += merge_stats.rejected_rows
            cur.connection.commit()
        except Exception:
            cur.connection.rollback()
            raise
        if reporter is not None:
            reporter.update(
                phase="committed prompt chunk",
                current_target="prompt_events",
                current_chunk=chunk_number,
                prompt_rows=totals.prompt_rows_processed,
                prompt_fact_rows=totals.prompt_rows_loaded,
                prompt_rejected_rows=totals.prompt_rows_rejected,
            )
        print(
            f"[load_streaming][chunk] target=prompt_events chunk={chunk_number} "
            f"processed={len(chunk)} staged={len(normalized_chunk)} "
            f"inserted={merge_stats.fact_rows} rejected={rejected_chunk + merge_stats.rejected_rows} "
            f"cumulative_processed={totals.prompt_rows_processed} "
            f"cumulative_inserted={totals.prompt_rows_loaded} "
            f"cumulative_rejected={totals.prompt_rows_rejected}",
            flush=True,
        )
    return totals


def load_comparisons(
    cur,
    comparison_path: Path,
    chunk_size: int,
    reporter: ProgressReporter | None = None,
) -> LoadTotals:
    totals = LoadTotals()
    for chunk_number, chunk in enumerate(chunked(iter_jsonl(comparison_path), chunk_size), start=1):
        normalized_chunk, rejected_chunk = prepare_stage_records(chunk, normalize_comparison_record)
        totals.comparison_rows_processed += len(chunk)
        totals.comparison_rows_rejected += rejected_chunk
        if reporter is not None:
            reporter.update(
                phase="copying comparison chunk",
                current_target="model_comparisons",
                current_chunk=chunk_number,
                comparison_rows=totals.comparison_rows_processed,
                comparison_fact_rows=totals.comparison_rows_loaded,
                comparison_rejected_rows=totals.comparison_rows_rejected,
            )
        try:
            copy_chunk(cur, "stg_model_comparisons", COMPARISON_STAGE_COLUMNS, normalized_chunk)
            if reporter is not None:
                reporter.update(
                    phase="merging comparison chunk",
                    current_target="model_comparisons",
                    current_chunk=chunk_number,
                    comparison_rows=totals.comparison_rows_processed,
                    comparison_fact_rows=totals.comparison_rows_loaded,
                    comparison_rejected_rows=totals.comparison_rows_rejected,
                )
            merge_stats = merge_comparison_stage(cur)
            totals.comparison_rows_loaded += merge_stats.fact_rows
            totals.comparison_rows_rejected += merge_stats.rejected_rows
            cur.connection.commit()
        except Exception:
            cur.connection.rollback()
            raise
        if reporter is not None:
            reporter.update(
                phase="committed comparison chunk",
                current_target="model_comparisons",
                current_chunk=chunk_number,
                comparison_rows=totals.comparison_rows_processed,
                comparison_fact_rows=totals.comparison_rows_loaded,
                comparison_rejected_rows=totals.comparison_rows_rejected,
            )
        print(
            f"[load_streaming][chunk] target=model_comparisons chunk={chunk_number} "
            f"processed={len(chunk)} staged={len(normalized_chunk)} "
            f"inserted={merge_stats.fact_rows} rejected={rejected_chunk + merge_stats.rejected_rows} "
            f"cumulative_processed={totals.comparison_rows_processed} "
            f"cumulative_inserted={totals.comparison_rows_loaded} "
            f"cumulative_rejected={totals.comparison_rows_rejected}",
            flush=True,
        )
    return totals


def load(
    prompt_input: str | None = None,
    comparisons_input: str | None = None,
    chunk_size: int = COPY_CHUNK_SIZE,
) -> dict[str, int]:
    prompt_path = Path(prompt_input) if prompt_input else DEFAULT_PROMPT_INPUT
    comparison_path = Path(comparisons_input) if comparisons_input else DEFAULT_COMPARISON_INPUT
    if not prompt_path.exists():
        raise FileNotFoundError(f"prompt input file not found: {prompt_path}")

    totals = LoadTotals()
    reporter = ProgressReporter(PROGRESS_INTERVAL_SECONDS)
    conn = get_conn()
    reporter.start()
    try:
        reporter.update(phase="applying schema", current_target="schema")
        apply_schema(conn)
        set_utc_timezone(conn)
        with conn.cursor() as cur:
            reporter.update(phase="creating stage tables", current_target="staging")
            create_stage_tables(cur)
            conn.commit()

            reporter.update(phase="loading prompts", current_target="prompt_events")
            prompt_totals = load_prompts(cur, prompt_path, chunk_size, reporter=reporter)
            totals.prompt_rows_processed = prompt_totals.prompt_rows_processed
            totals.prompt_rows_loaded = prompt_totals.prompt_rows_loaded
            totals.prompt_rows_rejected = prompt_totals.prompt_rows_rejected

            if comparison_path.exists():
                reporter.update(phase="loading comparisons", current_target="model_comparisons")
                comparison_totals = load_comparisons(cur, comparison_path, chunk_size, reporter=reporter)
                totals.comparison_rows_processed = comparison_totals.comparison_rows_processed
                totals.comparison_rows_loaded = comparison_totals.comparison_rows_loaded
                totals.comparison_rows_rejected = comparison_totals.comparison_rows_rejected
            else:
                reporter.update(
                    phase="comparisons file missing, skipping",
                    current_target="model_comparisons",
                    prompt_rows=totals.prompt_rows_processed,
                    prompt_fact_rows=totals.prompt_rows_loaded,
                    prompt_rejected_rows=totals.prompt_rows_rejected,
                )
    except Exception:
        conn.rollback()
        reporter.stop(final_phase="failed")
        raise
    finally:
        conn.close()

    reporter.update(
        phase="finished",
        current_target="database",
        prompt_rows=totals.prompt_rows_processed,
        prompt_fact_rows=totals.prompt_rows_loaded,
        prompt_rejected_rows=totals.prompt_rows_rejected,
        comparison_rows=totals.comparison_rows_processed,
        comparison_fact_rows=totals.comparison_rows_loaded,
        comparison_rejected_rows=totals.comparison_rows_rejected,
    )
    reporter.stop(final_phase="finished")
    return {
        "prompt_rows_processed": totals.prompt_rows_processed,
        "prompt_rows_loaded": totals.prompt_rows_loaded,
        "prompt_rows_rejected": totals.prompt_rows_rejected,
        "comparison_rows_processed": totals.comparison_rows_processed,
        "comparison_rows_loaded": totals.comparison_rows_loaded,
        "comparison_rows_rejected": totals.comparison_rows_rejected,
        "chunk_size": chunk_size,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bulk load PromptLens JSONL outputs into PostgreSQL")
    parser.add_argument("--input", default=None, help="Path to prompt_events.jsonl")
    parser.add_argument("--comparisons-input", default=None, help="Path to model_comparisons.jsonl")
    parser.add_argument("--chunk-size", type=int, default=COPY_CHUNK_SIZE, help="COPY chunk size")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    stats = load(
        prompt_input=args.input,
        comparisons_input=args.comparisons_input,
        chunk_size=args.chunk_size,
    )
    print(json.dumps(stats, indent=2))
