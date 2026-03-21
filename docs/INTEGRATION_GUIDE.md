# Integration & Deployment Guide - Parallel Development

## Overview

This document shows how your team will work in **parallel** on the three remaining phases, and how the final assembly will connect everything together. It's the "master blueprint" for coordinating between components.

**Architecture**: PostgreSQL (Phase 1 complete) → FastAPI (Phase 2, your teammate) → Frontend (Phase 3, your teammate) → You plug them together

**Timeline**: Phases 2 & 3 can happen simultaneously (parallel work) → Phase 4 (future)

---

## Parallel Development Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                      YOUR TEAM WORKFLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  You (User) - Phase 1 ✅ COMPLETE                              │
│  ├─ PostgreSQL Database: Loaded 200K+ records                  │
│  ├─ Star Schema: 8 tables with FKs, all working                │
│  ├─ OLAP Indexes: 14 indexes deployed                          │
│  ├─ Materialized Views: 5 views pre-aggregated                 │
│  └─ Status: Ready for API consumption                          │
│                                                                 │
│  Teammate A (Parallel) - Phase 2: FastAPI Service Layer        │
│  ├─ Task: Build 5 REST endpoints consuming materialized views  │
│  ├─ Time: ~2-4 hours (using API_SPECIFICATION.md)              │
│  ├─ Deliverable: api/main.py with 5 working endpoints          │
│  ├─ Testing: Uses cURL, Postman, or test_api.py               │
│  └─ Repo: Commits to /api/ folder in your workspace            │
│                                                                 │
│  Teammate B (Parallel) - Phase 3: Frontend Dashboard           │
│  ├─ Task: Build 5 dashboard pages with charts                  │
│  ├─ Time: ~4-8 hours (using FRONTEND_REQUIREMENTS.md)          │
│  ├─ Deliverable: React/Streamlit app ready to connect to API   │
│  ├─ Testing: Views charts, clicks filters, navigates pages     │
│  └─ Repo: Commits to /dashboard/ folder in your workspace      │
│                                                                 │
│  You (Sequential) - Phase 4: Assembly & Deployment             │
│  ├─ Task 1: Verify API endpoints work independently            │
│  ├─ Task 2: Verify Frontend connects to API                    │
│  ├─ Task 3: Test end-to-end (PostgreSQL → API → Frontend)      │
│  ├─ Task 4: Package into Docker Compose (all 3 services)       │
│  ├─ Task 5: Deploy and monitor                                 │
│  └─ Time: ~1-2 hours (integration & smoke tests)               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Project Structure for Parallel Development

### Folder Layout

```
promptlens-data/
├── warehouse/                   # Phase 1: COMPLETED ✅
│   ├── schema.sql
│   ├── olap_indexes.sql         # NEW (Phase 1)
│   ├── olap_materialized_views.sql  # NEW (Phase 1)
│   ├── load_to_postgres.py
│   └── load_streaming.py
│
├── api/                         # Phase 2: YOUR TEAMMATE
│   ├── main.py                  # FastAPI app (see template below)
│   ├── models.py                # Pydantic request/response schemas
│   ├── database.py              # Database connection pool
│   ├── requirements.txt          # pip dependencies
│   ├── Dockerfile               # Docker image for API
│   ├── .env.example             # Environment variables template
│   └── test_api.py              # Unit tests (optional)
│
├── dashboard/                   # Phase 3: YOUR TEAMMATE
│   ├── app.py                   # Streamlit or React main component
│   ├── pages/                   # (If using Streamlit)
│   │   ├── 1_models.py
│   │   ├── 2_languages.py
│   │   ├── 3_features.py
│   │   ├── 4_prompts.py
│   │   └── 5_summary.py
│   ├── requirements.txt          # pip dependencies (if Streamlit)
│   ├── Dockerfile               # Docker image for frontend
│   └── .env.example
│
├── docs/                        # DOCUMENTATION (you are reading this!)
│   ├── API_SPECIFICATION.md     # Detailed API contract ← SHARE WITH TEAMMATE A
│   ├── FRONTEND_REQUIREMENTS.md # UI/UX specs ← SHARE WITH TEAMMATE B
│   ├── DATABASE_SCHEMA_REFERENCE.md  # DB schema ← SHARE WITH BOTH
│   └── INTEGRATION_GUIDE.md     # This file
│
├── docker-compose.yml           # Phase 4: You'll create this
├── .env.docker                  # Docker environment variables
└── README.md                    # Updated with new phases

```

---

## Teammate A: FastAPI Implementation Guide

### What Teammate A Will Create (api/main.py template)

```python
from fastapi import FastAPI, Query
from psycopg2.pool import SimpleConnectionPool
import os
from datetime import datetime

app = FastAPI(
    title="PromptLens Analytics API",
    description="OLAP analytics endpoints for prompt optimization",
    version="1.0.0"
)

# Database connection pool (read from .env)
connection_pool = SimpleConnectionPool(
    1, 20,
    host=os.getenv("DATABASE_HOST", "localhost"),
    port=int(os.getenv("DATABASE_PORT", 5432)),
    database=os.getenv("DATABASE_NAME", "promptlens"),
    user=os.getenv("DATABASE_USER", "postgres"),
    password=os.getenv("DATABASE_PASSWORD", "")
)

# ============================================================================
# ENDPOINT 1: Model Performance Rankings
# ============================================================================

@app.get("/analytics/model-performance")
async def get_model_performance(
    limit: int = Query(10, ge=1, le=50),
    sort_by: str = Query("avg_success", regex="^(avg_success|attempts|median_success)$"),
    order: str = Query("desc", regex="^(asc|desc)$")
):
    """
    Returns all models ranked by success rate.
    
    - **limit**: Max models to return (1-50)
    - **sort_by**: Field to sort by (avg_success, attempts, median_success)
    - **order**: Sort order (asc, desc)
    
    Returns: Array of model objects with rank, success rate, attempt count
    """
    conn = connection_pool.getconn()
    try:
        cursor = conn.cursor()
        query = f"""
            SELECT 
                ROW_NUMBER() OVER (ORDER BY {sort_by} {order.upper()}) as rank,
                model_name,
                attempts,
                avg_success,
                median_success,
                ROUND(avg_success * 100, 2) as success_rate_pct
            FROM mv_model_performance_arena
            LIMIT %s
        """
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": "success",
            "total_count": len(rows),
            "data": [
                {
                    "rank": row[0],
                    "model_name": row[1],
                    "attempts": row[2],
                    "avg_success": float(row[3]),
                    "median_success": float(row[4]),
                    "success_rate_pct": float(row[5])
                }
                for row in rows
            ]
        }
    except Exception as e:
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": "error",
            "error": {"code": "DATABASE_ERROR", "message": str(e)}
        }
    finally:
        connection_pool.putconn(conn)

# ============================================================================
# ENDPOINT 2: Language Performance (similar structure)
# ============================================================================

@app.get("/analytics/language-performance")
async def get_language_performance(
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("success_rate", regex="^(success_rate|prompts|median_success)$"),
    order: str = Query("desc", regex="^(asc|desc)$")
):
    """Language difficulty ranking"""
    conn = connection_pool.getconn()
    try:
        cursor = conn.cursor()
        query = f"""
            SELECT 
                programming_lang,
                prompts,
                success_rate,
                median_success,
                CASE 
                    WHEN success_rate > 0.75 THEN 'easy'
                    WHEN success_rate > 0.50 THEN 'medium'
                    ELSE 'hard'
                END as difficulty_level
            FROM mv_language_performance
            WHERE prompts >= 1
            LIMIT %s
        """
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": "success",
            "total_languages": len(rows),
            "data": [
                {
                    "programming_language": row[0],
                    "total_prompts": row[1],
                    "success_rate": float(row[2]),
                    "median_success": float(row[3]),
                    "difficulty_level": row[4]
                }
                for row in rows
            ]
        }
    except Exception as e:
        return {"timestamp": datetime.utcnow().isoformat() + "Z", "status": "error", "error": {"code": "DATABASE_ERROR", "message": str(e)}}
    finally:
        connection_pool.putconn(conn)

# ============================================================================
# ENDPOINT 3: Prompt Features (similar structure)
# ============================================================================

@app.get("/analytics/prompt-features")
async def get_prompt_features(
    limit: int = Query(8, ge=1, le=16),
    min_samples: int = Query(10, ge=1),
    sort_by: str = Query("avg_success", regex="^(avg_success|cnt|median_success)$")
):
    """Feature impact analysis"""
    # Similar pattern: query mv_prompt_feature_impact
    # Return feature combinations with impact scores
    pass

# ============================================================================
# ENDPOINT 4: Top Prompts (similar structure)
# ============================================================================

@app.get("/analytics/top-prompts")
async def get_top_prompts(
    limit: int = Query(10, ge=1, le=100),
    min_uses: int = Query(5, ge=1),
    sort_by: str = Query("avg_success", regex="^(avg_success|uses|median_success)$")
):
    """Best-performing prompt templates"""
    # Similar pattern: query mv_top_prompt_templates
    pass

# ============================================================================
# ENDPOINT 5. Time-Series Model Performance (similar structure)
# ============================================================================

@app.get("/analytics/model-performance-timeline")
async def get_model_performance_timeline(
    model_name: str = Query(None),
    days: int = Query(30, ge=1, le=365),
    sort_by: str = Query("day")
):
    """
    30-day performance trend per model
    Similar pattern: query mv_daily_model_success with date filter
    """
    pass

# ============================================================================
# HEALTH CHECK (bonus)
# ============================================================================

@app.get("/health")
async def health_check():
    """Check if API and database are healthy"""
    conn = connection_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except:
        return {"status": "unhealthy", "database": "disconnected"}
    finally:
        connection_pool.putconn(conn)

# ============================================================================
# API DOCUMENTATION
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    # Swagger docs at: http://localhost:8000/docs
```

### Environment Variables for Teammate A

**File: api/.env.example**
```
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=promptlens
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password_here
API_HOST=0.0.0.0
API_PORT=8000
```

### Testing Endpoints (Teammate A Checklist)

```bash
# 1. Test health check
curl http://localhost:8000/health

# 2. Test model performance
curl "http://localhost:8000/analytics/model-performance?limit=5"

# 3. Test language performance
curl "http://localhost:8000/analytics/language-performance?limit=10"

# 4. Test features
curl "http://localhost:8000/analytics/prompt-features"

# 5. Test top prompts
curl "http://localhost:8000/analytics/top-prompts?limit=10"

# 6. Test timeline (30 days of data)
curl "http://localhost:8000/analytics/model-performance-timeline?days=30"

# 7. Swagger documentation (auto-generated)
# Open browser: http://localhost:8000/docs
```

---

## Teammate B: Frontend Implementation Guide

### What Teammate B Will Create

**If using Streamlit** (simplest, 2-3 hours):
```python
# dashboard/app.py
import streamlit as st
import pandas as pd
import requests
import plotly.express as px

API_URL = st.secrets["api_url"]  # From .streamlit/secrets.toml

st.set_page_config(page_title="PromptLens Analytics", layout="wide")

# Sidebar navigation
page = st.sidebar.radio("Navigation", [
    "Model Performance",
    "Language Difficulty",
    "Feature Impact",
    "Top Prompts",
    "Summary"
])

if page == "Model Performance":
    st.title("🏆 Model Performance Rankings")
    
    # Fetch data from API
    response = requests.get(f"{API_URL}/analytics/model-performance?limit=15")
    data = response.json()["data"]
    df = pd.DataFrame(data)
    
    # Display leaderboard
    st.dataframe(df[["rank", "model_name", "success_rate_pct", "attempts"]], use_container_width=True)
    
    # Fetch timeline data
    response_timeline = requests.get(f"{API_URL}/analytics/model-performance-timeline?days=30")
    timeline_data = response_timeline.json()["data"]
    
    # Plot trend
    fig = px.line(timeline_data, x="date", y="avg_success", color="model_name")
    st.plotly_chart(fig, use_container_width=True)

elif page == "Language Difficulty":
    # Similar pattern for other pages
    pass

# ... etc for other pages
```

**If using React** (more complex, 4-6 hours):
```jsx
// dashboard/src/pages/ModelPerformance.jsx
import React, { useEffect, useState } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function ModelPerformance() {
  const [models, setModels] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    
    Promise.all([
      fetch(`${process.env.REACT_APP_API_URL}/analytics/model-performance?limit=15`).then(r => r.json()),
      fetch(`${process.env.REACT_APP_API_URL}/analytics/model-performance-timeline?days=30`).then(r => r.json())
    ]).then(([modelsData, timelineData]) => {
      setModels(modelsData.data);
      setTimeline(timelineData.data);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div className="page-content">
      <h1>🏆 Model Performance Rankings</h1>
      
      <table className="leaderboard">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Model</th>
            <th>Success Rate</th>
            <th>Attempts</th>
          </tr>
        </thead>
        <tbody>
          {models.map((m) => (
            <tr key={m.model_name}>
              <td>{m.rank}</td>
              <td>{m.model_name}</td>
              <td>{(m.success_rate_pct).toFixed(2)}%</td>
              <td>{m.attempts}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={timeline}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="avg_success" stroke="#8884d8" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default ModelPerformance;
```

### Environment for Teammate B

**File: dashboard/.env.example**
```
# Streamlit
STREAMLIT_API_URL=http://localhost:8000

# React
REACT_APP_API_URL=http://localhost:8000
REACT_APP_REFRESH_INTERVAL=60000
```

---

## Phase 4: Integration (YOUR JOB - The Assembly)

Once both teammates deliver their code, you'll orchestrate the final integration.

### Integration Checklist

- [ ] **Step 1**: Verify API endpoints independently
  ```bash
  # Test each endpoint manually
  curl http://localhost:8000/analytics/model-performance
  curl http://localhost:8000/analytics/language-performance
  # ... etc
  ```

- [ ] **Step 2**: Verify Frontend connects to API
  ```bash
  # Run frontend and check browser console for errors
  # Should see data loading, charts rendering
  ```

- [ ] **Step 3**: End-to-end test (PostgreSQL → API → Frontend)
  ```bash
  # Verify data flows: DB query → API response → Dashboard display
  # Sample: Click filter on dashboard → API filters → New data displays
  ```

- [ ] **Step 4**: Package into Docker Compose
  ```yaml
  # docker-compose.yml (you'll create this)
  version: '3.8'
  services:
    postgres:
      image: postgres:15
      environment:
        POSTGRES_DB: promptlens
        POSTGRES_USER: postgres
        POSTGRES_PASSWORD: your_password
      volumes:
        - ./warehouse/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
        - ./warehouse/olap_indexes.sql:/docker-entrypoint-initdb.d/03-indexes.sql
        - ./warehouse/olap_materialized_views.sql:/docker-entrypoint-initdb.d/04-views.sql
      ports:
        - "5432:5432"

    api:
      build:
        context: ./api
        dockerfile: Dockerfile
      environment:
        DATABASE_HOST: postgres
        DATABASE_PORT: 5432
        DATABASE_NAME: promptlens
        DATABASE_USER: postgres
        DATABASE_PASSWORD: your_password
      ports:
        - "8000:8000"
      depends_on:
        - postgres

    dashboard:
      build:
        context: ./dashboard
        dockerfile: Dockerfile
      environment:
        REACT_APP_API_URL: http://api:8000
      ports:
        - "3000:3000"  # React
        # - "8501:8501"  # Streamlit alternative
      depends_on:
        - api
  ```

- [ ] **Step 5**: Start full stack
  ```bash
  docker-compose up --build
  # Access:
  # - API docs: http://localhost:8000/docs
  # - Dashboard: http://localhost:3000 (React) or http://localhost:8501 (Streamlit)
  # - Database: localhost:5432
  ```

- [ ] **Step 6**: Smoke tests
  ```bash
  # Verify all 5 endpoints return data
  # Verify dashboards display charts
  # Verify filters/sorts work end-to-end
  # Verify data consistency (same numbers in dashboard as API)
  ```

---

## Development Timeline

### Week 1: Parallel Work (Teammates work simultaneously)

| Timeframe | Teammate A (API) | Teammate B (Frontend) | You |
|-----------|------------------|----------------------|-----|
| Day 1-2 | Read API_SPECIFICATION.md | Read FRONTEND_REQUIREMENTS.md | Monitor, answer questions |
| Day 2-3 | Implement 5 endpoints | Set up frontend project | Monitor, answer questions |
| Day 3-4 | Test endpoints with cURL/Postman | Build dashboard pages | Monitor, answer questions |
| Day 4-5 | Debug, document API | Debug frontend, wire to API | Monitor, answer questions |

### Week 2: Integration (You orchestrate)

| Timeframe | Task |
|-----------|------|
| Day 1 | Merge teammates' code, test independently |
| Day 1-2 | Troubleshoot integration issues |
| Day 2 | Package into Docker Compose |
| Day 2-3 | Full smoke testing |
| Day 3 | Deploy to staging/production |

---

## Communication & Issue Escalation

### Regular Checkins

**Daily (15 min standup)**:
- Teammate A: "Implemented endpoints 1-3, testing now. Need schema clarification on X."
- Teammate B: "Built page structure, fetching model data. API response time is fast!"
- You: Answer questions, unblock issues

**Issue Template** (use chat or email):
```
Issue: [API returning null values] / [Frontend not rendering charts] / etc
Teammate: [Name]
Severity: [Critical/High/Medium/Low]
Screenshot/Error: [paste error message]
Blocking: [Yes/No]
Question: [What's expected behavior?]
```

### Common Questions to Answer

- **API Question**: "How do I connect to the database from Python?"
  - Answer: Show .env.example template
  
- **Frontend Question**: "What's the expected JSON format from /analytics/model-performance?"
  - Answer: Point to API_SPECIFICATION.mdexample responses
  
- **Data Question**: "Why are some models missing from the data?"
  - Answer: Check DATABASE_SCHEMA_REFERENCE.md → dim_model table

---

## Troubleshooting During Parallel Development

### Scenario 1: API Endpoints Timeout

**Problem**: `/analytics/model-performance` takes >5 seconds
**Solution**: 
- Check PostgreSQL is running and responsive
- Verify materialized views exist: `SELECT COUNT(*) FROM mv_model_performance_arena;`
- Check database indexes were created: `SELECT * FROM pg_indexes WHERE tablename LIKE 'fact_%';`

### Scenario 2: Frontend Can't Connect to API

**Problem**: Dashboard shows "Cannot reach API"
**Solution**:
- Verify API is running: `curl http://localhost:8000/health`
- Check CORS headers in API (FastAPI auto-enables)
- Verify .env has correct API_URL (http://localhost:8000, not http://localhost:3000)

### Scenario 3: Data Mismatch (API shows 15 models, frontend shows 10)

**Problem**: Data inconsistency between API and dashboard
**Solution**:
- Check API response limit parameter: `?limit=10` vs `?limit=15`
- Verify both are querying same view: `mv_model_performance_arena`
- Check pagination/filtering logic

---

## Handoff Checklist (Teammate → You)

### Teammate A (API) Deliverables

- [ ] `/api/main.py` with all 5 endpoints working
- [ ] `/api/requirements.txt` with all dependencies
- [ ] `/api/.env.example` template
- [ ] `/api/Dockerfile` for containerization
- [ ] **README** in `/api/` explaining how to run locally
- [ ] Test results showing all endpoints return data
- [ ] Example cURL commands showing each endpoint

### Teammate B (Frontend) Deliverables

- [ ] `/dashboard/` folder with complete app
- [ ] `/dashboard/requirements.txt` (if Streamlit) or `package.json` (if React)
- [ ] `/dashboard/.env.example` template
- [ ] `/dashboard/Dockerfile` for containerization
- [ ] **README** in `/dashboard/` explaining how to run locally
- [ ] Screenshots of each page
- [ ] List of all API endpoints consumed + expected data format

---

## Phase 5: Optional - ML Model Integration

Once Phases 2-4 are complete, Phase 5 can add:

```
/ml/clustering-results
/ml/association-rules
/ml/feature-importance
```

These would consume models from `ml_service/models/`:
- `association_rules.json`
- `training_summary.json`

---

## Final Deployment Verification

```bash
# 1. Start full stack
docker-compose up --build

# 2. Wait for services to be healthy
sleep 10

# 3. Test each endpoint
curl -s http://localhost:8000/health | jq .
curl -s http://localhost:8000/analytics/model-performance | jq '.data | length'
curl -s http://localhost:8000/analytics/language-performance | jq '.data | length'
curl -s http://localhost:8000/analytics/prompt-features | jq '.data | length'
curl -s http://localhost:8000/analytics/top-prompts | jq '.data | length'

# 4. Open dashboard in browser
# http://localhost:3000 (React) or http://localhost:8501 (Streamlit)

# 5. Verify data flows end-to-end
# - Load page
# - Check network tab (API calls successful)
# - Check data displays in charts
# - Try filter/sort (data updates)

# 6. Check logs for errors
docker-compose logs api
docker-compose logs dashboard
docker-compose logs postgres
```

---

## Success Criteria

✅ **Project Complete When**:

1. All 5 API endpoints return valid data in <500ms
2. All 5 dashboard pages load and display charts
3. Filters/sorts on dashboard update data correctly
4. All services run in Docker Compose without errors
5. End-to-end test passes: modify database → API reflects change → dashboard shows change
6. Team can demonstrate full workflow to stakeholders

---

## Questions? Documentation Index

- **"How do I build the API?"** → [API_SPECIFICATION.md](API_SPECIFICATION.md)
- **"What should the dashboard look like?"** → [FRONTEND_REQUIREMENTS.md](FRONTEND_REQUIREMENTS.md)
- **"What data is available?"** → [DATABASE_SCHEMA_REFERENCE.md](DATABASE_SCHEMA_REFERENCE.md)
- **"How do we integrate everything?"** → [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) ← you are here
- **"How do we query the database?"** → [DATABASE_SCHEMA_REFERENCE.md](DATABASE_SCHEMA_REFERENCE.md) → Example Queries section

