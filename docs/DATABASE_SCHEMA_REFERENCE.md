# Database Architecture & Schema Reference

## Overview

This document is the authoritative reference for the PostgreSQL database used by the PromptLens project. It covers the star schema, materialized views, and indexes available for analytics.

**Database**: `promptlens` (PostgreSQL)  
**Status**: Phase 1 OLAP complete (indexes + materialized views deployed)  
**Location**: Docker container `promptlens-postgres`  
**Data Completeness**: 200K+ fact records, fully populated

---

## Connection Details

### Local Development Connection

```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="promptlens",
    user="postgres",
    password="<password>"
)

cursor = conn.cursor()
cursor.execute("SELECT version();")
print(cursor.fetchone())
```

### Docker Environment Connection

```bash
# From host machine
docker exec -t promptlens-postgres psql -U postgres -d promptlens -c "SELECT * FROM mv_model_performance_arena;"

# Or from within docker compose network
docker exec -it promptlens-postgres /bin/bash
psql -U postgres -d promptlens
```

### Connection Strings

- **SQLAlchemy**: `postgresql+psycopg2://postgres:PASSWORD@localhost:5432/promptlens`
- **SQLAlchemy (async)**: `postgresql+asyncpg://postgres:PASSWORD@localhost:5432/promptlens`
- **psycopg2**: `host=localhost port=5432 dbname=promptlens user=postgres password=PASSWORD`

---

## Star Schema (8 Tables)

### Entity-Relationship Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                   DIMENSION TABLES (6)                       │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  dim_prompt              dim_model           dim_task       │
│  ├─ prompt_key (PK)      ├─ model_key (PK)   ├─ task_key    │
│  ├─ prompt_hash          ├─ model_name       ├─ task_category
│  ├─ prompt_text          ├─ model_version    ├─ difficulty  │
│  ├─ contains_examples    └─ provider         └─ domain      │
│  ├─ contains_code                                           │
│  └─ contains_constraints  dim_time           dim_session    │
│                          ├─ time_key         ├─ session_key │
│  dim_source             ├─ ts (timestamp)   ├─ session_id  │
│  ├─ source_key          ├─ year             ├─ user_id     │
│  ├─ dataset_name        ├─ month            └─ duration    │
│  ├─ source_url          ├─ day                             │
│  └─ version             └─ hour              dim_source     │
│                                             continuation ->│
│                                                              │
└──────────────────────────────────────────────────────────────┘
            │               │                │      │
            │ (FK)          │ (FK)          │ (FK) │ (FK)
            │               │                │      │
            ▼               ▼                ▼      ▼
┌──────────────────────────────────────────────────────────────┐
│              FACT TABLES (2)                                 │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  fact_promptexecution (200K+ rows)                          │
│  ├─ execution_id (PK)                                       │
│  ├─ prompt_key (FK) ──────→ dim_prompt                      │
│  ├─ model_key (FK) ─────────→ dim_model                     │
│  ├─ task_key (FK) ──────────→ dim_task                      │
│  ├─ time_key (FK) ─────────→ dim_time                       │
│  ├─ session_key (FK) ────────→ dim_session                  │
│  ├─ source_key (FK) ────────→ dim_source                    │
│  ├─ success_flag (BOOLEAN)                                  │
│  ├─ success_score (NUMERIC 0-1)                             │
│  ├─ latency_ms (INTEGER)                                    │
│  ├─ tokens_used (INTEGER)                                   │
│  └─ created_at (TIMESTAMP)                                  │
│                                                              │
│  fact_model_comparison (50K+ rows)                          │
│  ├─ comparison_id (PK)                                      │
│  ├─ time_key (FK) ────────→ dim_time                        │
│  ├─ source_key (FK) ────────→ dim_source                    │
│  ├─ model_a_key (FK) ────────→ dim_model                    │
│  ├─ model_b_key (FK) ────────→ dim_model                    │
│  ├─ winner_model_key (FK) ──→ dim_model                     │
│  ├─ competitiveness_score (NUMERIC)                         │
│  └─ created_at (TIMESTAMP)                                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Dimension Tables

### dim_prompt
Unique prompts (or prompt templates)

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| prompt_key | SERIAL | PK | Surrogate key |
| prompt_hash | VARCHAR(64) | UNIQUE | SHA256 hash of prompt |
| prompt_text | TEXT | | First 500 chars or full prompt |
| contains_examples | BOOLEAN | | Has code examples |
| contains_code | BOOLEAN | | Has code snippets |
| contains_constraints | BOOLEAN | | Has constraints/requirements |
| created_at | TIMESTAMP | | Row creation time |

**Size**: ~2,341 rows (unique templates/variations)

---

### dim_model
Unique AI models tested

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| model_key | SERIAL | PK | Surrogate key |
| model_name | VARCHAR(100) | UNIQUE | gpt-4, claude-v1, etc. |
| model_version | VARCHAR(50) | | Model version/variant |
| provider | VARCHAR(50) | | OpenAI, Anthropic, etc. |
| created_at | TIMESTAMP | | Row creation time |

**Size**: ~15 rows

**Sample Data**:
- gpt-4 (OpenaI)
- gpt-3.5-turbo (OpenAI)
- claude-v1 (Anthropic)
- claude-instant-v1 (Anthropic)
- vicuna-13b (Open source)

---

### dim_task
Programming tasks/categories

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| task_key | SERIAL | PK | Surrogate key |
| task_category | VARCHAR(100) | | Task type (code_generation, bug_fix, etc.) |
| programming_lang | VARCHAR(50) | | python, java, sql, javascript, etc. |
| difficulty | VARCHAR(20) | | easy, medium, hard |
| domain | VARCHAR(100) | | data_processing, web, system_design, etc. |
| created_at | TIMESTAMP | | Row creation time |

**Size**: ~12 rows

**Sample Data**:
- Category: code_generation, Language: python, Difficulty: medium, Domain: data_processing
- Category: bug_fix, Language: javascript, Difficulty: hard, Domain: web
- Category: sql_query, Language: sql, Difficulty: easy, Domain: database

---

### dim_time
Time dimension for temporal analytics

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| time_key | SERIAL | PK | Surrogate key |
| ts | TIMESTAMP | UNIQUE | Full timestamp |
| year | INTEGER | | Year (2023, 2024, etc.) |
| month | INTEGER | | Month (1-12) |
| day | DATE | | Date (YYYY-MM-DD) |
| hour | INTEGER | | Hour (0-23) |
| day_of_week | INTEGER | | 0=Sun, 6=Sat |
| week_of_year | INTEGER | | Week number (1-53) |
| is_weekend | BOOLEAN | | True if Sat/Sun |

**Size**: ~5,000+ rows (one per hour tested)

---

### dim_session
User sessions / execution batches

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| session_key | SERIAL | PK | Surrogate key |
| session_id | VARCHAR(100) | UNIQUE | Unique session identifier |
| user_id | VARCHAR(100) | | User or batch identifier |
| duration_seconds | INTEGER | | How long session lasted |
| prompt_count | INTEGER | | How many prompts in session |
| created_at | TIMESTAMP | | Session start time |

**Size**: ~500+ rows (batches of prompts)

---

### dim_source
Dataset/source tracking

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| source_key | SERIAL | PK | Surrogate key |
| dataset_name | VARCHAR(100) | UNIQUE | Arena, MetaCoder, etc. |
| source_url | VARCHAR(500) | | HuggingFace URL or path |
| version | VARCHAR(50) | | Dataset version |
| record_count | BIGINT | | Total records in source |
| created_at | TIMESTAMP | | Row creation time |

**Size**: ~4 rows (Arena, MetaCoder, HumanEval, SWE-Bench)

---

## Fact Tables

### fact_promptexecution (Main fact table)

**Purpose**: One row per prompt execution attempt

**Size**: 200K+ rows

| Column | Type | Key | Constraint | Description |
|--------|------|-----|-----------|-------------|
| execution_id | SERIAL | PK | NOT NULL | Unique execution record |
| prompt_key | INTEGER | FK | NOT NULL | Foreign key to dim_prompt |
| model_key | INTEGER | FK | NOT NULL | Foreign key to dim_model |
| task_key | INTEGER | FK | NOT NULL | Foreign key to dim_task |
| time_key | INTEGER | FK | NOT NULL | Foreign key to dim_time |
| session_key | INTEGER | FK | | Foreign key to dim_session |
| source_key | INTEGER | FK | NOT NULL | Foreign key to dim_source |
| success_flag | BOOLEAN | | NOT NULL | 1=passed, 0=failed |
| success_score | NUMERIC(5,4) | | CHECK (0-1) | Score 0.0-1.0 |
| latency_ms | INTEGER | | CHECK (>0) | Execution time in ms |
| tokens_used | INTEGER | | | Tokens consumed (if applicable) |
| created_at | TIMESTAMP | | NOT NULL | Record creation time |

**Indexes**:
- PRIMARY KEY: execution_id
- FOREIGN KEYS: All FK columns indexed
- COMPOSITE: (time_key, model_key) for time-series queries
- PARTIAL: (success_flag = true) for success rate calculations
- PARTIAL: (latency_ms IS NOT NULL) for latency analysis

**Sample Query**:
```sql
-- Average success by model (using materialized view)
SELECT model_name, COUNT(*) as attempts, AVG(success_score) as avg_success
FROM fact_promptexecution f
JOIN dim_model m ON f.model_key = m.model_key
GROUP BY m.model_name
ORDER BY avg_success DESC;
```

---

### fact_model_comparison

**Purpose**: Pairwise comparisons between models

**Size**: 50K+ rows

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| comparison_id | SERIAL | PK | Unique comparison record |
| time_key | INTEGER | FK | When comparison occurred |
| source_key | INTEGER | FK | Which dataset |
| model_a_key | INTEGER | FK | First model in pair |
| model_b_key | INTEGER | FK | Second model in pair |
| winner_model_key | INTEGER | FK | Which model won |
| competitiveness_score | NUMERIC(5,4) | | How close was the match |
| created_at | TIMESTAMP | | Record creation time |

**Sample Query**:
```sql
-- How often did gpt-4 beat claude?
SELECT 
  a.model_name as model_a,
  b.model_name as model_b,
  COUNT(*) as comparisons,
  SUM(CASE WHEN w.model_key = a.model_key THEN 1 ELSE 0 END) as a_wins
FROM fact_model_comparison c
JOIN dim_model a ON c.model_a_key = a.model_key
JOIN dim_model b ON c.model_b_key = b.model_key
JOIN dim_model w ON c.winner_model_key = w.model_key
WHERE a.model_name IN ('gpt-4', 'claude-v1')
GROUP BY a.model_name, b.model_name;
```

---

## Materialized Views (Phase 1 Completed)

All materialized views are indexed and pre-aggregated for fast API response times.

### mv_model_performance_arena

Models ranked by success rate (Arena dataset only)

```sql
SELECT 
  COALESCE(m.model_name, 'Unknown') as model_name,
  COUNT(f.execution_id)::BIGINT as attempts,
  AVG(f.success_score)::NUMERIC(5,4) as avg_success,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.success_score)::NUMERIC(5,4) as median_success
FROM fact_promptexecution f
JOIN dim_model m ON f.model_key = m.model_key
JOIN dim_source s ON f.source_key = s.source_key
WHERE s.dataset_name ILIKE '%arena%'
GROUP BY m.model_key, m.model_name
ORDER BY avg_success DESC NULLS LAST;
```

**Row Count**: ~15 rows (models)  
**Indexes**: (model_name), (avg_success DESC), (attempts DESC)  
**Refresh**: Requires manual REFRESH MATERIALIZED VIEW after new data is loaded

---

### mv_daily_model_success

Time-series: Model performance per day

```sql
SELECT 
  COALESCE(t.day, CURRENT_DATE) as day,
  COALESCE(m.model_name, 'Unknown') as model_name,
  COUNT(f.execution_id)::BIGINT as attempts,
  AVG(f.success_score)::NUMERIC(5,4) as avg_success,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.success_score)::NUMERIC(5,4) as median_success
FROM fact_promptexecution f
JOIN dim_model m ON f.model_key = m.model_key
JOIN dim_time t ON f.time_key = t.time_key
GROUP BY t.day, m.model_key, m.model_name
ORDER BY day DESC, avg_success DESC;
```

**Row Count**: ~450 rows (15 models × 30 days)  
**Indexes**: (day DESC, model_name), (avg_success DESC)  
**Use Case**: Time-series charting, trend analysis

---

### mv_language_performance

Programming language difficulty ranking

```sql
SELECT 
  COALESCE(tk.programming_lang, 'Unknown') as programming_lang,
  COUNT(f.execution_id)::BIGINT as prompts,
  AVG(f.success_score)::NUMERIC(5,4) as success_rate,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.success_score)::NUMERIC(5,4) as median_success
FROM fact_promptexecution f
JOIN dim_task tk ON f.task_key = tk.task_key
GROUP BY tk.task_key, tk.programming_lang
ORDER BY success_rate DESC NULLS LAST;
```

**Row Count**: ~12 rows (languages)  
**Indexes**: (programming_lang), (success_rate DESC), (prompts DESC)

---

### mv_prompt_feature_impact

Feature combinations and their success impact

```sql
SELECT 
  COALESCE(p.contains_examples, FALSE) as contains_examples,
  COALESCE(p.contains_code, FALSE) as contains_code,
  COALESCE(p.contains_constraints, FALSE) as contains_constraints,
  COUNT(f.execution_id)::BIGINT as cnt,
  AVG(f.success_score)::NUMERIC(5,4) as avg_success,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.success_score)::NUMERIC(5,4) as median_success
FROM fact_promptexecution f
JOIN dim_prompt p ON f.prompt_key = p.prompt_key
GROUP BY p.contains_examples, p.contains_code, p.contains_constraints
ORDER BY avg_success DESC NULLS LAST;
```

**Row Count**: 8 rows (all combinations of 3 boolean features)  
**Indexes**: (contains_examples, contains_code, contains_constraints), (avg_success DESC)

---

### mv_top_prompt_templates

Best-performing prompt templates

```sql
SELECT 
  COALESCE(p.prompt_hash, 'unknown') as prompt_hash,
  COALESCE(p.prompt_text, '') as prompt_text,
  COUNT(f.execution_id)::BIGINT as uses,
  AVG(f.success_score)::NUMERIC(5,4) as avg_success,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.success_score)::NUMERIC(5,4) as median_success
FROM fact_promptexecution f
JOIN dim_prompt p ON f.prompt_key = p.prompt_key
GROUP BY p.prompt_key, p.prompt_hash, p.prompt_text
HAVING COUNT(f.execution_id) >= 5
ORDER BY avg_success DESC NULLS LAST, uses DESC;
```

**Row Count**: ~2,341 rows (top N prompt templates)  
**Indexes**: (prompt_hash), (avg_success DESC), (uses DESC)  
**Filter**: Only prompts with 5+ uses (HAVING clause prevents noise)

---

## OLAP Indexes (Phase 1 Completed)

**Total Indexes Created**: 14

### Fact Table Indexes (11)

On `fact_promptexecution`:

```sql
-- FK Indexes (for join performance)
CREATE INDEX idx_fpe_prompt_key ON fact_promptexecution(prompt_key);
CREATE INDEX idx_fpe_model_key ON fact_promptexecution(model_key);
CREATE INDEX idx_fpe_task_key ON fact_promptexecution(task_key);
CREATE INDEX idx_fpe_time_key ON fact_promptexecution(time_key);
CREATE INDEX idx_fpe_session_key ON fact_promptexecution(session_key);
CREATE INDEX idx_fpe_source_key ON fact_promptexecution(source_key);

-- Analytical Predicates (partial indexes for WHERE clauses)
CREATE INDEX idx_fpe_success_score_notnull ON fact_promptexecution(success_score) 
  WHERE success_score IS NOT NULL;
CREATE INDEX idx_fpe_latency_notnull ON fact_promptexecution(latency_ms) 
  WHERE latency_ms IS NOT NULL;

-- Composite (time-sries queries)
CREATE INDEX idx_fpe_time_model ON fact_promptexecution(time_key, model_key);

-- Comparison fact table
CREATE INDEX idx_fmc_time_key ON fact_model_comparison(time_key);
CREATE INDEX idx_fmc_source_key ON fact_model_comparison(source_key);
CREATE INDEX idx_fmc_model_a_key ON fact_model_comparison(model_a_key);
CREATE INDEX idx_fmc_model_b_key ON fact_model_comparison(model_b_key);
CREATE INDEX idx_fmc_winner_model_key ON fact_model_comparison(winner_model_key);
```

### Dimension Table Indexes (3)

```sql
-- Commonly filtered dimensions
CREATE INDEX idx_dim_time_day ON dim_time(day);
CREATE INDEX idx_dim_source_dataset_name ON dim_source(dataset_name);
CREATE INDEX idx_dim_task_lang ON dim_task(programming_lang);
```

---

## Query Optimization Tips

### Always Use Materialized Views for Aggregations

**Good** (fast - <100ms):
```sql
SELECT * FROM mv_model_performance_arena LIMIT 10;
```

**Bad** (slow - >500ms):
```sql
SELECT m.model_name, AVG(f.success_score)
FROM fact_promptexecution f
JOIN dim_model m ON f.model_key = m.model_key
WHERE source_key IN (SELECT source_key FROM dim_source WHERE dataset_name ILIKE '%arena%')
GROUP BY m.model_key, m.model_name;
```

### Filter by Indexed Columns

**Good** (uses indexes):
```sql
SELECT * FROM mv_model_performance_arena 
WHERE model_name IN ('gpt-4', 'claude-v1');
```

**Less efficient** (no index on success_score):
```sql
SELECT * FROM mv_model_performance_arena 
WHERE avg_success > 0.7;
```

### Use EXPLAIN to Understand Query Plans

```sql
EXPLAIN ANALYZE
SELECT * FROM fact_promptexecution 
WHERE model_key = 1 AND time_key > 100
LIMIT 100;
```

---

## Refresh Strategy

### Materialized View Refresh

After new data is loaded into fact tables, refresh views:

```sql
-- Refresh one view
REFRESH MATERIALIZED VIEW mv_model_performance_arena;

-- Refresh all views (consider order due to dependencies)
REFRESH MATERIALIZED VIEW mv_model_performance_arena;
REFRESH MATERIALIZED VIEW mv_daily_model_success;
REFRESH MATERIALIZED VIEW mv_language_performance;
REFRESH MATERIALIZED VIEW mv_prompt_feature_impact;
REFRESH MATERIALIZED VIEW mv_top_prompt_templates;
```

### Automated Refresh (Cron/Scheduler)

```bash
# PostgreSQL cron extension (if available)
SELECT cron.schedule('refresh-olap-views', '0 * * * *', $$
  REFRESH MATERIALIZED VIEW CONCURRENTLY mv_model_performance_arena;
  REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_model_success;
  REFRESH MATERIALIZED VIEW CONCURRENTLY mv_language_performance;
  REFRESH MATERIALIZED VIEW CONCURRENTLY mv_prompt_feature_impact;
  REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_prompt_templates;
$$);
```

---

## Example Queries for Developers

### Query 1: Top 5 Models by Success Rate
```sql
SELECT model_name, attempts, avg_success, median_success
FROM mv_model_performance_arena
ORDER BY avg_success DESC
LIMIT 5;
```

### Query 2: Language Difficulty Ranking
```sql
SELECT programming_lang, prompts, success_rate, median_success
FROM mv_language_performance
WHERE prompts >= 50
ORDER BY success_rate DESC;
```

### Query 3: Best Prompt Features Combination
```sql
SELECT 
  CASE 
    WHEN contains_examples AND contains_code THEN 'Examples + Code'
    WHEN contains_examples THEN 'Examples Only'
    WHEN contains_code THEN 'Code Only'
    ELSE 'No Features'
  END as feature_combo,
  cnt as sample_count,
  avg_success,
  median_success
FROM mv_prompt_feature_impact
ORDER BY avg_success DESC;
```

### Query 4: Top 10 Reused Prompts
```sql
SELECT prompt_hash, prompt_text, uses, avg_success, median_success
FROM mv_top_prompt_templates
ORDER BY uses DESC
LIMIT 10;
```

### Query 5: 30-Day Performance Trend for gpt-4
```sql
SELECT day, avg_success, median_success, attempts
FROM mv_daily_model_success
WHERE model_name = 'gpt-4'
  AND day >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY day ASC;
```

---

## Useful psql Commands

```bash
# Connect to database
psql -U postgres -d promptlens

# List all tables
\dt

# List all views
\dv

# List materialized views
\dm

# List indexes
\di

# Describe table structure
\d fact_promptexecution

# Show table size
SELECT pg_size_pretty(pg_total_relation_size('fact_promptexecution'));

# Count rows in table
SELECT COUNT(*) FROM fact_promptexecution;

# Show view definition
SELECT pg_get_viewdef('mv_model_performance_arena');

# Analyze query plan
EXPLAIN ANALYZE SELECT ...;
```

---

## Data Dictionary (Quick Reference)

| Column | Table | Type | Range | Description |
|--------|-------|------|-------|-------------|
| success_score | fact_promptexecution | NUMERIC | 0.0-1.0 | Execution success (0=fail, 1=perfect pass) |
| latency_ms | fact_promptexecution | INTEGER | 0-∞ | Time model took to respond (milliseconds) |
| avg_success | Materialized Views | NUMERIC | 0.0-1.0 | Average of success_score values |
| median_success | Materialized Views | NUMERIC | 0.0-1.0 | Median of success_score values |
| attempts | Materialized Views | BIGINT | 0-∞ | Count of execution records |
| prompt_hash | dim_prompt | VARCHAR(64) | - | SHA256 hash (unique identifier) |
| model_name | dim_model | VARCHAR(100) | - | Model identifier (gpt-4, claude-v1, etc.) |
| programming_lang | dim_task | VARCHAR(50) | - | Language (python, java, sql, etc.) |
| dataset_name | dim_source | VARCHAR(100) | - | Dataset (Arena, MetaCoder, etc.) |

