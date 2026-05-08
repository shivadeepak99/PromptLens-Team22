-- PromptLens OLAP performance indexes
-- Safe to run multiple times.

-- Fact table join/filter keys (prompt execution)
CREATE INDEX IF NOT EXISTS idx_fact_promptexecution_prompt_key
    ON fact_promptexecution(prompt_key);

CREATE INDEX IF NOT EXISTS idx_fact_promptexecution_source_key
    ON fact_promptexecution(source_key);

CREATE INDEX IF NOT EXISTS idx_fact_promptexecution_session_key
    ON fact_promptexecution(session_key);

-- Partial indexes for common analytical predicates
CREATE INDEX IF NOT EXISTS idx_fact_promptexecution_success_not_null
    ON fact_promptexecution(success_score)
    WHERE success_score IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_fact_promptexecution_latency_not_null
    ON fact_promptexecution(latency)
    WHERE latency IS NOT NULL;

-- Comparison fact table join keys
CREATE INDEX IF NOT EXISTS idx_fact_model_comparison_time_key
    ON fact_model_comparison(time_key);

CREATE INDEX IF NOT EXISTS idx_fact_model_comparison_source_key
    ON fact_model_comparison(source_key);

CREATE INDEX IF NOT EXISTS idx_fact_model_comparison_model_a_key
    ON fact_model_comparison(model_a_key);

CREATE INDEX IF NOT EXISTS idx_fact_model_comparison_model_b_key
    ON fact_model_comparison(model_b_key);

CREATE INDEX IF NOT EXISTS idx_fact_model_comparison_winner_model_key
    ON fact_model_comparison(winner_model_key);

-- Dimension-side helper indexes for frequent filters/groupings
CREATE INDEX IF NOT EXISTS idx_dim_time_ts
    ON dim_time(ts);

CREATE INDEX IF NOT EXISTS idx_dim_source_dataset_name
    ON dim_source(dataset_name);

CREATE INDEX IF NOT EXISTS idx_dim_task_programming_lang
    ON dim_task(programming_lang);

CREATE INDEX IF NOT EXISTS idx_dim_prompt_feature_flags
    ON dim_prompt(contains_examples, contains_code, contains_constraints);
