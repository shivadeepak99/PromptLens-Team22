# Team Quick Start Checklist

**Print this. Share with your teammates. They'll love you.**

---

## 🚀 Team 1: API Backend Developer

### Your Mission
Build 5 REST API endpoints that expose database queries and ML models.

### Day 1 (Setup)
- [ ] Clone GitHub repo: `PromptLens_DataMining_Team`
- [ ] Install Python 3.9+: `python --version`
- [ ] Create `api/` folder
- [ ] Install packages: 
  ```bash
  pip install fastapi uvicorn psycopg2-binary pydantic joblib
  ```
- [ ] Create `api/.env` with PostgreSQL credentials (from Team Lead Shiva)
- [ ] Test database connection:
  ```python
  import psycopg2
  conn = psycopg2.connect("dbname=promptlens user=postgres...")
  print("✓ Connected!")
  ```

### Days 2-3 (Development)
- [ ] Create `api/main.py` with basic FastAPI app:
  ```python
  from fastapi import FastAPI
  app = FastAPI()
  
  @app.get("/analytics/model-performance")
  async def get_model_performance():
      # Query materialized view: mv_model_performance_arena
      pass
  ```
- [ ] Implement 5 endpoints (see DETAILED spec in `PARALLEL_WORK_COORDINATION.md`):
  1. `/analytics/model-performance` [GET]
  2. `/analytics/language-performance` [GET]
  3. `/analytics/prompt-features` [GET]
  4. `/ml/success-prediction` [POST]
  5. `/ml/association-rules` [GET]

### Day 4 (Testing & Documentation)
- [ ] Test each endpoint with sample requests
- [ ] Generate OpenAPI docs: `http://localhost:8000/docs`
- [ ] Create `api/README.md` with setup instructions
- [ ] Create `api/requirements.txt`:
  ```
  fastapi==0.104.1
  uvicorn==0.24.0
  psycopg2-binary==2.9.9
  pydantic==2.5.0
  joblib==1.3.2
  ```
- [ ] Push to GitHub

### Critical Resources
- **Database Connection:** Contact Shiva for `.env`
- **API Spec:** See `docs/PARALLEL_WORK_COORDINATION.md` (Endpoint Specifications section)
- **ML Models:** Load from `ml_service/models/` (Python pickle files)
- **Materialized Views:** Query these (all pre-created):
  - `mv_daily_model_success`
  - `mv_model_performance_arena`
  - `mv_language_performance`
  - `mv_prompt_feature_impact`
  - `mv_top_prompt_templates`

### ✅ Done When
- All 5 endpoints tested
- Swagger docs complete
- Code pushed to GitHub
- Team 3 can start using your API

---

## 🐉 Team 2: R Data Analyst

### Your Mission
Run 4 R scripts, generate 12 visualizations, write findings document.

### Day 1 (Setup)
- [ ] Install R 4.0+ (Windows/Mac/Linux)
- [ ] Open RStudio or R console
- [ ] Install packages (one-time):
  ```r
  source("requirements.R")
  # Downloads & installs 20+ packages
  ```
- [ ] Create folder structure in project:
  ```bash
  mkdir -p data/raw data/processed scripts results/figures results/tables
  ```
- [ ] Get PostgreSQL credentials from Shiva, create `.env` file:
  ```
  DB_HOST=localhost
  DB_PORT=5432
  DB_NAME=promptlens
  DB_USER=postgres
  DB_PASSWORD=your_password
  ```

### Day 2-3 (Run Scripts in Sequence)
**Each script takes care of itself. Just run them:**

```r
# Script 1: Load data (30 min)
source("scripts/01_data_preparation.R")
# Output: data/processed/promptlens_clean.RData

# Script 2: Create visualizations (1-2 hours)
source("scripts/02_exploratory_analysis.R")
# Output: 8 PNG files + 3 CSV tables

# Script 3: Validate models (1-2 hours)
source("scripts/03_modeling_validation.R")
# Output: 4 PNG files + 2 CSV tables

# Script 4: Final report (30 min)
source("scripts/04_evaluation.R")
# Output: FINDINGS.txt, RECOMMENDATIONS.txt
```

### Day 4 (Verification)
- [ ] Check that `results/figures/` has 12 PNG files
- [ ] Check that `results/tables/` has 6 CSV files
- [ ] Read `results/FINDINGS.txt` (key insights)
- [ ] Push everything to GitHub

### Critical Details
- **All scripts are SELF-CONTAINED** — no manual edits needed
- **Scripts must run in order** — each depends on previous output
- **PostgreSQL data loaded?** Check: 
  ```r
  conn <- dbConnect(PostgreSQL(), ...) # Should connect
  fact <- dbGetQuery(conn, "SELECT COUNT(*) FROM fact_promptexecution")
  # Should show 200K+ rows
  ```

### ✅ Done When
- 12 PNG figures in `results/figures/`
- 6 CSV tables in `results/tables/`
- `results/FINDINGS.txt` readable
- All code pushed to GitHub

---

## 🎨 Team 3: Frontend/Dashboard Developer

### Your Mission
Build interactive dashboard consuming API from Team 1.

### Day 1 (Waiting)
**⏳ Start after Team 1 finishes (Day 4)**
- [ ] Clone GitHub repo
- [ ] Install Python 3.9+
- [ ] Install Streamlit:
  ```bash
  pip install streamlit requests pandas plotly
  ```
- [ ] While waiting, review API spec in `PARALLEL_WORK_COORDINATION.md`

### Day 2 (Skeleton)
Once Team 1 shares API docs:
- [ ] Get list of 5 API endpoints from Team 1
- [ ] Test each endpoint manually:
  ```bash
  curl http://localhost:8000/analytics/model-performance
  ```
- [ ] Create `app/dashboard.py`:
  ```python
  import streamlit as st
  import requests
  
  st.set_page_config(page_title="PromptLens", layout="wide")
  st.title("🔍 PromptLens Dashboard")
  
  # Tab 1: Model Performance
  with st.tabs(["Model Performance", "Languages", "Features", 
                "Clusters", "Rules"]):
      st.subheader("Model Performance")
      response = requests.get("http://localhost:8000/analytics/model-performance")
      st.dataframe(response.json())
  ```

### Day 3-4 (Development)
Build 5 dashboard sections (one per API endpoint):
1. **Model Performance** — Bar chart + table ranking models
2. **Language Analysis** — Interactive filter by programming language
3. **Feature Impact** — Toggle contains_examples, contains_code, etc.
4. **Prompt Clusters** — Cluster explorer + statistics
5. **Association Rules** — Rule browser + confidence/lift filters

### Day 5 (Polish & Deploy)
- [ ] Test dashboard locally:
  ```bash
  streamlit run app/dashboard.py
  # Opens http://localhost:8501
  ```
- [ ] Add screenshots to `app/README.md`
- [ ] Deploy to Streamlit Cloud (free):
  ```bash
  streamlit cloud deploy app/dashboard.py
  ```
- [ ] Push to GitHub

### ✅ Done When
- Dashboard runs without errors
- All 5 sections populated with data
- API calls working correctly
- Screenshots in README
- Deployed or deployable

---

## 👑 You (Team Lead - Shiva)

### Your Role
Coordinate, integrate, validate, prepare submission.

### Day 1-7: Monitoring
- [ ] Send this checklist to all 3 teammates
- [ ] Create GitHub repository (public)
- [ ] Add teammates as collaborators
- [ ] Create `.env` file with PostgreSQL credentials (shared securely)
- [ ] Set up folder structure
- [ ] Daily: Ask each team for updates
  - Team 1: "API done? Which endpoints working?"
  - Team 2: "Scripts running? Any errors?"
  - Team 3: "Dashboard ready to start?"

### Day 8-9: Integration
- [ ] Merge all three repos into main branch
- [ ] Copy `docs/README_TEMPLATE_FOR_SUBMISSION.md` → README.md
- [ ] Update README with:
  - [ ] Team member names & roll numbers
  - [ ] Screenshots from dashboard
  - [ ] Sample API outputs
  - [ ] How to install & run everything
- [ ] Create presentation (15 slides):
  ```
  1. Title slide
  2. Problem statement
  3. Data pipeline diagram
  4. Star schema (draw it)
  5-7. Top 3 visualizations from Team 2
  8. Clustering results
  9. Classification metrics
  10. Association rules
  11. Key findings
  12. API architecture (diagram)
  13. Dashboard screenshot
  14. Recommendations
  15. Thank you / Future work
  ```
- [ ] Save presentation as `presentation/project_presentation.pptx`

### Day 9: Final Checks
- [ ] Test R scripts (run all 4):
  ```bash
  R --vanilla -f scripts/01_data_preparation.R
  R --vanilla -f scripts/02_exploratory_analysis.R
  R --vanilla -f scripts/03_modeling_validation.R
  R --vanilla -f scripts/04_evaluation.R
  ```
- [ ] Test API (all 5 endpoints):
  ```bash
  python -m uvicorn api.main:app --reload
  curl http://localhost:8000/analytics/model-performance
  ```
- [ ] Test dashboard:
  ```bash
  streamlit run app/dashboard.py
  ```
- [ ] Verify README complete
- [ ] Verify all figures in `results/figures/`
- [ ] Verify all tables in `results/tables/`
- [ ] Push final version to GitHub

### ✅ Submission Ready When
- [ ] GitHub repo contains everything
- [ ] All scripts run without errors
- [ ] README follows professor's format exactly
- [ ] Presentation is professional (15 slides)
- [ ] All 4 team members are listed as collaborators
- [ ] Repo is public (anyone can view)

---

## 📋 File Checklist (Final)

```
PromptLens_DataMining_Team/
│
├── README.md ✅ (CRITICAL - follows professor's format)
├── requirements.R
├── .env (NOT in git - credentials)
│
├── scripts/ (FROM TEAM 2)
│   ├── 01_data_preparation.R
│   ├── 02_exploratory_analysis.R
│   ├── 03_modeling_validation.R
│   ├── 04_evaluation.R
│   └── helpers.R (optional)
│
├── results/ (FROM TEAM 2 - AUTO-GENERATED)
│   ├── figures/
│   │   ├── 01_success_distribution.png
│   │   ├── 02_feature_impact.png
│   │   ├── 03_correlation_heatmap.png
│   │   ├── 04_model_performance.png
│   │   ├── 05_task_difficulty.png
│   │   ├── 06_daily_trends.png
│   │   ├── 07_latency_distribution.png
│   │   ├── 08_prompt_length_effect.png
│   │   ├── 09_silhouette_analysis.png
│   │   ├── 10_cluster_visualization.png
│   │   ├── 11_feature_importance.png
│   │   └── 12_association_rules.png
│   ├── tables/
│   │   ├── 01_data_summary.csv
│   │   ├── 02_model_performance.csv
│   │   ├── 03_summary_statistics.csv
│   │   ├── 04_cluster_characteristics.csv
│   │   ├── 05_association_rules.csv
│   │   └── 06_model_evaluation.csv
│   ├── FINDINGS.txt
│   └── RECOMMENDATIONS.txt
│
├── data/ (FROM TEAM 2)
│   ├── dataset_description.md
│   ├── raw/ (PostgreSQL connection details)
│   └── processed/
│       ├── promptlens_clean.RData
│       └── promptlens_clean.csv
│
├── api/ (FROM TEAM 1)
│   ├── main.py
│   ├── models.py (Pydantic schemas)
│   ├── database.py
│   ├── ml_loader.py
│   ├── requirements.txt
│   └── README.md
│
├── app/ (FROM TEAM 3)
│   ├── dashboard.py
│   ├── requirements.txt
│   └── README.md
│
├── presentation/
│   └── project_presentation.pptx (FROM YOU)
│
├── docs/
│   ├── ML_MODELS_DOCUMENTATION.md (already created)
│   ├── R_ANALYSIS_GUIDE.md (already created)
│   ├── README_TEMPLATE_FOR_SUBMISSION.md (template - becomes README.md)
│   ├── PARALLEL_WORK_COORDINATION.md (already created)
│   └── DATABASE_SCHEMA.md (optional - schema details)
│
└── .gitignore
    .env (credentials - never commit)
    data/raw/*.csv (if too large)
    __pycache__/
    .Rhistory
    *.RData (optional - are 100MB+)
```

---

## 🎯 Success Looks Like...

**Team 1 says:**
> "API is running, all 5 endpoints tested, Swagger docs auto-generated. Team 3 can start building dashboard now."

**Team 2 says:**
> "All 4 scripts ran end-to-end. Generated 12 figures and 6 CSV tables. Key finding: GPT-4 outperforms others by 23%, examples increase success +12%."

**Team 3 says:**
> "Dashboard is live! Shows model rankings, lets you explore features, runs predictions. Deployed to Streamlit Cloud."

**You say:**
> "Everything is merged, README is perfect, presentation is ready, repo is public. Let's submit!"

---

## 🆘 If You Get Stuck

| Problem | Solution |
|--|--|
| Can't connect to PostgreSQL | Get `.env` from Shiva, test: `psql -U postgres -d promptlens` |
| R packages won't install | Run: `install.packages(c("dplyr", "ggplot2", ...))` |
| API endpoint returns 500 error | Check PostgreSQL connection, check column names match schema |
| Dashboard slow | Cache API results: `@st.cache_data` decorator |
| Git merge conflicts | Communicate! Work on different files. |

---

## 📞 Get Help

- **Database issues?** → Shiva
- **R script errors?** → Shiva
- **API design questions?** → Shiva
- **Dashboard UI help?** → Shiva
- **GitHub workflow?** → Shiva

**Bottom line:** Shiva knows the whole system. Ask questions early.

---

## 🚀 Ready?

Print this. Share it. Follow it. You've got this!

**Timeline:** 9 days to a complete, polished, submission-ready data mining project.

**Good luck! 🎓**

---

*Last updated: March 20, 2026 | For CSS321 Data Mining Course*
