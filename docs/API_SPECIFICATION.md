# FastAPI Service Layer - Complete Specification

## Overview
This document specifies the REST API endpoints that will consume the OLAP materialized views from PostgreSQL. The API is the bridge between the analytics database layer (Phase 1: completed) and the frontend dashboard (Phase 3).

**Status**: Ready for implementation  
**Database**: PostgreSQL `promptlens` container  
**Technology Stack**: FastAPI + uvicorn + psycopg2  
**Deployment**: Docker or standalone Python

---

## Database Connection

### Connection Parameters
```
Host: localhost (or docker-host or container-name)
Port: 5432
Database: promptlens
User: postgres
Password: [check docker/environment]
```

### Connection String (Python psycopg2)
```python
DATABASE_URL = "postgresql+psycopg2://postgres:PASSWORD@HOST:5432/promptlens"
```

### Connection String (SQLAlchemy)
```python
from sqlalchemy import create_engine
engine = create_engine("postgresql://postgres:PASSWORD@HOST:5432/promptlens")
```

---

## Available Materialized Views (Data Sources)

All endpoints query these materialized views created in Phase 1:

### 1. `mv_model_performance_arena`
Models ranked by success rate (Arena dataset only)

**Columns**:
- `model_name` (VARCHAR): Model identifier
- `attempts` (BIGINT): Total prompt executions
- `avg_success` (NUMERIC): Average success score (0-1)
- `median_success` (NUMERIC): Median success score

**Sample Data**:
```
model_name          | attempts | avg_success | median_success
gpt-4               | 4217     | 0.7543      | 1
claude-v1           | 3927     | 0.6718      | 1
claude-instant-v1   | 2626     | 0.6350      | 1
gpt-3.5-turbo       | 4654     | 0.6138      | 1
vicuna-13b          | 5931     | 0.5162      | 0.5
```

### 2. `mv_daily_model_success`
Time-series data: model performance per day

**Columns**:
- `day` (DATE): Date (YYYY-MM-DD)
- `model_name` (VARCHAR): Model identifier
- `attempts` (BIGINT): Execution count that day
- `avg_success` (NUMERIC): Success rate that day
- `median_success` (NUMERIC): Median success that day

### 3. `mv_language_performance`
Programming language difficulty ranking

**Columns**:
- `programming_lang` (VARCHAR): Programming language (python, java, sql, etc.)
- `prompts` (BIGINT): Total prompts for that language
- `success_rate` (NUMERIC): Overall success rate (0-1)
- `median_success` (NUMERIC): Median success score

### 4. `mv_prompt_feature_impact`
Feature combinations and their impact on success

**Columns**:
- `contains_examples` (BOOLEAN): Has code examples in prompt
- `contains_code` (BOOLEAN): Has code snippets in prompt
- `contains_constraints` (BOOLEAN): Has constraints in prompt
- `cnt` (BIGINT): Count of prompts with this combination
- `avg_success` (NUMERIC): Success rate for this combination
- `median_success` (NUMERIC): Median success score

### 5. `mv_top_prompt_templates`
Best-performing prompt templates (by hash)

**Columns**:
- `prompt_hash` (VARCHAR): Hash of prompt template
- `prompt_text` (TEXT): First 500 chars of prompt
- `uses` (BIGINT): How many times used
- `avg_success` (NUMERIC): Success rate
- `median_success` (NUMERIC): Median success

---

## API Endpoints

### Endpoint 1: Model Performance Rankings

**Route**: `GET /analytics/model-performance`

**Description**: Returns all models ranked by success rate (Arena dataset)

**Query Parameters**:
- `limit` (optional, int, default=10): Max models to return
- `sort_by` (optional, str, default="avg_success"): Sort field (avg_success, attempts, median_success)
- `order` (optional, str, default="desc"): asc or desc

**Response Schema**:
```json
{
  "timestamp": "2024-03-20T10:30:00Z",
  "total_count": 15,
  "data": [
    {
      "model_name": "gpt-4",
      "attempts": 4217,
      "avg_success": 0.7543,
      "median_success": 1.0,
      "rank": 1,
      "success_rate_pct": 75.43
    }
  ]
}
```

**Example Request**:
```
GET /analytics/model-performance?limit=5&sort_by=avg_success&order=desc
```

**Example Response**:
```json
{
  "timestamp": "2024-03-20T10:30:00Z",
  "total_count": 5,
  "data": [
    {
      "model_name": "gpt-4",
      "attempts": 4217,
      "avg_success": 0.7543,
      "median_success": 1.0,
      "rank": 1,
      "success_rate_pct": 75.43
    },
    {
      "model_name": "claude-v1",
      "attempts": 3927,
      "avg_success": 0.6718,
      "median_success": 1.0,
      "rank": 2,
      "success_rate_pct": 67.18
    }
  ]
}
```

---

### Endpoint 2: Language Performance Difficulty

**Route**: `GET /analytics/language-performance`

**Description**: Programming language difficulty ranking. Shows which languages have highest/lowest success rates.

**Query Parameters**:
- `limit` (optional, int, default=20): Max languages to return
- `sort_by` (optional, str, default="success_rate"): Sort field (success_rate, prompts, median_success)
- `order` (optional, str, default="desc"): asc or desc

**Response Schema**:
```json
{
  "timestamp": "2024-03-20T10:30:00Z",
  "total_languages": 12,
  "data": [
    {
      "programming_language": "sql",
      "total_prompts": 2341,
      "success_rate": 0.8234,
      "median_success": 1.0,
      "difficulty_level": "easy"
    }
  ]
}
```

**Expected Data**:
- High success: SQL, Python, SQL (easier, more training data)
- Medium success: Java, C++, JavaScript
- Low success: Obscure/niche languages (less training, more ambiguity)

---

### Endpoint 3: Prompt Feature Impact Analysis

**Route**: `GET /analytics/prompt-features`

**Description**: Shows how prompt features (examples, code, constraints) impact success rates

**Query Parameters**:
- `limit` (optional, int, default=8): Max combinations to return
- `min_samples` (optional, int, default=10): Minimum prompts to include (filters noise)
- `sort_by` (optional, str, default="avg_success"): Sort field (avg_success, cnt, median_success)

**Response Schema**:
```json
{
  "timestamp": "2024-03-20T10:30:00Z",
  "data": [
    {
      "features": {
        "contains_examples": true,
        "contains_code": true,
        "contains_constraints": false
      },
      "sample_count": 1523,
      "avg_success": 0.8145,
      "median_success": 1.0,
      "feature_combination_id": "EX_CO_NC"
    }
  ],
  "insights": {
    "best_combination": "examples + code (no constraints)",
    "worst_combination": "no features",
    "confidence": "medium"
  }
}
```

**Feature Combinations** (8 possible):
```
1. examples=T, code=T, constraints=T  → avg_success
2. examples=T, code=T, constraints=F  → avg_success
3. examples=T, code=F, constraints=T  → avg_success
4. examples=T, code=F, constraints=F  → avg_success
5. examples=F, code=T, constraints=T  → avg_success
6. examples=F, code=T, constraints=F  → avg_success
7. examples=F, code=F, constraints=T  → avg_success
8. examples=F, code=F, constraints=F  → avg_success (baseline)
```

---

### Endpoint 4: Top Prompt Templates

**Route**: `GET /analytics/top-prompts`

**Description**: Best-performing prompt templates ranked by success rate

**Query Parameters**:
- `limit` (optional, int, default=10): Max templates to return
- `min_uses` (optional, int, default=5): Minimum reuse count (filters one-offs)
- `sort_by` (optional, str, default="avg_success"): Sort field (avg_success, uses, median_success)

**Response Schema**:
```json
{
  "timestamp": "2024-03-20T10:30:00Z",
  "total_templates": 2341,
  "top_templates": [
    {
      "prompt_hash": "a1b2c3d4e5f6",
      "prompt_preview": "Write a Python function that...",
      "full_prompt_available": true,
      "usage_count": 234,
      "avg_success": 0.9123,
      "median_success": 1.0,
      "success_rate_pct": 91.23,
      "rank": 1
    }
  ]
}
```

---

### Endpoint 5: Time-Series Model Performance

**Route**: `GET /analytics/model-performance-timeline`

**Description**: Daily model performance over time (for charting trends)

**Query Parameters**:
- `model_name` (optional, str): Filter to specific model (default: all models)
- `days` (optional, int, default=30): Last N days
- `start_date` (optional, date, format=YYYY-MM-DD): Start date
- `end_date` (optional, date, format=YYYY-MM-DD): End date

**Response Schema**:
```json
{
  "timestamp": "2024-03-20T10:30:00Z",
  "models": ["gpt-4", "claude-v1", "gpt-3.5-turbo"],
  "date_range": {
    "start": "2024-02-20",
    "end": "2024-03-20"
  },
  "data": [
    {
      "date": "2024-02-20",
      "series": [
        {
          "model_name": "gpt-4",
          "attempts": 142,
          "avg_success": 0.7654,
          "median_success": 1.0
        }
      ]
    }
  ]
}
```

---

## Response Format Standards

All endpoints follow this envelope format:

```json
{
  "timestamp": "ISO-8601 UTC timestamp",
  "status": "success" | "error",
  "data": {},
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message"
  }
}
```

### Success Response (200 OK)
```json
{
  "timestamp": "2024-03-20T10:30:00Z",
  "status": "success",
  "data": {...}
}
```

### Error Response (4xx/5xx)
```json
{
  "timestamp": "2024-03-20T10:30:00Z",
  "status": "error",
  "error": {
    "code": "DATABASE_CONNECTION_ERROR",
    "message": "Failed to connect to PostgreSQL database"
  }
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Scenario |
|------|----------|
| 200 | Success |
| 400 | Bad request (invalid parameters) |
| 404 | Resource not found |
| 500 | Server error (database, etc.) |
| 503 | Service unavailable (database down) |

### Common Errors

**Invalid Parameter**:
```json
{
  "status": "error",
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "sort_by must be one of: avg_success, attempts, median_success"
  }
}
```

**Database Connection Error**:
```json
{
  "status": "error",
  "error": {
    "code": "DATABASE_ERROR",
    "message": "Cannot connect to PostgreSQL. Check connection parameters."
  }
}
```

---

## Performance Expectations

All endpoints should respond in **<500ms** under normal load because data comes from materialized views (pre-aggregated).

| Endpoint | View | Expected Rows | Typical Response Time |
|----------|------|---------------|-----------------------|
| /model-performance | mv_model_performance_arena | ~15 | <50ms |
| /language-performance | mv_language_performance | ~20 | <50ms |
| /prompt-features | mv_prompt_feature_impact | 8 | <50ms |
| /top-prompts | mv_top_prompt_templates | 2341 | <200ms |
| /model-performance-timeline | mv_daily_model_success | ~450 (15 models × 30 days) | <300ms |

---

## Implementation Checklist

- [ ] Create FastAPI project structure
- [ ] Set up PostgreSQL connection pool
- [ ] Implement endpoint 1: /analytics/model-performance
- [ ] Implement endpoint 2: /analytics/language-performance
- [ ] Implement endpoint 3: /analytics/prompt-features
- [ ] Implement endpoint 4: /analytics/top-prompts
- [ ] Implement endpoint 5: /analytics/model-performance-timeline
- [ ] Add error handling and logging
- [ ] Add request validation with Pydantic models
- [ ] Add CORS headers (for frontend cross-origin requests)
- [ ] Test all endpoints with example queries
- [ ] Add API documentation (Swagger/OpenAPI via FastAPI)
- [ ] Deploy and verify connectivity to PostgreSQL

---

## Dependencies

```
fastapi==0.104.1
uvicorn==0.24.0
psycopg2-binary==2.9.9
python-dotenv==1.0.0
pydantic==2.5.0
```

---

## Setup Instructions for Team

1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables:
   ```
   DATABASE_HOST=localhost
   DATABASE_PORT=5432
   DATABASE_NAME=promptlens
   DATABASE_USER=postgres
   DATABASE_PASSWORD=your_password
   ```
4. Run: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
5. API docs available at: `http://localhost:8000/docs`

---

## Integration with Frontend

- Frontend calls `http://API_SERVER:8000/analytics/*` endpoints
- Expects JSON responses with `timestamp`, `status`, and `data` fields
- Should implement retry logic (exponential backoff) for failures
- Should refresh data on intervals (suggest: 30-60 seconds for most charts)

---

## Next Phase Integration

Once API is complete:
1. Frontend team integrates endpoints into dashboard
2. User plugs API container/service into orchestration
3. Data flows: PostgreSQL → FastAPI → Frontend Dashboard

