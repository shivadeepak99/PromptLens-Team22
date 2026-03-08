# PromptLens Adapter ETL Data Contract

The adapter-driven ETL produces two newline-delimited JSON outputs:

1. `prompt_events.jsonl`
2. `model_comparisons.jsonl`

## Prompt Event Contract

| Field Name | Type | Description | Nullable |
|------------|------|-------------|----------|
| `conversation_id` | TEXT | Stable source conversation/question identifier | No |
| `turn_number` | INTEGER | Event turn index within the conversation | No |
| `prompt_text` | TEXT | Prompt content used for the event | No |
| `prompt_hash` | CHAR(64) | SHA-256 hash of normalized prompt text | No |
| `prompt_length` | INTEGER | Prompt character length | No |
| `token_estimate` | INTEGER | Estimated prompt tokens using `ceil(len/4)` | No |
| `prompt_type` | VARCHAR | Derived prompt type such as `roleplay` or `standard` | No |
| `contains_code` | BOOLEAN | Prompt or response contains a fenced code block | No |
| `contains_examples` | BOOLEAN | Prompt contains example-oriented phrasing | No |
| `contains_constraints` | BOOLEAN | Prompt contains constraint-oriented phrasing | No |
| `language` | VARCHAR | Source language or detected fallback | No |
| `complexity_score` | FLOAT | Weighted score from token estimate, constraints, and examples | No |
| `response_text` | TEXT | Response content for the event | Yes |
| `response_tokens` | INTEGER | Estimated response tokens | Yes |
| `tokens` | INTEGER | Total estimated tokens across prompt and response | No |
| `model_name` | VARCHAR | Model identifier if provided by the source | Yes |
| `task_type` | VARCHAR | Canonical task type | Yes |
| `programming_lang` | VARCHAR | Canonical programming language when detected | Yes |
| `task_category` | VARCHAR | Optional task category such as `developer` | Yes |
| `quality_label` | VARCHAR | Arena-style label such as `winner`, `loser`, `tie` | Yes |
| `success_score` | FLOAT | Objective score when the source provides one | Yes |
| `timestamp` | TIMESTAMP | Event timestamp in UTC ISO-8601 form | No |
| `session_id` | CHAR(64) | SHA-256 hash of `conversation_id` | No |
| `dataset_name` | VARCHAR | Source dataset folder name | No |
| `collection_method` | VARCHAR | Source ingestion method metadata | No |
| `version` | VARCHAR | Source dataset version metadata | Yes |
| `ingest_timestamp` | TIMESTAMP | ETL run ingestion timestamp | No |
| `batch_id` | VARCHAR | ETL batch identifier | No |

## Model Comparison Contract

| Field Name | Type | Description | Nullable |
|------------|------|-------------|----------|
| `conversation_id` | TEXT | Stable question/comparison identifier | No |
| `prompt_text` | TEXT | Shared prompt text for the comparison | No |
| `prompt_hash` | CHAR(64) | SHA-256 hash of normalized prompt text | No |
| `prompt_length` | INTEGER | Prompt character length | No |
| `token_estimate` | INTEGER | Estimated prompt tokens | No |
| `prompt_type` | VARCHAR | Derived prompt type | No |
| `contains_code` | BOOLEAN | Prompt contains code | No |
| `contains_examples` | BOOLEAN | Prompt contains examples | No |
| `contains_constraints` | BOOLEAN | Prompt contains constraints | No |
| `language` | VARCHAR | Source language or detected fallback | No |
| `complexity_score` | FLOAT | Prompt complexity score | No |
| `model_a` | VARCHAR | Left-side model identifier | No |
| `model_b` | VARCHAR | Right-side model identifier | No |
| `winner` | VARCHAR | Raw winner label from the source | No |
| `timestamp` | TIMESTAMP | Comparison timestamp in UTC ISO-8601 form | No |
| `dataset_name` | VARCHAR | Source dataset folder name | No |
| `collection_method` | VARCHAR | Source ingestion method metadata | No |
| `version` | VARCHAR | Source dataset version metadata | Yes |
| `ingest_timestamp` | TIMESTAMP | ETL run ingestion timestamp | No |
| `batch_id` | VARCHAR | ETL batch identifier | No |
