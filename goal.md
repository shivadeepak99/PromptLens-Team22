
23

Automatic Zoom
OLAP: where & how aggregations run 
All OLAP aggregations run inside the data warehouse (PostgreSQL) as SQL queries or 
precomputed materialized views / aggregates. We do not pull full tables into application memory for aggregations. 
Why: 
●  SQL is fast for grouping/aggregation. 
●  Postgres supports indexes, MV, and fast scans. 
●  Keeps architecture simple for team. 
Two aggregation modes 
1.  Interactive (ad-hoc) — run parameterized SQL directly against 
fact_promptexecution + joins. Good for exploratory queries and dashboards with 
filters. 
2.  Precomputed / Materialized — heavy aggregations (daily model performance, top N 
prompts, time-series rollups) are stored as materialized views refreshed on a schedule 
or after ETL. Good for dashboards and APIs with SLAs. 
Performance knobs (what Shivadeepak should set) 
●  Indexes on time_key, model_key, prompt_key, source_key, task_key. 
●  Partial indexes for frequent filters (e.g., WHERE success_score IS NOT NULL). 
●  Materialized views for expensive aggregates and refresh schedule after ETL. 
●  LIMIT + pagination for large result sets. 
●  Use EXPLAIN ANALYSE for tuning slow queries. 
 
Core OLAP example queries — SQL + 
explanation + sample result 
Tables used: fact_promptexecution (f), dim_prompt (p), dim_model (m), 
dim_time (t), dim_source (s), dim_task (k). 
1) Model performance (Arena-only) 
SQL 
SELECT m.model_name, 
       COUNT(*) AS attempts, 
       AVG(f.success_score) AS avg_success, 
       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.success_score) AS 
median_success 
FROM fact_promptexecution f 
JOIN dim_model m     ON f.model_key = m.model_key 
JOIN dim_source s    ON f.source_key = s.source_key 
WHERE s.dataset_name ILIKE '%arena%' 
  AND f.success_score IS NOT NULL 
GROUP BY m.model_name 
ORDER BY avg_success DESC 
LIMIT 50; 
 
Where: runs on Postgres / exposed via API /analytics/model-performance. 
Sample JSON: 
[ 
  {"model_name":"claude-v1","attempts":10000,"avg_success":0.672,"median_success":0.75}, 
  {"model_name":"gpt-3.5-turbo","attempts":9000,"avg_success":0.613,"median_success":0.67} 
] 
 
 
2) Programming language success (filter non-null) 
SQL 
SELECT p.programming_lang, 
       COUNT(*) AS prompts, 
       AVG(f.success_score) AS success_rate 
FROM fact_promptexecution f 
JOIN dim_prompt p ON f.prompt_key = p.prompt_key 
WHERE p.programming_lang IS NOT NULL 
  AND f.success_score IS NOT NULL 
GROUP BY p.programming_lang 
ORDER BY success_rate DESC 
LIMIT 50; 
 
Use: find which languages are hardest. (Run via API /analytics/language-performance) 
 
3) Prompt feature impact (examples / constraints / code) 
SQL 
SELECT p.contains_examples, 
       p.contains_code, 
       p.contains_constraints, 
       COUNT(*) AS cnt, 
       AVG(f.success_score) AS avg_success 
FROM fact_promptexecution f 
JOIN dim_prompt p ON f.prompt_key = p.prompt_key 
WHERE f.success_score IS NOT NULL 
GROUP BY p.contains_examples, p.contains_code, p.contains_constraints 
ORDER BY cnt DESC; 
 
Result: tells you combos like (examples=true, code=false, constraints=true) → avg_success. 
 
4) Time-series: daily success rate (materialized view) 
Create materialized view 
CREATE MATERIALIZED VIEW mv_daily_success AS 
SELECT t.ts::date AS day, 
       m.model_name, 
       COUNT(*) AS attempts, 
       AVG(f.success_score) AS avg_success 
FROM fact_promptexecution f 
JOIN dim_time t ON f.time_key = t.time_key 
LEFT JOIN dim_model m ON f.model_key = m.model_key 
WHERE f.success_score IS NOT NULL 
GROUP BY day, m.model_name; 
 
Refresh: REFRESH MATERIALIZED VIEW mv_daily_success; (schedule after ETL). 
Use: dashboard chart and trend analysis. 
 
5) Top 20 prompt templates by success (pivot) 
SQL 
SELECT p.prompt_hash, p.prompt_text, COUNT(*) AS uses, AVG(f.success_score) AS 
avg_success 
FROM fact_promptexecution f 
JOIN dim_prompt p ON f.prompt_key = p.prompt_key 
WHERE f.success_score IS NOT NULL 
GROUP BY p.prompt_hash, p.prompt_text 
ORDER BY avg_success DESC 
LIMIT 20; 
 
Use: show “best prompts” for humans to copy. 
 
How prompt insights are produced — full 
flow (user → system → response) 
1.  User requests insight (via UI or API): “Which prompt features increase success for 
Python code prompts?” 
2.  Agent/API layer receives request, validates input and user permissions. 
3.  Agent maps to SQL (or ML routine): it will choose an OLAP query, possibly with extra 
filters: programming_lang='python' + contains_code=true. 
4.  Query runs on warehouse (directly or via materialized view). 
5.  Result returned, agent formats human-friendly insights and confidence stats (counts, 
p-values or support/confidence for rules). 
6.  UI shows a chart and textual suggestions. 
Example insight flow (explicit) 
User: “Do examples help for Python coding prompts?” 
API: 
/insights/prompt-feature-impact?lang=python&feature=contains_examples 
Backend mapping → SQL 
SELECT p.contains_examples, 
       COUNT(*) AS cnt, 
GET /analytics/model-performance 
Description: aggregated model performance. 
Query params: dataset (optional), lang (optional), since (e.g., 30d), limit 
Sample request 
GET /analytics/model-performance?dataset=chatbot_arena&since=30d 
 
Sample response 
[ 
  {"model_name":"claude-v1","attempts":10000,"avg_success":0.672}, 
  {"model_name":"gpt-3.5-turbo","attempts":9000,"avg_success":0.613} 
] 
 
 
GET /analytics/prompt-features 
Description: measure effect of features (contains_examples, code, constraints). 
Query params: feature=contains_examples, filter_lang=python, 
dataset=chatbot_arena 
Sample response 
{"feature":"contains_examples","filter":{"programming_lang":"python"},"results":[{"value":true,"cnt
":1120,"avg_success":0.423},{"value":false,"cnt":3250,"avg_success":0.399}]} 
 
 
GET /analytics/time-series 
Description: time-series for model or feature (uses materialized view / rollup) 
Params: model_name, feature, granularity (daily|weekly|monthly), since 
Response: list of {date, metric} 
User prompt: 
How should I design a Python coding prompt? 
 
System returns: 
Best structure: 
• include example code 
• include constraints 
• prompt length ~120 tokens 
 
 
3⃣ Integration points 
PromptLens can integrate with several systems. 
Integration 1 — Developer tools 
Example tools: 
Cursor 
VSCode 
JetBrains IDE 
 
How it works: 
Plugin sends prompt → PromptLens API. 
PromptLens returns insights. 
 
Integration 2 — Prompt engineering platforms 
Example: 
LangChain 
AutoGPT 
AI agents 
 
Example result: 
Claude → 0.67 success 
GPT-3.5 → 0.61 
Vicuna → 0.51 
 
 
Use Case 2 — Prompt feature analysis 
User asks: 
Does including code reduce success? 
 
System computes: 
contains_code → success_rate 
 
 
Use Case 3 — Programming language analysis 
User asks: 
Which languages are hardest for LLMs? 
 
System computes: 
language → success_rate 
 
 
Use Case 4 — Prompt clustering 
User wants to discover prompt types. 
System groups prompts. 
Example clusters: 
code generation prompts 
reasoning prompts 
PostgreSQL 
↓ 
Python dataset extraction 
↓ 
KMeans clustering 
↓ 
cluster labels stored 
↓ 
API returns clusters 
 
 
Use Case 4 — Classification 
Goal: 
Predict prompt success. 
Pipeline: 
feature extraction 
↓ 
training dataset 
↓ 
RandomForest classifier 
↓ 
model predicts success probability 
 
 
Use Case 5 — Association rules 
Algorithm: 
Apriori 
 
Example rule: 
contains_examples → success 
 
 
6⃣ Final PromptLens system architecture 
Full system: 
Datasets 
    ↓ 
ETL Pipeline 
    ↓ 
Feature Engineering 
    ↓ 
PostgreSQL Warehouse 
    ↓ 
OLAP Analytics 
    ↓ 
Machine Learning 
    ↓ 
FastAPI Layer 
    ↓ 
Dashboard / Integrations 
 
 
7⃣ Final system capabilities 
PromptLens will be able to: 
Analyze prompt performance 
Compare AI models 
Discover prompt patterns 
Recommend prompt improvements 
Benchmark prompts 
Provide prompt analytics API 
Power prompt dashboards 
Integrate with developer tools 
 
 
 
 