"""Shared fixtures for PromptLens ETL tests."""

from __future__ import annotations

from datetime import datetime, timezone


FIXED_TIMESTAMP = datetime(2026, 3, 7, 12, 0, tzinfo=timezone.utc)


def sharegpt_row() -> dict:
    return {
        "id": "conv-1",
        "conversations": [
            {"from": "human", "value": "Explain recursion with an example."},
            {"from": "gpt", "value": "Recursion is when a function calls itself."},
            {"from": "human", "value": "This prompt should be skipped."},
            {"from": "human", "value": "Act as a Python tutor and explain loops step by step."},
            {"from": "gpt", "value": "Here is a step by step explanation of loops."},
            {"from": "human", "value": "Trailing user turn"},
        ],
    }


def code_interpreter_row() -> dict:
    return {
        "conversations": [
            {"from": "human", "value": "Write code in Python to sort a list."},
            {
                "from": "gpt",
                "value": "```python\nitems = sorted(items)\n```",
            },
        ]
    }


def arena_row() -> dict:
    return {
        "question_id": "arena-42",
        "model_a": "vicuna-13b",
        "model_b": "koala-13b",
        "winner": "model_a",
        "language": "English",
        "turn": 1,
        "tstamp": 1700000000.0,
        "conversation_a": [
            {"role": "user", "content": "Explain quicksort."},
            {"role": "assistant", "content": "Quicksort is divide and conquer."},
        ],
        "conversation_b": [
            {"role": "user", "content": "Explain quicksort."},
            {"role": "assistant", "content": "It is a sorting algorithm."},
        ],
    }


def prompt_library_row() -> dict:
    return {
        "act": "Linux Terminal",
        "prompt": "Act as a Linux terminal and provide an example step by step.",
        "type": "persona",
        "for_devs": True,
        "contributor": "tester",
    }
