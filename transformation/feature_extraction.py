"""Shared feature extraction for PromptLens ETL adapters."""

from __future__ import annotations

import hashlib
import math
import re


WHITESPACE_RE = re.compile(r"\s+")
CODE_BLOCK_RE = re.compile(r"```[\w+-]*\n[\s\S]*?```", re.MULTILINE)
FENCED_LANGUAGE_RE = re.compile(r"```([A-Za-z0-9_+#-]+)")
EXAMPLE_RE = re.compile(r"\bexamples?\b|e\.g\.", re.IGNORECASE)
CONSTRAINT_PATTERNS = [
    re.compile(r"\bstep by step\b", re.IGNORECASE),
    re.compile(r"\bmust\b", re.IGNORECASE),
    re.compile(r"\bshould\b", re.IGNORECASE),
    re.compile(r"\bonly\b", re.IGNORECASE),
    re.compile(r"\bdo not\b", re.IGNORECASE),
]
VERB_RE = re.compile(r"\b(create|generate|fix|write|improve|explain|optimize|convert)\b", re.IGNORECASE)
PROMPT_ROLEPLAY_RE = re.compile(r"\bact as\b", re.IGNORECASE)
LANGUAGE_ALIASES = {
    "english": "en",
    "en": "en",
    "chinese": "zh",
    "mandarin": "zh",
    "zh": "zh",
    "japanese": "ja",
    "ja": "ja",
    "korean": "ko",
    "ko": "ko",
    "french": "fr",
    "fr": "fr",
    "spanish": "es",
    "es": "es",
    "german": "de",
    "de": "de",
    "portuguese": "pt",
    "pt": "pt",
    "hindi": "hi",
    "hi": "hi",
}
PROGRAMMING_LANGUAGE_LABELS = {
    "py": "python",
    "python": "python",
    "javascript": "javascript",
    "js": "javascript",
    "node": "javascript",
    "typescript": "typescript",
    "ts": "typescript",
    "sql": "sql",
    "postgresql": "sql",
    "mysql": "sql",
    "sqlite": "sql",
    "bash": "bash",
    "shell": "bash",
    "sh": "bash",
    "powershell": "powershell",
    "ps1": "powershell",
    "java": "java",
    "c#": "csharp",
    "csharp": "csharp",
    "cpp": "cpp",
    "c++": "cpp",
    "go": "go",
    "golang": "go",
    "rust": "rust",
    "php": "php",
    "ruby": "ruby",
    "html": "html",
    "css": "css",
    "json": "json",
    "yaml": "yaml",
    "yml": "yaml",
    "r": "r",
}
PROGRAMMING_LANGUAGE_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("python", "python"),
    ("javascript", "javascript"),
    ("typescript", "typescript"),
    (" sql ", "sql"),
    ("sql", "sql"),
    ("bash", "bash"),
    ("shell", "bash"),
    ("powershell", "powershell"),
    ("java", "java"),
    ("c++", "cpp"),
    ("cpp", "cpp"),
    ("c#", "csharp"),
    ("golang", "go"),
    (" go ", "go"),
    ("rust", "rust"),
    ("php", "php"),
    ("ruby", "ruby"),
    ("html", "html"),
    ("css", "css"),
    ("json", "json"),
    ("yaml", "yaml"),
)


def normalize_text(text: str | None) -> str:
    """Collapse whitespace for hashing and pattern checks."""
    if text is None:
        return ""
    return WHITESPACE_RE.sub(" ", str(text)).strip()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def estimate_tokens(text: str | None) -> int:
    normalized = normalize_text(text)
    if not normalized:
        return 0
    return math.ceil(len(normalized) / 4)


def contains_code(text: str | None) -> bool:
    return bool(CODE_BLOCK_RE.search(text or ""))


def count_examples(text: str | None) -> int:
    return len(EXAMPLE_RE.findall(text or ""))


def count_constraints(text: str | None) -> int:
    content = text or ""
    return sum(len(pattern.findall(content)) for pattern in CONSTRAINT_PATTERNS)


def detect_prompt_type(text: str | None, source_prompt_type: str | None = None) -> str:
    if PROMPT_ROLEPLAY_RE.search(text or ""):
        return "roleplay"
    if source_prompt_type:
        return normalize_text(source_prompt_type).lower().replace(" ", "_")
    return "standard"


def detect_language(text: str | None, explicit_language: str | None = None) -> str:
    if explicit_language:
        normalized = normalize_text(explicit_language).lower()
        return LANGUAGE_ALIASES.get(normalized, normalized or "unknown")
    candidate = normalize_text(text)
    if not candidate:
        return "unknown"
    try:
        from langdetect import LangDetectException, detect
    except ImportError:
        return "unknown"
    try:
        detected = detect(candidate)
    except LangDetectException:
        return "unknown"
    return detected or "unknown"


def _canonical_programming_language(label: str) -> str | None:
    return PROGRAMMING_LANGUAGE_LABELS.get(label.lower().strip())


def detect_programming_language(prompt_text: str | None, response_text: str | None = None) -> str | None:
    combined = "\n".join(part for part in [prompt_text or "", response_text or ""] if part)
    for label in FENCED_LANGUAGE_RE.findall(combined):
        canonical = _canonical_programming_language(label)
        if canonical:
            return canonical
    lowered = f" {combined.lower()} "
    for keyword, canonical in PROGRAMMING_LANGUAGE_KEYWORDS:
        if keyword in lowered:
            return canonical
    return None


def build_feature_fields(
    prompt_text: str,
    response_text: str | None = None,
    explicit_language: str | None = None,
    source_prompt_type: str | None = None,
) -> dict[str, object]:
    normalized_prompt = normalize_text(prompt_text)
    response = str(response_text).strip() if response_text is not None else None
    prompt_tokens = estimate_tokens(normalized_prompt)
    response_tokens = estimate_tokens(response)
    example_count = count_examples(prompt_text)
    constraint_count = count_constraints(prompt_text)
    complexity_score = (0.4 * prompt_tokens) + (0.3 * constraint_count) + (0.3 * example_count)
    prompt_contains_code = contains_code(prompt_text) or contains_code(response)
    programming_lang = detect_programming_language(prompt_text, response)
    words = normalized_prompt.split()
    instruction_density = len(VERB_RE.findall(normalized_prompt)) / (len(words) or 1)
    prompt_type = detect_prompt_type(prompt_text, source_prompt_type)
    return {
        "prompt_hash": sha256_text(normalized_prompt),
        "prompt_length": len(prompt_text or ""),
        "length": len(prompt_text or ""),
        "token_estimate": prompt_tokens,
        "token_count": prompt_tokens,
        "prompt_type": prompt_type,
        "type": prompt_type,
        "contains_code": prompt_contains_code,
        "contains_examples": example_count > 0,
        "contains_constraints": constraint_count > 0,
        "example_count": example_count,
        "constraint_count": constraint_count,
        "language": detect_language(prompt_text, explicit_language=explicit_language),
        "complexity_score": round(complexity_score, 4),
        "instruction_density": round(instruction_density, 4),
        "response_tokens": response_tokens or None,
        "tokens": prompt_tokens + response_tokens,
        "programming_lang": programming_lang,
    }


def extract_features(rec: dict) -> dict:
    """Attach the shared prompt-level features to a transformed record."""
    prompt_text = str(rec.get("prompt_text") or "").strip()
    response_text = rec.get("response_text")
    explicit_language = rec.get("language")
    prompt_type = rec.get("prompt_type")
    rec["prompt_text"] = prompt_text
    if isinstance(response_text, str):
        rec["response_text"] = response_text.strip()
    features = build_feature_fields(
        prompt_text,
        response_text=response_text if isinstance(response_text, str) else None,
        explicit_language=explicit_language if isinstance(explicit_language, str) else None,
        source_prompt_type=prompt_type if isinstance(prompt_type, str) else None,
    )
    rec.update(features)
    if rec.get("programming_lang") is None and features.get("programming_lang") is not None:
        rec["programming_lang"] = features["programming_lang"]
    return rec
