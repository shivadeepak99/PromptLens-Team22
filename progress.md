# PromptLens Progress Report

## Snapshot

Status as of 2026-03-07:

- The new adapter-driven ETL pipeline is implemented in code.
- The four requested dataset adapters are implemented.
- Shared feature extraction, validation, warehouse DDL, and a staged PostgreSQL loader are implemented.
- Unit tests are passing.
- A real smoke run against the local Hugging Face disk datasets succeeded with a small sample.
- The full production load into a real PostgreSQL database has **not** been executed yet.

This means the project is **past planning and into working code**, but it is **not fully end-to-end proven in a real warehouse environment yet**.

## What Is Fully Implemented

### 1. Adapter-driven transformation pipeline

Implemented:

- Scan `raw/datasets`
- Select the correct adapter by dataset folder name
- Transform source rows into normalized prompt events
- Emit model comparison events for `chatbot_arena`
- Write transformed outputs as JSONL files

Current entrypoint:

- `transformation/run_pipeline.py`

### 2. Dataset adapters

Implemented adapters:

- `sharegpt_conversation_chronicles`
- `sharegpt_code_interpreter`
- `chatbot_arena`
- `prompt_library`

Implemented behaviors:

- ShareGPT adjacent `human -> gpt` pairing
- Code Interpreter task type rules
- Code language detection
- Chatbot Arena two prompt facts plus one comparison fact
- Prompt Library task/category/prompt type mapping

### 3. Shared feature extraction

Implemented:

- `prompt_hash`
- `prompt_length`
- `token_estimate`
- `response_tokens`
- `tokens`
- `contains_code`
- `contains_examples`
- `contains_constraints`
- `prompt_type`
- `language`
- `complexity_score`
- `instruction_density`

### 4. Validation

Implemented:

- prompt event record validation
- model comparison record validation
- JSONL file validation helpers

### 5. Warehouse layer

Implemented:

- expanded `dim_prompt`
- expanded `dim_task`
- expanded `fact_promptexecution`
- new `fact_model_comparison`
- staged in-memory deduplication before load
- dimension upsert logic
- fact insert logic

### 6. Tests and local verification

Implemented and verified:

- `unittest` suite for adapters, validation, and warehouse staging
- smoke transformation run against the real local datasets with `--limit-per-dataset 1`
- smoke outputs validated successfully

Verified results:

- `9/9` tests passing
- smoke run produced `11` prompt records and `1` comparison record
- smoke outputs validated as `11/11` valid prompt rows and `1/1` valid comparison rows

## What Each Important File Does

### Transformation

- `transformation/pipeline_types.py`
  - Defines normalized internal event types:
    - `PromptEvent`
    - `ModelComparisonEvent`

- `transformation/adapters.py`
  - Holds the adapter registry
  - Implements dataset-specific transformation logic
  - Loads Hugging Face datasets from disk with `load_from_disk`

- `transformation/feature_extraction.py`
  - Computes all shared prompt features
  - Handles token estimation, hashing, prompt type, regex flags, and language/programming language detection

- `transformation/task_classifier.py`
  - Handles task type normalization
  - Contains Code Interpreter task rules
  - Normalizes Prompt Library `act` values

- `transformation/run_pipeline.py`
  - Main ETL transformation entrypoint
  - Scans datasets, runs adapters, applies features/classification, and writes:
    - `prompt_events.jsonl`
    - `model_comparisons.jsonl`

### Validation

- `validation/validation_checks.py`
  - Validates transformed prompt event and comparison records
  - Validates JSONL output files

### Warehouse

- `warehouse/schema.sql`
  - Current warehouse DDL for the expanded star schema

- `warehouse/load_to_postgres.py`
  - Reads transformed JSONL files
  - Stages/deduplicates dimensions in memory
  - Loads dimensions and facts into PostgreSQL

### Tests

- `tests/fixtures.py`
  - Small deterministic fixture rows for all four datasets

- `tests/test_transformation.py`
  - Adapter behavior tests
  - Arena winner/tie/both-bad coverage

- `tests/test_validation.py`
  - Validation tests

- `tests/test_warehouse_loader.py`
  - Staging and deduplication tests across all dataset types

### Smoke output

- `transformed_smoke/prompt_events.jsonl`
  - Real sample output from the new pipeline

- `transformed_smoke/model_comparisons.jsonl`
  - Real sample comparison output from the new pipeline

## Honest Current State

### Working now

- The new transformation pipeline works.
- The adapter mapping logic is implemented.
- The local tests pass.
- The pipeline can read the real local Hugging Face disk datasets and emit valid transformed outputs.

### Not yet proven

- The PostgreSQL loader has **not** been run against a live database in this workspace.
- The new schema has **not** been applied to a real PostgreSQL instance here.
- Final warehouse row counts for the full datasets have **not** been produced yet.
- No performance run on the full corpus has been done yet.

### Legacy / stale parts still in the repo

- `ingestion/ingest_to_mongodb.py`
  - Old raw MongoDB ingestion script
  - Still present, but not part of the new primary ETL flow

- `transformation/clean_data.py`
  - Old generic cleaning logic from the previous pipeline
  - Still present, but not wired into the new adapter-driven path

- `transformed.json`
  - Old output artifact from the earlier pipeline style
  - Not the current target output format

This means the repo is currently in a **mixed state**:

- new ETL path = implemented and active
- old Mongo/generic path = still present as legacy code/artifacts

## Where We Are Right Now

Current phase:

- **Implementation complete for the transformation/staging layer**
- **Ready for real warehouse integration testing**

Practically, the next real milestone is:

1. Apply `warehouse/schema.sql` to PostgreSQL
2. Run the new ETL pipeline on a meaningful dataset slice
3. Run `warehouse/load_to_postgres.py` against that database
4. Verify real dimension/fact counts and spot-check loaded rows
5. Decide whether to remove or archive the old Mongo-based files

## Recommended Immediate Next Steps

- Run the new schema on PostgreSQL
- Execute a small real load first, not the full corpus immediately
- Validate row counts in:
  - `dim_prompt`
  - `dim_model`
  - `dim_task`
  - `dim_source`
  - `fact_promptexecution`
  - `fact_model_comparison`
- If that passes, run the full ETL
- Then clean up legacy files if they are no longer needed
