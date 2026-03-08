"""Task classification helpers for PromptLens adapters."""

from __future__ import annotations

import re


CODE_INTERPRETER_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bsql\b", re.IGNORECASE), "database"),
    (re.compile(r"\bdebug\b", re.IGNORECASE), "debugging"),
    (re.compile(r"\b(write|generate)\s+code\b", re.IGNORECASE), "code_generation"),
    (re.compile(r"\bexplain\b", re.IGNORECASE), "explanation"),
)
GENERIC_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bdebug|fix\b", re.IGNORECASE), "debugging"),
    (re.compile(r"\b(write|generate|create)\b", re.IGNORECASE), "code_generation"),
    (re.compile(r"\bexplain\b", re.IGNORECASE), "explanation"),
    (re.compile(r"\bsql\b", re.IGNORECASE), "database"),
)
NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def normalize_label(value: object, default: str = "unknown") -> str:
    lowered = str(value or "").strip().lower()
    if not lowered:
        return default
    lowered = NON_ALNUM_RE.sub("_", lowered)
    lowered = lowered.strip("_")
    return lowered or default


def classify_code_interpreter_task(text: str | None) -> str:
    content = str(text or "")
    for pattern, label in CODE_INTERPRETER_RULES:
        if pattern.search(content):
            return label
    return "unknown"


def categorize_prompt_library_act(act: object) -> str:
    return normalize_label(act, default="unknown")


def classify_record(rec: dict) -> dict:
    task_type = str(rec.get("task_type") or "").strip().lower()
    if task_type and task_type != "unknown":
        rec["task_type"] = normalize_label(task_type)
        return rec

    content = str(rec.get("prompt_text") or "")
    for pattern, label in GENERIC_RULES:
        if pattern.search(content):
            rec["task_type"] = label
            return rec
    rec["task_type"] = "unknown"
    return rec
