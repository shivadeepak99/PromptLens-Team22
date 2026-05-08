"""Utilities for cleaning raw records from MongoDB.

The cleaning step enforces the Data Contract: required fields exist and are of the
correct type. Invalid or malformed records are dropped (return None).
"""

from datetime import datetime


REQUIRED_FIELDS = [
    "prompt_text",
    "task_type",
    "model",
    "timestamp",
    "tokens",
    "success_score",
]


def parse_timestamp(ts):
    if isinstance(ts, datetime):
        return ts
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(ts, fmt)
        except Exception:
            continue
    # fallback: let pandas or others handle it if available
    try:
        import dateutil.parser
        return dateutil.parser.parse(ts)
    except Exception:
        return None


def clean_record(rec: dict) -> dict | None:
    """Return cleaned record or None if invalid.

    * Ensure required fields are present.
    * Convert timestamp to datetime.
    * Cast numeric fields to appropriate types.
    * Trim whitespace in strings.
    """
    if not isinstance(rec, dict):
        return None

    for fld in REQUIRED_FIELDS:
        if fld not in rec:
            return None

    # string fields
    rec["prompt_text"] = str(rec.get("prompt_text", "")).strip()
    rec["task_type"] = str(rec.get("task_type", "")).strip()
    rec["model"] = str(rec.get("model", "")).strip()

    # timestamp
    ts = parse_timestamp(rec.get("timestamp"))
    if ts is None:
        return None
    rec["timestamp"] = ts

    # numeric
    try:
        rec["tokens"] = int(rec.get("tokens", 0))
    except Exception:
        rec["tokens"] = None

    try:
        rec["success_score"] = float(rec.get("success_score", 0.0))
    except Exception:
        rec["success_score"] = None

    # optional latency
    if "latency" in rec:
        try:
            rec["latency"] = float(rec.get("latency"))
        except Exception:
            rec["latency"] = None

    # drop if critical numeric missing
    if rec["tokens"] is None or rec["success_score"] is None:
        return None

    return rec

