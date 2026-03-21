-- PromptLens OLAP materialized views
-- Run after base schema/tables exist.
-- Refresh these views after each ETL load.

DROP MATERIALIZED VIEW IF EXISTS mv_daily_model_success;
CREATE MATERIALIZED VIEW mv_daily_model_success AS
SELECT
    t.ts::date AS day,
    COALESCE(m.model_name, 'unknown') AS model_name,
    COUNT(*) AS attempts,
    AVG(f.success_score) AS avg_success,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.success_score) AS median_success
FROM fact_promptexecution f
JOIN dim_time t ON t.time_key = f.time_key
LEFT JOIN dim_model m ON m.model_key = f.model_key
WHERE f.success_score IS NOT NULL
GROUP BY t.ts::date, COALESCE(m.model_name, 'unknown');

CREATE INDEX IF NOT EXISTS idx_mv_daily_model_success_day_model
    ON mv_daily_model_success(day, model_name);

DROP MATERIALIZED VIEW IF EXISTS mv_model_performance_arena;
CREATE MATERIALIZED VIEW mv_model_performance_arena AS
SELECT
    m.model_name,
    COUNT(*) AS attempts,
    AVG(f.success_score) AS avg_success,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.success_score) AS median_success
FROM fact_promptexecution f
JOIN dim_model m ON m.model_key = f.model_key
JOIN dim_source s ON s.source_key = f.source_key
WHERE s.dataset_name ILIKE '%arena%'
  AND f.success_score IS NOT NULL
GROUP BY m.model_name;

CREATE INDEX IF NOT EXISTS idx_mv_model_performance_arena_model
    ON mv_model_performance_arena(model_name);

DROP MATERIALIZED VIEW IF EXISTS mv_language_performance;
CREATE MATERIALIZED VIEW mv_language_performance AS
SELECT
    k.programming_lang,
    COUNT(*) AS prompts,
    AVG(f.success_score) AS success_rate,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.success_score) AS median_success
FROM fact_promptexecution f
JOIN dim_task k ON k.task_key = f.task_key
WHERE k.programming_lang IS NOT NULL
  AND f.success_score IS NOT NULL
GROUP BY k.programming_lang;

CREATE INDEX IF NOT EXISTS idx_mv_language_performance_lang
    ON mv_language_performance(programming_lang);

DROP MATERIALIZED VIEW IF EXISTS mv_prompt_feature_impact;
CREATE MATERIALIZED VIEW mv_prompt_feature_impact AS
SELECT
    p.contains_examples,
    p.contains_code,
    p.contains_constraints,
    COUNT(*) AS cnt,
    AVG(f.success_score) AS avg_success,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.success_score) AS median_success
FROM fact_promptexecution f
JOIN dim_prompt p ON p.prompt_key = f.prompt_key
WHERE f.success_score IS NOT NULL
GROUP BY p.contains_examples, p.contains_code, p.contains_constraints;

CREATE INDEX IF NOT EXISTS idx_mv_prompt_feature_impact_flags
    ON mv_prompt_feature_impact(contains_examples, contains_code, contains_constraints);

DROP MATERIALIZED VIEW IF EXISTS mv_top_prompt_templates;
CREATE MATERIALIZED VIEW mv_top_prompt_templates AS
SELECT
    p.prompt_hash,
    p.prompt_text,
    COUNT(*) AS uses,
    AVG(f.success_score) AS avg_success,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.success_score) AS median_success
FROM fact_promptexecution f
JOIN dim_prompt p ON p.prompt_key = f.prompt_key
WHERE f.success_score IS NOT NULL
GROUP BY p.prompt_hash, p.prompt_text;

CREATE INDEX IF NOT EXISTS idx_mv_top_prompt_templates_metrics
    ON mv_top_prompt_templates(avg_success DESC, uses DESC);

-- Optional convenience view for easier API use
DROP VIEW IF EXISTS v_olap_refresh_commands;
CREATE VIEW v_olap_refresh_commands AS
SELECT 'REFRESH MATERIALIZED VIEW mv_daily_model_success;'::text AS command
UNION ALL SELECT 'REFRESH MATERIALIZED VIEW mv_model_performance_arena;'
UNION ALL SELECT 'REFRESH MATERIALIZED VIEW mv_language_performance;'
UNION ALL SELECT 'REFRESH MATERIALIZED VIEW mv_prompt_feature_impact;'
UNION ALL SELECT 'REFRESH MATERIALIZED VIEW mv_top_prompt_templates;';
