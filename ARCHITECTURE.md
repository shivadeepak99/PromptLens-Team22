# System Architecture

PromptLens is an enterprise-grade AI analytics platform consisting of decoupled components that handle data ingestion, feature transformation, scalable data warehousing, analytical ML workloads, and RESTful API serving.

## High-Level Platform Architecture

The platform follows a modern Data Engineering topology with distinct boundaries between raw data, processed warehouse, API serving, and user interfaces.

```mermaid
flowchart TD
    subgraph Data Sources
        A1[ShareGPT]
        A2[Chatbot Arena]
        A3[Other Prompt Logs]
    end

    subgraph ETL & Pipeline Layer
        B1[Raw Ingestion / Adapters]
        B2[Feature Extraction Engine]
        B3[Validation & Cleaning]
    end

    subgraph Data Warehouse (PostgreSQL)
        C1[(Star Schema DB)]
        C2[Materialized Views]
        C3[OLAP Indexes]
    end

    subgraph Analytics & ML Layer
        D1[Apriori Mining]
        D2[K-Means Clustering]
        D3[Logistic / RF Baselines]
    end

    subgraph Serving & API Layer
        E1[FastAPI Routes]
        E2[Query Agents]
        E3[ML Model Interfaces]
    end

    subgraph Frontend Client
        F1[Next.js Dashboard]
        F2[React Visualization Components]
    end

    A1 --> B1
    A2 --> B1
    A3 --> B1

    B1 --> B2
    B2 --> B3
    B3 --> C1

    C1 --> C2
    C1 --> D1
    C1 --> D2
    C1 --> D3

    C2 --> E1
    D3 --> E3

    E1 <--> F1
    E3 <--> F1
```

## Component Overview

### 1. Ingestion & Transformation (`/etl`)
Manages the influx of up to 4.6M prompt execution events. Employs a robust Python pipeline that standardizes varying dataset formats, removes sparse null values, and maps textual patterns into strict boolean structure flags (e.g., `contains_code`) and quantitative tokens (`complexity_score`).

### 2. Data Warehouse (`/etl/warehouse`)
Built on a highly optimized PostgreSQL relational instance mapping a classical Star Schema. Centralized around `fact_promptexecution` with connected dimensions, allowing aggregations, materialized views, and rapid OLAP queries against massive volumes of historical prompt behavior.

### 3. ML Analytics (`/analytics`)
Runs continuous insight generation using integrated R and Python scripts. Responsibilities include clustering prompt complexity profiles, utilizing apriori rules to find successful variable subsets, and validating models to understand execution outcomes proactively.

### 4. API & Query Agent (`/api`)
Built using FastAPI for asynchronous, high-throughput data serving. Acts as the interface between the data warehouse, ML inference artifacts, and the user dashboard.

### 5. Frontend UI (`/frontend`)
Next.js React application orchestrating API data into digestible business intelligence charts mapping success metrics, correlation heatmaps, and latency matrices for prompt engineers.
