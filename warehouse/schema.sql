-- PromptLens star schema with adapter-driven ETL support

CREATE TABLE IF NOT EXISTS dim_prompt (
    prompt_key SERIAL PRIMARY KEY,
    prompt_text TEXT NOT NULL,
    prompt_hash CHAR(64) NOT NULL,
    prompt_length INTEGER NOT NULL,
    token_estimate INTEGER NOT NULL,
    prompt_type VARCHAR(128) NOT NULL DEFAULT 'standard',
    contains_code BOOLEAN NOT NULL DEFAULT FALSE,
    contains_examples BOOLEAN NOT NULL DEFAULT FALSE,
    contains_constraints BOOLEAN NOT NULL DEFAULT FALSE,
    language VARCHAR(64) NOT NULL DEFAULT 'unknown',
    complexity_score FLOAT NOT NULL DEFAULT 0,
    instruction_density FLOAT,
    length INTEGER,
    token_count INTEGER,
    type VARCHAR(128),
    UNIQUE (prompt_hash)
);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = 'dim_prompt'
    ) THEN
        ALTER TABLE dim_prompt DROP CONSTRAINT IF EXISTS dim_prompt_prompt_hash_prompt_text_key;
        IF NOT EXISTS (
            SELECT 1
            FROM pg_constraint
            WHERE conrelid = 'dim_prompt'::regclass
              AND conname = 'dim_prompt_prompt_hash_key'
        ) THEN
            ALTER TABLE dim_prompt
            ADD CONSTRAINT dim_prompt_prompt_hash_key UNIQUE (prompt_hash);
        END IF;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS dim_model (
    model_key SERIAL PRIMARY KEY,
    model_name VARCHAR(256) NOT NULL UNIQUE,
    version VARCHAR(64),
    provider VARCHAR(128),
    param_count BIGINT,
    context_window INTEGER,
    release_date DATE
);

CREATE TABLE IF NOT EXISTS dim_task (
    task_key SERIAL PRIMARY KEY,
    task_type VARCHAR(128),
    domain VARCHAR(128),
    language VARCHAR(64),
    programming_lang VARCHAR(64),
    difficulty VARCHAR(64),
    benchmark_id VARCHAR(128),
    category VARCHAR(128)
);

CREATE TABLE IF NOT EXISTS dim_time (
    time_key SERIAL PRIMARY KEY,
    ts TIMESTAMP NOT NULL UNIQUE,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    day INTEGER,
    day_of_week INTEGER,
    week_number INTEGER,
    is_weekend BOOLEAN
);

CREATE TABLE IF NOT EXISTS dim_session (
    session_key SERIAL PRIMARY KEY,
    session_id VARCHAR(256) UNIQUE,
    user_context TEXT,
    environment TEXT,
    config_flags TEXT,
    runtime_version VARCHAR(128)
);

CREATE TABLE IF NOT EXISTS dim_source (
    source_key SERIAL PRIMARY KEY,
    dataset_name VARCHAR(256) NOT NULL UNIQUE,
    collection_method VARCHAR(256),
    version VARCHAR(64),
    ingest_timestamp TIMESTAMP,
    batch_id VARCHAR(128)
);

CREATE TABLE IF NOT EXISTS fact_promptexecution (
    fact_key SERIAL PRIMARY KEY,
    conversation_id VARCHAR(256) NOT NULL,
    turn_number INTEGER NOT NULL,
    prompt_key INTEGER REFERENCES dim_prompt(prompt_key),
    model_key INTEGER REFERENCES dim_model(model_key),
    task_key INTEGER REFERENCES dim_task(task_key),
    time_key INTEGER REFERENCES dim_time(time_key),
    session_key INTEGER REFERENCES dim_session(session_key),
    source_key INTEGER REFERENCES dim_source(source_key),
    response_text TEXT,
    tokens INTEGER NOT NULL,
    response_tokens INTEGER,
    latency FLOAT,
    quality_label VARCHAR(64),
    success_score FLOAT
);

CREATE TABLE IF NOT EXISTS fact_model_comparison (
    comparison_key SERIAL PRIMARY KEY,
    conversation_id VARCHAR(256) NOT NULL,
    prompt_key INTEGER REFERENCES dim_prompt(prompt_key),
    model_a_key INTEGER REFERENCES dim_model(model_key),
    model_b_key INTEGER REFERENCES dim_model(model_key),
    winner_model_key INTEGER REFERENCES dim_model(model_key),
    time_key INTEGER REFERENCES dim_time(time_key),
    source_key INTEGER REFERENCES dim_source(source_key)
);

CREATE INDEX IF NOT EXISTS idx_fact_time ON fact_promptexecution(time_key);
CREATE INDEX IF NOT EXISTS idx_fact_model ON fact_promptexecution(model_key);
CREATE INDEX IF NOT EXISTS idx_fact_task ON fact_promptexecution(task_key);
CREATE INDEX IF NOT EXISTS idx_fact_conversation ON fact_promptexecution(conversation_id);
CREATE INDEX IF NOT EXISTS idx_comparison_conversation ON fact_model_comparison(conversation_id);

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'dim_prompt') THEN
        ALTER TABLE dim_prompt
            ALTER COLUMN prompt_type TYPE TEXT,
            ALTER COLUMN language TYPE TEXT,
            ALTER COLUMN type TYPE TEXT;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'dim_model') THEN
        ALTER TABLE dim_model
            ALTER COLUMN model_name TYPE TEXT,
            ALTER COLUMN version TYPE TEXT,
            ALTER COLUMN provider TYPE TEXT;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'dim_task') THEN
        ALTER TABLE dim_task
            ALTER COLUMN task_type TYPE TEXT,
            ALTER COLUMN domain TYPE TEXT,
            ALTER COLUMN language TYPE TEXT,
            ALTER COLUMN programming_lang TYPE TEXT,
            ALTER COLUMN difficulty TYPE TEXT,
            ALTER COLUMN benchmark_id TYPE TEXT,
            ALTER COLUMN category TYPE TEXT;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'dim_source') THEN
        ALTER TABLE dim_source
            ALTER COLUMN dataset_name TYPE TEXT,
            ALTER COLUMN collection_method TYPE TEXT,
            ALTER COLUMN version TYPE TEXT,
            ALTER COLUMN batch_id TYPE TEXT;
    END IF;
END $$;
