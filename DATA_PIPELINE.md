# Data Pipeline & ETL Architecture

PromptLens is driven by a heavily structured Data Engineering pipeline, ingesting raw multi-source text and mapping it to a highly structured Star Schema designed for OLAP operations.

## ETL Workflow

The ETL logic is isolated within the `etl/` directory and manages a complete end-to-end transformation framework.

```mermaid
flowchart LR
    A[Raw Prompt JSON] --> B[Schema Adapters]
    B --> C[Feature Extractor]
    C --> D[Data Validator]
    D --> E[PostgreSQL Warehouse]

    subgraph Feature Engineering
        C1[Complexity Score]
        C2[Token Estimation]
        C3[Code Detection]
    end

    C -.-> C1
    C -.-> C2
    C -.-> C3
```

### 1. Ingestion (`etl/ingestion/`)
Adapters dynamically load overlapping unstructured text records from sources like Chatbot Arena or ShareGPT, applying base schema alignments.

### 2. Transformation (`etl/transformation/`)
- Extracts over 15 targeted attributes per prompt execution.
- Calculates textual structure properties (`prompt_length`, token volumes).
- Identifies internal logic rules, triggering boolean flags (`contains_code`, `contains_examples`, `contains_constraints`).

### 3. Load & Data Warehousing (`etl/warehouse/`)
Utilizes a PostgreSQL database mapping to a highly structured Star Schema optimized for large-scale aggregations.

## Warehouse Star Schema

The database relies on multidimensional modeling to allow real-time analytical queries via the FastAPI layer.

```mermaid
erDiagram
    FACT_PROMPT_EXECUTION {
        int event_id PK
        int prompt_dim_id FK
        int model_dim_id FK
        float success_score
        float complexity_score
        float latency_ms
        timestamp execution_time
    }

    DIM_PROMPT {
        int prompt_dim_id PK
        string original_text
        int length
        boolean contains_code
        boolean contains_examples
    }

    DIM_MODEL {
        int model_dim_id PK
        string model_name
        string model_version
        string provider
    }

    DIM_LANGUAGE {
        int language_dim_id PK
        string language_name
    }

    FACT_PROMPT_EXECUTION }o--|| DIM_PROMPT : has
    FACT_PROMPT_EXECUTION }o--|| DIM_MODEL : processed_by
    FACT_PROMPT_EXECUTION }o--|| DIM_LANGUAGE : written_in
```

### Materialized Views
Frequently accessed multi-join aggregations are cached as materialized views to serve real-time dashboard analytics with low latency, regularly refreshed by database triggers or cron tasks.
