# TEAMMATE TASKS - YOUR ASSIGNMENT

## For: Teammates A (Backend/API) and B (Frontend/Dashboard)

This is the **executive summary** of what YOU need to build. Read this first, then dive into the detailed spec documents.

---

## 🎯 THE BIG PICTURE

```
PHASE 1 (COMPLETE) ✅             PHASE 2 (YOUR JOB)          PHASE 3 (YOUR JOB)
PostgreSQL OLAP Infrastructure  →  FastAPI REST Endpoints  →  Frontend Dashboard
- 8 tables, fully loaded        →  5 API routes            →  5 pages with charts
- 14 indexes                    →  200K+ records queryable →  Real-time data display
- 5 materialized views          →  <500ms response time    →  Interactive filters
```

**OUTPUT**: Two independent services that you'll deliver to your lead, who will integrate them.

---

## 👨‍💻 TEAMMATE A: FastAPI Backend Service (You Build)

### Your Task
Build a REST API with **5 endpoints** that query PostgreSQL materialized views.

### Time Estimate
**2-4 hours** (depending on experience)

### What You'll Deliver
- `api/main.py` - FastAPI application with 5 working endpoints
- `api/requirements.txt` - Python dependencies
- `api/Dockerfile` - Container image
- `api/.env.example` - Configuration template
- `api/README.md` - How to run it locally
- Working endpoints tested with cURL

### The 5 Endpoints You Need to Build

| # | Endpoint | Database View | Returns | Example Use |
|---|----------|---------------|---------|------------|
| 1 | `GET /analytics/model-performance` | `mv_model_performance_arena` | Top models ranked by success rate | "Which model performs best?" |
| 2 | `GET /analytics/language-performance` | `mv_language_performance` | Programming languages ranked by difficulty | "Which language is easiest?" |
| 3 | `GET /analytics/prompt-features` | `mv_prompt_feature_impact` | Feature combinations and their impact | "Do examples help success?" |
| 4 | `GET /analytics/top-prompts` | `mv_top_prompt_templates` | Best-performing prompt templates | "What prompts work best?" |
| 5 | `GET /analytics/model-performance-timeline` | `mv_daily_model_success` | Model performance trend (30 days) | "Is gpt-4 improving?" |

### What You Don't Need to Do
- ❌ Load or transform data (that's done)
- ❌ Build the dashboard (Teammate B does that)
- ❌ Set up PostgreSQL (it's already running with data)
- ❌ Write authentication/security (use simple access for now)

### Expected Response Format (All Endpoints)
```json
{
  "timestamp": "2024-03-20T10:30:00Z",
  "status": "success",
  "data": [...],
  "total_count": 15
}
```

### Database Connection Details
```
Host: localhost
Port: 5432
Database: promptlens
User: postgres
Password: [provided by lead]
```

### Quick Start Checklist
- [ ] Create `/api` folder with `main.py`
- [ ] Install dependencies: `pip install fastapi uvicorn psycopg2-binary`
- [ ] Copy `/docs/API_SPECIFICATION.md` - READ THIS FIRST (detailed endpoint specs)
- [ ] Implement endpoint 1: model-performance
- [ ] Test with: `curl http://localhost:8000/analytics/model-performance`
- [ ] Repeat for endpoints 2-5
- [ ] Test Swagger docs: http://localhost:8000/docs
- [ ] Commit code to `/api` folder

### Key Files to Reference
- **API_SPECIFICATION.md** ← **START HERE** (detailed contract, examples, error codes)
- **DATABASE_SCHEMA_REFERENCE.md** (explains the 5 views you'll query)

### Testing Your Work
```bash
# Run the API
python -m uvicorn api.main:app --reload

# Test each endpoint (in another terminal)
curl http://localhost:8000/analytics/model-performance?limit=5
curl http://localhost:8000/analytics/language-performance
curl http://localhost:8000/analytics/prompt-features
curl http://localhost:8000/analytics/top-prompts?limit=10
curl http://localhost:8000/analytics/model-performance-timeline?days=30

# Open Swagger UI in browser (auto-generated docs)
http://localhost:8000/docs
```

### Success Criteria
✅ All 5 endpoints return data  
✅ Response time < 500ms per endpoint  
✅ JSON format matches API_SPECIFICATION.md  
✅ No database connection errors  
✅ Swagger docs work at `/docs`

---

## 👩‍🎨 TEAMMATE B: Frontend Dashboard Service (You Build)

### Your Task
Build a web dashboard with **5 pages** that visualize API data from Teammate A.

### Time Estimate
**4-8 hours** (depending on framework & experience)

### What You'll Deliver
- `dashboard/app.py` (if Streamlit) or `dashboard/src/App.jsx` (if React) - Complete app
- `dashboard/requirements.txt` (if Streamlit) or `package.json` (if React) - Dependencies
- `dashboard/Dockerfile` - Container image
- `dashboard/.env.example` - Configuration template
- `dashboard/README.md` - How to run it locally
- Screenshots of all 5 pages
- No errors in browser console

### The 5 Pages You Need to Build

| # | Page | URL | Shows | Data from API |
|---|------|-----|-------|---------------|
| 1 | Model Performance | `/` or `/models` | Models ranked by success + 30-day trend chart | `/analytics/model-performance` + `/analytics/model-performance-timeline` |
| 2 | Language Difficulty | `/languages` | Languages ranked by difficulty + color-coded table | `/analytics/language-performance` |
| 3 | Feature Impact | `/features` | How prompt features affect success (heatmap) | `/analytics/prompt-features` |
| 4 | Top Prompts | `/prompts` | Best-performing prompt templates (searchable) | `/analytics/top-prompts` |
| 5 | Summary (Optional) | `/summary` | Executive dashboard with KPIs & mini charts | All endpoints aggregated |

### What You Don't Need to Do
- ❌ Set up the database (it's running)
- ❌ Build the API (Teammate A does that)
- ❌ Deploy infrastructure (lead does that)
- ❌ Implement authentication (use simple access for now)

### Technology Recommendations

**Option A: Streamlit (Simplest, 2-3 hours)**
- **Pros**: No frontend skills needed, rapid development, Python-only
- **Cons**: Less customizable styling, limited interactivity
- **Best for**: Quick MVP, data engineer teams
- **Framework**: Python + Streamlit + Plotly/Matplotlib

**Option B: React (More Control, 4-6 hours)**
- **Pros**: Beautiful UI, full customization, responsive design
- **Cons**: Requires JavaScript/Node, more initial setup
- **Best for**: Production dashboards, modern UX
- **Tech Stack**: React + TypeScript + Recharts/Plotly.js

**Recommendation**: Start with **Streamlit** (faster delivery), upgrade to React later if needed.

### Expected UI Components

**Page 1 (Model Performance)**:
- Metric cards: Total models, top model, highest success rate
- Leaderboard table: Model name, success rate %, attempt count
- Line chart: Success rate trend over 30 days (toggle models on/off)
- Controls: Sort by, limit, auto-refresh toggle

**Page 2 (Language Difficulty)**:
- Metric cards: Easiest language, hardest language, total languages
- Difficulty table: Language, success rate, difficulty level (color-coded)
- Bar chart: Horizontal bar showing difficulty ranking
- Controls: Min samples filter, sort by

**Page 3 (Feature Impact)**:
- Heatmap/Matrix: Feature combinations vs success rate
- Detailed table: Show all 8 feature combinations ranked
- Insights: Auto-generated text (e.g., "Best: Examples + Code")

**Page 4 (Top Prompts)**:
- Metric cards: Total unique templates, top success rate, most reused
- Table: Prompt preview, success rate, use count, "View" button
- Modal/Drawer: Click row to see full prompt text
- Controls: Min uses filter, search box, sort by

**Page 5 (Summary - Optional)**:
- KPI cards: Models, languages, templates, success rate
- Mini charts: Top 5 models, top 5 languages, success trend
- Quick links: Navigation to detailed pages

### Quick Start Checklist

**If using Streamlit**:
- [ ] Create `/dashboard` folder with `app.py`
- [ ] Install: `pip install streamlit requests pandas plotly`
- [ ] Copy `/docs/FRONTEND_REQUIREMENTS.md` - READ THIS FIRST
- [ ] Create page 1 (model performance) with table + line chart
- [ ] Fetch data from API: `requests.get("http://localhost:8000/analytics/...")`
- [ ] Add pages 2-5 (similar pattern)
- [ ] Test: `streamlit run app.py`
- [ ] Commit code to `/dashboard` folder

**If using React**:
- [ ] `npx create-react-app dashboard`
- [ ] Install: `npm install recharts axios`
- [ ] Create `/src/pages/` folder with 5 page components
- [ ] Create `/src/api.js` - API client to fetch from Teammate A's endpoints
- [ ] Build page 1 (models) with Table + LineChart
- [ ] Repeat for pages 2-5
- [ ] Test: `npm start`
- [ ] Commit code to `/dashboard` folder

### Key Files to Reference
- **FRONTEND_REQUIREMENTS.md** ← **START HERE** (detailed UI/UX specs, colors, fonts, layout)
- **API_SPECIFICATION.md** (understand the JSON format from API endpoints)
- **DATABASE_SCHEMA_REFERENCE.md** (understand what the data means)

### Testing Your Work

**Streamlit**:
```bash
streamlit run dashboard/app.py
# Open http://localhost:8501 in browser
# Navigate through all 5 pages
# Verify data displays correctly
# Try filters, sorting, clicking (no errors in console)
```

**React**:
```bash
cd dashboard
npm start
# Open http://localhost:3000 in browser
# Navigate through all 5 pages
# Check browser DevTools → Console (no errors)
# Check Network tab (API calls successful)
```

### Success Criteria
✅ All 5 pages load without errors  
✅ Data displays in tables and charts  
✅ API calls successful (check Network tab)  
✅ Filters/sorting work (updates data)  
✅ Responsive on desktop (mobile optional for MVP)  
✅ Looks reasonably polished (colors, spacing, fonts)

---

## 🔌 Integration Points (For Reference)

Your two services must work together. Here's how:

```
Teammate B (Frontend)
  └─ Calls API endpoints from Teammate A
     ├─ GET /analytics/model-performance
     ├─ GET /analytics/language-performance
     ├─ GET /analytics/prompt-features
     ├─ GET /analytics/top-prompts
     └─ GET /analytics/model-performance-timeline

Teammate A (API)
  └─ Queries PostgreSQL materialized views
     ├─ mv_model_performance_arena
     ├─ mv_language_performance
     ├─ mv_prompt_feature_impact
     ├─ mv_top_prompt_templates
     └─ mv_daily_model_success

Lead (You) = Plugs Components Together
  └─ Docker Compose orchestrates:
      ├─ PostgreSQL (Phase 1 - ready)
      ├─ FastAPI service (from Teammate A)
      └─ Frontend service (from Teammate B)
```

---

## 📋 Detailed Specifications

### For Teammate A (API Backend)
→ **Read**: `/docs/API_SPECIFICATION.md`
- Full endpoint specs with query parameters
- Request/response examples
- Error codes
- Performance expectations
- Implementation checklist

### For Teammate B (Frontend)
→ **Read**: `/docs/FRONTEND_REQUIREMENTS.md`
- UI/UX requirements for all 5 pages
- Color scheme, typography, spacing
- Chart types and data structures
- State management patterns
- Responsive design specs

### Both Should Reference
→ **Read**: `/docs/DATABASE_SCHEMA_REFERENCE.md`
- What data is available
- Materialized view contents
- Example SQL queries
- Data dictionary

→ **Read**: `/docs/INTEGRATION_GUIDE.md`
- Parallel development workflow
- How we'll integrate your work
- Testing & deployment steps
- Troubleshooting common issues

---

## 🚀 Delivery Process

### Step 1: Build Independently (Parallel Work)
- **Teammate A**: Implement API endpoints following API_SPECIFICATION.md
- **Teammate B**: Build dashboard pages following FRONTEND_REQUIREMENTS.md
- **Both**: Test locally with provided examples

### Step 2: Commit & Deliver
- **Teammate A**: Commit to `/api` folder with working endpoints
- **Teammate B**: Commit to `/dashboard` folder with working pages
- **Both**: Include working Dockerfile and environment template

### Step 3: Lead Integration (Your Lead Does This)
- Pulls both submissions
- Runs Docker Compose to orchestrate services
- Tests end-to-end data flow

### Step 4: Feedback Loop
- Lead may ask for adjustments (response format, etc.)
- Both iterate quickly

---

## ❓ Questions?

### Common Questions

**Q (Teammate A): "How do I connect to PostgreSQL?"**
A: See DATABASE_SCHEMA_REFERENCE.md → Connection Details section. Use psycopg2 or SQLAlchemy.

**Q (Teammate B): "What JSON format does the API return?"**
A: See API_SPECIFICATION.md → Response Format Standards section. Also includes examples.

**Q (Both): "What if the API/database is down when I'm building?"**
A: Use mock data in test files. When the API is ready, swap in real data.

**Q (Both): "Can I use a different tech stack?"**
A: Yes! As long as:
- API returns JSON matching the spec
- Frontend displays the data correctly
- Both Dockerizable

**Q (Both): "What if I get stuck?"**
A: Ask your lead - they're monitoring progress daily.

---

## 📦 Delivery Checklist

### Teammate A (API) - Before Submitting

- [ ] `/api/main.py` has all 5 endpoints working
- [ ] All endpoints tested and return data in <500ms
- [ ] Errors handled gracefully (return proper error JSON)
- [ ] `/api/requirements.txt` lists all dependencies
- [ ] `/api/.env.example` has all required env vars
- [ ] `/api/Dockerfile` builds and runs successfully
- [ ] `/api/README.md` explains setup and running
- [ ] Swagger docs work at `/api/*app*/docs`
- [ ] Code committed to `/api/` folder
- [ ] Tests passing locally

### Teammate B (Frontend) - Before Submitting

- [ ] All 5 pages implemented and load without errors
- [ ] All pages fetch data from API successfully
- [ ] Charts/tables display data correctly
- [ ] Filters, sorting, pagination work end-to-end
- [ ] `/dashboard/requirements.txt` (Streamlit) or `package.json` (React) has all deps
- [ ] `/dashboard/.env.example` has all required env vars
- [ ] `/dashboard/Dockerfile` builds and runs successfully
- [ ] `/dashboard/README.md` explains setup and running
- [ ] Screenshots of all 5 pages included in README
- [ ] No console errors in browser
- [ ] Responsive layout (desktop at minimum)
- [ ] Code committed to `/dashboard/` folder
- [ ] All pages tested locally

---

## 🏁 Success Looks Like

**When Everything Works Together:**

1. You run: `docker-compose up --build`
2. PostgreSQL starts (Phase 1 OLAP layer ready)
3. API starts and connects to PostgreSQL
4. Frontend starts and connects to API
5. You open browser to dashboard
6. You see models ranked by success rate
7. You click a filter → API returns new data → Chart updates
8. All data flows without errors
9. Response times are snappy (<1 second per interaction)
10. You ship it with confidence ✅

---

## Timeline

- **Day 1**: Read specifications, set up project structure
- **Day 2-3**: Build core functionality (Endpoints 1-3 for A, Pages 1-3 for B)
- **Day 3-4**: Build remaining functionality (Endpoints 4-5 for A, Pages 4-5 for B)
- **Day 4**: Test independently, fix bugs
- **Day 5**: Submit to lead for integration

**Total**: ~5 days of parallel work → 1 day integration → Done!

---

## Questions About This Assignment?

→ Ask your lead before starting.  
→ Don't be blocked by missing info - make reasonable assumptions & document them.

**You've got this! 🚀**

