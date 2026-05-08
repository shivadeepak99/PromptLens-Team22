"""Dataset adapters for PromptLens Hugging Face disk datasets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Iterable, Iterator

from feature_extraction import detect_programming_language, normalize_text, sha256_text
from pipeline_types import ModelComparisonEvent, PromptEvent
from task_classifier import categorize_prompt_library_act, classify_code_interpreter_task


USER_ROLES = {"human", "user"}
ASSISTANT_ROLES = {"gpt", "assistant", "bot"}


def _normalize_role(role: object) -> str:
    return str(role or "").strip().lower()


def _message_value(message: dict, text_key: str) -> str:
    return str(message.get(text_key) or "").strip()


def _ensure_datetime(value: object, default: datetime) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return default
        if cleaned.endswith("Z"):
            cleaned = cleaned[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(cleaned)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return default
    return default


def _adjacent_pairs(
    messages: list[dict],
    role_key: str = "from",
    text_key: str = "value",
) -> Iterator[tuple[int, str, str]]:
    turn_number = 0
    for index in range(len(messages) - 1):
        current = messages[index]
        following = messages[index + 1]
        current_role = _normalize_role(current.get(role_key))
        following_role = _normalize_role(following.get(role_key))
        if current_role in USER_ROLES and following_role in ASSISTANT_ROLES:
            prompt_text = _message_value(current, text_key)
            response_text = _message_value(following, text_key)
            if not prompt_text:
                continue
            turn_number += 1
            yield turn_number, prompt_text, response_text


def _first_user_message(messages: list[dict], role_key: str, text_key: str) -> str:
    for message in messages:
        if _normalize_role(message.get(role_key)) in USER_ROLES:
            prompt_text = _message_value(message, text_key)
            if prompt_text:
                return prompt_text
    return ""


def _assistant_transcript(messages: list[dict], role_key: str, text_key: str) -> str:
    parts: list[str] = []
    for message in messages:
        if _normalize_role(message.get(role_key)) in ASSISTANT_ROLES:
            content = _message_value(message, text_key)
            if content:
                parts.append(content)
    return "\n\n".join(parts)


def _hash_conversation(dataset_name: str, conversations: object) -> str:
    payload = json.dumps(conversations, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(f"{dataset_name}:{payload}".encode("utf-8")).hexdigest()
    return digest


def _winner_side(winner: object) -> str:
    return str(winner or "").strip().lower()


def _arena_outcomes(winner: object) -> tuple[str, str, float | None, float | None]:
    side = _winner_side(winner)
    if side == "model_a":
        return "winner", "loser", 1.0, 0.0
    if side == "model_b":
        return "loser", "winner", 0.0, 1.0
    if side in {"tie", "draw"}:
        return "tie", "tie", 0.5, 0.5
    if "bothbad" in side.replace(" ", ""):
        return "both_bad", "both_bad", 0.0, 0.0
    return "unknown", "unknown", None, None


@dataclass(slots=True)
class DatasetAdapter:
    dataset_name: str

    def transform_record(
        self,
        row: dict,
        default_timestamp: datetime,
    ) -> tuple[list[PromptEvent], list[ModelComparisonEvent]]:
        raise NotImplementedError


@dataclass(slots=True)
class ShareGPTConversationAdapter(DatasetAdapter):
    def transform_record(
        self,
        row: dict,
        default_timestamp: datetime,
    ) -> tuple[list[PromptEvent], list[ModelComparisonEvent]]:
        conversation_id = str(row.get("id") or _hash_conversation(self.dataset_name, row.get("conversations")))
        prompts: list[PromptEvent] = []
        messages = list(row.get("conversations") or [])
        for turn_number, prompt_text, response_text in _adjacent_pairs(messages):
            prompts.append(
                PromptEvent(
                    conversation_id=conversation_id,
                    turn_number=turn_number,
                    prompt_text=prompt_text,
                    response_text=response_text or None,
                    timestamp=default_timestamp,
                    dataset_name=self.dataset_name,
                )
            )
        return prompts, []


@dataclass(slots=True)
class ShareGPTCodeInterpreterAdapter(DatasetAdapter):
    def transform_record(
        self,
        row: dict,
        default_timestamp: datetime,
    ) -> tuple[list[PromptEvent], list[ModelComparisonEvent]]:
        messages = list(row.get("conversations") or [])
        conversation_id = _hash_conversation(self.dataset_name, messages)
        prompts: list[PromptEvent] = []
        for turn_number, prompt_text, response_text in _adjacent_pairs(messages):
            task_type = classify_code_interpreter_task(prompt_text)
            programming_lang = detect_programming_language(prompt_text, response_text)
            prompts.append(
                PromptEvent(
                    conversation_id=conversation_id,
                    turn_number=turn_number,
                    prompt_text=prompt_text,
                    response_text=response_text or None,
                    timestamp=default_timestamp,
                    dataset_name=self.dataset_name,
                    task_type=task_type,
                    programming_lang=programming_lang,
                )
            )
        return prompts, []


@dataclass(slots=True)
class ChatbotArenaAdapter(DatasetAdapter):
    def transform_record(
        self,
        row: dict,
        default_timestamp: datetime,
    ) -> tuple[list[PromptEvent], list[ModelComparisonEvent]]:
        timestamp = _ensure_datetime(row.get("tstamp"), default_timestamp)
        conversation_id = str(row.get("question_id") or _hash_conversation(self.dataset_name, row))
        conversation_a = list(row.get("conversation_a") or [])
        conversation_b = list(row.get("conversation_b") or [])
        prompt_text = _first_user_message(conversation_a, "role", "content") or _first_user_message(
            conversation_b,
            "role",
            "content",
        )
        if not prompt_text:
            return [], []
        response_a = _assistant_transcript(conversation_a, "role", "content")
        response_b = _assistant_transcript(conversation_b, "role", "content")
        quality_a, quality_b, score_a, score_b = _arena_outcomes(row.get("winner"))
        turn_number = int(row.get("turn") or 1)
        language = str(row.get("language") or "").strip() or None
        prompts = [
            PromptEvent(
                conversation_id=conversation_id,
                turn_number=turn_number,
                prompt_text=prompt_text,
                response_text=response_a or None,
                timestamp=timestamp,
                dataset_name=self.dataset_name,
                model_name=str(row.get("model_a") or "").strip() or None,
                language=language,
                quality_label=quality_a,
                success_score=score_a,
            ),
            PromptEvent(
                conversation_id=conversation_id,
                turn_number=turn_number,
                prompt_text=prompt_text,
                response_text=response_b or None,
                timestamp=timestamp,
                dataset_name=self.dataset_name,
                model_name=str(row.get("model_b") or "").strip() or None,
                language=language,
                quality_label=quality_b,
                success_score=score_b,
            ),
        ]
        comparisons = [
            ModelComparisonEvent(
                conversation_id=conversation_id,
                prompt_text=prompt_text,
                model_a=str(row.get("model_a") or "").strip(),
                model_b=str(row.get("model_b") or "").strip(),
                winner=str(row.get("winner") or "").strip(),
                timestamp=timestamp,
                dataset_name=self.dataset_name,
            )
        ]
        return prompts, comparisons


@dataclass(slots=True)
class PromptLibraryAdapter(DatasetAdapter):
    def transform_record(
        self,
        row: dict,
        default_timestamp: datetime,
    ) -> tuple[list[PromptEvent], list[ModelComparisonEvent]]:
        prompt_text = str(row.get("prompt") or "").strip()
        if not prompt_text:
            return [], []
        prompt_hash = sha256_text(normalize_text(prompt_text))
        task_category = "developer" if bool(row.get("for_devs")) else "general"
        event = PromptEvent(
            conversation_id=f"{self.dataset_name}:{prompt_hash}",
            turn_number=1,
            prompt_text=prompt_text,
            timestamp=default_timestamp,
            dataset_name=self.dataset_name,
            task_type=categorize_prompt_library_act(row.get("act")),
            prompt_type=str(row.get("type") or "").strip() or None,
            task_category=task_category,
        )
        return [event], []


ADAPTER_REGISTRY: dict[str, DatasetAdapter] = {
    "sharegpt_conversation_chronicles": ShareGPTConversationAdapter("sharegpt_conversation_chronicles"),
    "sharegpt_code_interpreter": ShareGPTCodeInterpreterAdapter("sharegpt_code_interpreter"),
    "chatbot_arena": ChatbotArenaAdapter("chatbot_arena"),
    "prompt_library": PromptLibraryAdapter("prompt_library"),
}


def get_adapter(dataset_name: str) -> DatasetAdapter:
    try:
        return ADAPTER_REGISTRY[dataset_name]
    except KeyError as exc:
        raise ValueError(f"No adapter registered for dataset '{dataset_name}'") from exc


def list_supported_datasets() -> list[str]:
    return sorted(ADAPTER_REGISTRY)


def read_dataset_metadata(dataset_path: str | Path, dataset_name: str) -> dict[str, str | None]:
    metadata_path = Path(dataset_path) / "train" / "dataset_info.json"
    payload: dict = {}
    if metadata_path.exists():
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    version = payload.get("version", {})
    return {
        "dataset_name": dataset_name,
        "collection_method": "huggingface_disk",
        "version": version.get("version_str") if isinstance(version, dict) else None,
    }


def iter_dataset_rows(dataset_path: str | Path, limit: int | None = None) -> Iterable[dict]:
    try:
        from datasets import load_from_disk
    except ImportError as exc:
        raise RuntimeError(
            "The 'datasets' package is required to load Hugging Face disk datasets. "
            "Install dependencies from requirements.txt before running the ETL."
        ) from exc

    dataset = load_from_disk(str(dataset_path))
    if isinstance(dataset, dict) and "train" in dataset:
        dataset = dataset["train"]
    elif hasattr(dataset, "keys") and "train" in dataset:
        dataset = dataset["train"]

    count = len(dataset) if hasattr(dataset, "__len__") else None
    upper_bound = count if limit is None or count is None else min(limit, count)
    if upper_bound is not None and hasattr(dataset, "select"):
        dataset = dataset.select(range(upper_bound))
    for row in dataset:
        yield dict(row)
