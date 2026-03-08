import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = "postgresql://postgres:supersecret@localhost:5432/promptlens"

def run_query(cur, title, query):
    print("\n" + "="*70)
    print(title)
    print("="*70)
    cur.execute(query)
    rows = cur.fetchall()

    if not rows:
        print("No rows returned")
        return

    for row in rows:
        print(dict(row))


def main():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print("\nPromptLens Database Validation Report")

    # --------------------------------------------------
    # DATABASE SIZE
    # --------------------------------------------------

    run_query(
        cur,
        "Database Size",
        """
        SELECT pg_size_pretty(pg_database_size('promptlens')) AS database_size;
        """
    )

    # --------------------------------------------------
    # TABLE SIZES
    # --------------------------------------------------

    run_query(
        cur,
        "Table Sizes",
        """
        SELECT
            relname AS table_name,
            pg_size_pretty(pg_total_relation_size(relid)) AS total_size
        FROM pg_catalog.pg_statio_user_tables
        ORDER BY pg_total_relation_size(relid) DESC;
        """
    )

    # --------------------------------------------------
    # ROW COUNTS
    # --------------------------------------------------

    run_query(
        cur,
        "Row Counts",
        """
        SELECT relname AS table_name, n_live_tup AS row_count
        FROM pg_stat_user_tables
        ORDER BY n_live_tup DESC;
        """
    )

    # --------------------------------------------------
    # DATASET DISTRIBUTION
    # --------------------------------------------------

    run_query(
        cur,
        "Dataset Distribution",
        """
        SELECT s.dataset_name, COUNT(*) AS rows
        FROM fact_promptexecution f
        JOIN dim_source s ON f.source_key = s.source_key
        GROUP BY s.dataset_name
        ORDER BY rows DESC;
        """
    )

    # --------------------------------------------------
    # FOREIGN KEY VALIDATION
    # --------------------------------------------------

    run_query(
        cur,
        "Prompt FK Integrity",
        """
        SELECT COUNT(*) AS broken_prompt_keys
        FROM fact_promptexecution f
        LEFT JOIN dim_prompt p
        ON f.prompt_key = p.prompt_key
        WHERE p.prompt_key IS NULL;
        """
    )

    run_query(
        cur,
        "Model FK Integrity",
        """
        SELECT COUNT(*) AS broken_model_keys
        FROM fact_promptexecution f
        LEFT JOIN dim_model m
        ON f.model_key = m.model_key
        WHERE f.model_key IS NOT NULL
        AND m.model_key IS NULL;
        """
    )

    run_query(
        cur,
        "Time FK Integrity",
        """
        SELECT COUNT(*) AS broken_time_keys
        FROM fact_promptexecution f
        LEFT JOIN dim_time t
        ON f.time_key = t.time_key
        WHERE t.time_key IS NULL;
        """
    )

    # --------------------------------------------------
    # DUPLICATE PROMPTS
    # --------------------------------------------------

    run_query(
        cur,
        "Duplicate Prompt Hashes",
        """
        SELECT prompt_hash, COUNT(*) AS count
        FROM dim_prompt
        GROUP BY prompt_hash
        HAVING COUNT(*) > 1
        LIMIT 10;
        """
    )

    # --------------------------------------------------
    # MODEL PERFORMANCE (OLAP example)
    # --------------------------------------------------

    run_query(
        cur,
        "Model Performance",
        """
        SELECT m.model_name,
               COUNT(*) AS attempts,
               AVG(f.success_score) AS avg_success
        FROM fact_promptexecution f
        JOIN dim_model m ON f.model_key = m.model_key
        WHERE f.success_score IS NOT NULL
        GROUP BY m.model_name
        ORDER BY avg_success DESC
        LIMIT 10;
        """
    )

    # --------------------------------------------------
    # PROMPT FEATURE IMPACT
    # --------------------------------------------------

    run_query(
        cur,
        "Prompt Feature Impact",
        """
        SELECT p.contains_code,
               p.contains_examples,
               p.contains_constraints,
               COUNT(*) AS rows,
               AVG(f.success_score) AS avg_success
        FROM fact_promptexecution f
        JOIN dim_prompt p ON f.prompt_key = p.prompt_key
        WHERE f.success_score IS NOT NULL
        GROUP BY p.contains_code,
                 p.contains_examples,
                 p.contains_constraints
        ORDER BY rows DESC
        LIMIT 10;
        """
    )
# --------------------------------------------------
# PROGRAMMING LANGUAGE ANALYSIS (safe version)
# --------------------------------------------------

    cur.execute("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name='dim_prompt';
    """)

    columns = {row["column_name"] for row in cur.fetchall()}
    run_query(
        cur,
        "Language Success Analysis",
        """
        SELECT
            p.language,
            COUNT(*) AS prompts,
            AVG(f.success_score) AS success_rate
        FROM fact_promptexecution f
        JOIN dim_prompt p
            ON f.prompt_key = p.prompt_key
        WHERE
            p.language IS NOT NULL
            AND f.success_score IS NOT NULL
        GROUP BY p.language
        ORDER BY success_rate DESC
        LIMIT 20;
        """
    )

if __name__ == "__main__":
    main()