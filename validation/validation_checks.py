"""Validation utilities for PromptLens transformed records."""

from __future__ import annotations

from datetime import datetime
import json


PROMPT_REQUIRED_FIELDS = [
    "conversation_id",
    "turn_number",
    "prompt_text",
    "prompt_hash",
    "prompt_length",
    "token_estimate",
    "timestamp",
    "dataset_name",
    "tokens",
]
COMPARISON_REQUIRED_FIELDS = [
    "conversation_id",
    "prompt_text",
    "prompt_hash",
    "timestamp",
    "dataset_name",
    "model_a",
    "model_b",
    "winner",
]


def _is_timestamp(value: object) -> bool:
    if isinstance(value, datetime):
        return True
    if not isinstance(value, str):
        return False
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        datetime.fromisoformat(candidate)
    except ValueError:
        return False
    return True


def validate_prompt_record(rec: dict) -> bool:
    if not isinstance(rec, dict):
        return False
    for field in PROMPT_REQUIRED_FIELDS:
        if field not in rec:
            return False
    if not isinstance(rec.get("conversation_id"), str) or not rec["conversation_id"].strip():
        return False
    if not isinstance(rec.get("prompt_text"), str) or not rec["prompt_text"].strip():
        return False
    if not isinstance(rec.get("prompt_hash"), str) or len(rec["prompt_hash"]) != 64:
        return False
    if not isinstance(rec.get("dataset_name"), str) or not rec["dataset_name"].strip():
        return False
    if not _is_timestamp(rec.get("timestamp")):
        return False
    try:
        int(rec.get("turn_number"))
        int(rec.get("prompt_length"))
        int(rec.get("token_estimate"))
        int(rec.get("tokens"))
    except (TypeError, ValueError):
        return False
    response_tokens = rec.get("response_tokens")
    if response_tokens is not None:
        try:
            int(response_tokens)
        except (TypeError, ValueError):
            return False
    success_score = rec.get("success_score")
    if success_score is not None:
        try:
            float(success_score)
        except (TypeError, ValueError):
            return False
    return True


def validate_comparison_record(rec: dict) -> bool:
    if not isinstance(rec, dict):
        return False
    for field in COMPARISON_REQUIRED_FIELDS:
        if field not in rec:
            return False
    if not isinstance(rec.get("prompt_text"), str) or not rec["prompt_text"].strip():
        return False
    if not isinstance(rec.get("model_a"), str) or not rec["model_a"].strip():
        return False
    if not isinstance(rec.get("model_b"), str) or not rec["model_b"].strip():
        return False
    if not _is_timestamp(rec.get("timestamp")):
        return False
    return True


def validate_file(path: str, record_type: str = "prompt") -> dict:
    """Scan a newline-delimited JSON file and report prompt/comparison validity."""
    validator = validate_prompt_record if record_type == "prompt" else validate_comparison_record
    total = valid = invalid = 0
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            total += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                invalid += 1
                continue
            if validator(record):
                valid += 1
            else:
                invalid += 1
    return {"total": total, "valid": valid, "invalid": invalid}
