"""Adapter-driven ETL transformation pipeline for PromptLens datasets."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Iterable, Iterator

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from adapters import get_adapter, iter_dataset_rows, list_supported_datasets, read_dataset_metadata
from feature_extraction import extract_features, sha256_text
from task_classifier import classify_record


DEFAULT_DATASETS_ROOT = CURRENT_DIR.parent / "raw" / "datasets"
DEFAULT_OUTPUT_DIR = CURRENT_DIR.parent / "transformed"


def _batch_id(run_started_at: datetime) -> str:
    return run_started_at.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _serialize_timestamp(value: datetime) -> str:
    aware = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return aware.astimezone(timezone.utc).isoformat()


def _base_source_fields(source_metadata: dict[str, str | None], run_started_at: datetime) -> dict[str, str | None]:
    return {
        "dataset_name": source_metadata["dataset_name"],
        "collection_method": source_metadata.get("collection_method") or "huggingface_disk",
        "version": source_metadata.get("version"),
        "ingest_timestamp": _serialize_timestamp(run_started_at),
        "batch_id": _batch_id(run_started_at),
    }


def prompt_event_to_record(event, source_metadata: dict[str, str | None], run_started_at: datetime) -> dict:
    record = event.to_dict()
    record["session_id"] = sha256_text(event.conversation_id)
    record = extract_features(record)
    record = classify_record(record)
    record["timestamp"] = _serialize_timestamp(event.timestamp)
    record.update(_base_source_fields(source_metadata, run_started_at))
    return record


def comparison_event_to_record(event, source_metadata: dict[str, str | None], run_started_at: datetime) -> dict:
    record = event.to_dict()
    record = extract_features(record)
    record["timestamp"] = _serialize_timestamp(event.timestamp)
    record.update(_base_source_fields(source_metadata, run_started_at))
    return record


def iter_transformed_records(
    dataset_name: str,
    rows: Iterable[dict],
    source_metadata: dict[str, str | None],
    run_started_at: datetime | None = None,
) -> Iterator[tuple[str, dict]]:
    run_started = run_started_at or datetime.now(timezone.utc)
    adapter = get_adapter(dataset_name)
    for row in rows:
        prompt_events, comparison_events = adapter.transform_record(row, default_timestamp=run_started)
        for prompt_event in prompt_events:
            yield "prompt", prompt_event_to_record(prompt_event, source_metadata, run_started)
        for comparison_event in comparison_events:
            yield "comparison", comparison_event_to_record(comparison_event, source_metadata, run_started)


def transform_dataset_rows(
    dataset_name: str,
    rows: Iterable[dict],
    source_metadata: dict[str, str | None] | None = None,
    run_started_at: datetime | None = None,
) -> tuple[list[dict], list[dict]]:
    metadata = source_metadata or {"dataset_name": dataset_name, "collection_method": "fixture", "version": "test"}
    prompt_records: list[dict] = []
    comparison_records: list[dict] = []
    for record_type, record in iter_transformed_records(dataset_name, rows, metadata, run_started_at=run_started_at):
        if record_type == "prompt":
            prompt_records.append(record)
        else:
            comparison_records.append(record)
    return prompt_records, comparison_records


def discover_dataset_paths(datasets_root: Path, selected_datasets: set[str] | None = None) -> list[Path]:
    dataset_paths: list[Path] = []
    for child in sorted(datasets_root.iterdir()):
        if not child.is_dir() or child.name.startswith("_"):
            continue
        if selected_datasets and child.name not in selected_datasets:
            continue
        if child.name in list_supported_datasets():
            dataset_paths.append(child)
    return dataset_paths


def run_pipeline(
    datasets_root: Path = DEFAULT_DATASETS_ROOT,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    selected_datasets: set[str] | None = None,
    limit_per_dataset: int | None = None,
    resume: bool = False,
) -> dict[str, int]:
    """Process all source rows and dump JSONL files.

    If ``resume`` is True and an output file already exists we append to it
    instead of rewriting from scratch; the existing line counts are read into
    ``counts`` so that the printed summary roughly reflects total output.  A
    more robust checkpointing system could track per-dataset offsets, but
    this simple scheme gets you off the ground when a run is interrupted by
    a full disk (as in your earlier error).
    """

    run_started_at = datetime.now(timezone.utc)
    output_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = output_dir / "prompt_events.jsonl"
    comparison_path = output_dir / "model_comparisons.jsonl"
    counts: dict[str, int] = defaultdict(int)

    # determine file mode and pre‑populate existing counts when resuming
    mode = "a" if resume else "w"
    if resume:
        if prompt_path.exists():
            counts["prompt_output"] = sum(1 for _ in prompt_path.open("r", encoding="utf-8"))
        if comparison_path.exists():
            counts["comparison_output"] = sum(1 for _ in comparison_path.open("r", encoding="utf-8"))

    with prompt_path.open(mode, encoding="utf-8") as prompt_out, comparison_path.open(mode, encoding="utf-8") as comparison_out:
        for dataset_path in discover_dataset_paths(datasets_root, selected_datasets):
            source_metadata = read_dataset_metadata(dataset_path, dataset_path.name)
            rows = iter_dataset_rows(dataset_path, limit=limit_per_dataset)
            for record_type, record in iter_transformed_records(
                dataset_path.name,
                rows,
                source_metadata,
                run_started_at=run_started_at,
            ):
                target = prompt_out if record_type == "prompt" else comparison_out
                target.write(json.dumps(record, ensure_ascii=False) + "\n")
                counts[f"{dataset_path.name}:{record_type}"] += 1

    counts["prompt_output"] = sum(value for key, value in counts.items() if key.endswith(":prompt"))
    counts["comparison_output"] = sum(value for key, value in counts.items() if key.endswith(":comparison"))
    return dict(counts)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run PromptLens adapter-based ETL transformation")
    parser.add_argument(
        "--datasets-root",
        default=str(DEFAULT_DATASETS_ROOT),
        help="Path to the raw/datasets directory",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory where transformed JSONL files will be written",
    )
    parser.add_argument(
        "--dataset",
        action="append",
        dest="datasets",
        help="Optional dataset folder name to process; may be repeated",
    )
    parser.add_argument(
        "--limit-per-dataset",
        type=int,
        help="Limit the number of source rows processed per dataset",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Append to existing output files instead of overwriting",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    counts = run_pipeline(
        datasets_root=Path(args.datasets_root),
        output_dir=Path(args.output_dir),
        selected_datasets=set(args.datasets) if args.datasets else None,
        limit_per_dataset=args.limit_per_dataset,
        resume=args.resume,
    )
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
