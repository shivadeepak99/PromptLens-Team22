"""Normalized ETL event types used across dataset adapters."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class PromptEvent:
    """Normalized prompt execution event emitted by dataset adapters."""

    conversation_id: str
    turn_number: int
    prompt_text: str
    timestamp: datetime
    dataset_name: str
    response_text: str | None = None
    model_name: str | None = None
    task_type: str | None = None
    programming_lang: str | None = None
    prompt_type: str | None = None
    language: str | None = None
    task_category: str | None = None
    quality_label: str | None = None
    success_score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ModelComparisonEvent:
    """Normalized model comparison event emitted by arena-style datasets."""

    conversation_id: str
    prompt_text: str
    model_a: str
    model_b: str
    winner: str
    timestamp: datetime
    dataset_name: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
