from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SortOrder(str, Enum):
	asc = "asc"
	desc = "desc"


class ModelPerformanceSortBy(str, Enum):
	avg_success = "avg_success"
	attempts = "attempts"
	median_success = "median_success"


class LanguagePerformanceSortBy(str, Enum):
	success_rate = "success_rate"
	prompts = "prompts"
	median_success = "median_success"


class PromptFeatureSortBy(str, Enum):
	avg_success = "avg_success"
	cnt = "cnt"
	median_success = "median_success"


class TopPromptsSortBy(str, Enum):
	avg_success = "avg_success"
	uses = "uses"
	median_success = "median_success"


class ErrorDetails(BaseModel):
	code: str
	message: str


class ApiEnvelope(BaseModel):
	timestamp: str
	status: str
	data: dict[str, Any] | list[Any] | None = None
	error: ErrorDetails | None = None


class FeatureFlags(BaseModel):
	contains_examples: bool
	contains_code: bool
	contains_constraints: bool


class DateRange(BaseModel):
	start: str
	end: str


class TimelinePoint(BaseModel):
	date: str
	series: list[dict[str, Any]] = Field(default_factory=list)
