# Frontend Dashboard - Complete Requirements Specification

## Overview
This document specifies the web dashboard UI that visualizes the analytics API endpoints. The frontend consumes REST APIs (Phase 2) and presents insights about model performance, language difficulty, and prompt effectiveness.

**Status**: Ready for implementation  
**Technology Stack**: React + TypeScript (recommended) or Streamlit (simplest)  
**API Server**: FastAPI running on `http://localhost:8000` (or configured URL)  
**Deployment**: Docker, Vercel, or standalone web server

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│           Frontend Dashboard (React/Streamlit)      │
│  (User browsing charts, tables, insights)           │
└────────────────────┬────────────────────────────────┘
                     │ HTTP/REST
                     │ (GET requests with query params)
┌────────────────────▼────────────────────────────────┐
│         FastAPI Service Layer (Phase 2)             │
│  (5 REST endpoints: /analytics/...)                 │
└────────────────────┬────────────────────────────────┘
                     │ Direct query
                     │ (SQL to views)
┌────────────────────▼────────────────────────────────┐
│  PostgreSQL Database (Phase 1 - OLAP Layer)         │
│  (5 Materialized Views + 14 Indexes)                │
└─────────────────────────────────────────────────────┘
```

---

## Dashboard Pages

### Page 1: Model Performance (Home/Landing)

**Route**: `/` or `/dashboard/models`

**Purpose**: Show which models perform best

**UI Components**:

1. **Metric Cards** (Top-level summary)
   - Total Models: 15
   - Highest Success Rate: gpt-4 (75.43%)
   - Most Tested Model: vicuna-13b (5,931 attempts)
   - Overall Dataset Size: 200K+ executions

2. **Leaderboard Table** (Main content)
   - Columns: Rank | Model Name | Success Rate | Median Score | Attempt Count | Trend (7-day)
   - Sort: By success rate (descending), attempts, or median
   - Show: Top 10 (configurable via dropdown)
   - Refresh: Every 60 seconds (auto-refresh toggle)

   | Rank | Model Name        | Success Rate | Median | Attempts | 7-Day Trend |
   |------|-------------------|--------------|--------|----------|-------------|
   | 1    | gpt-4             | 75.43%       | 1.00   | 4,217    | ↑ +2.3%     |
   | 2    | claude-v1         | 67.18%       | 1.00   | 3,927    | ↓ -0.5%     |
   | 3    | claude-instant-v1 | 63.50%       | 1.00   | 2,626    | → +0.1%     |

3. **Time-Series Chart** (Below leaderboard)
   - X-axis: Date (last 30 days)
   - Y-axis: Success Rate (0-1 scale, percentage labels)
   - Lines: One per model (toggle on/off)
   - Interactive: Hover shows exact values, click legend to hide/show
   - Chart Library: Chart.js, Plotly, or Recharts

   **Sample Data**:
   ```
   2024-02-20: gpt-4=0.7654, claude-v1=0.6722, gpt-3.5-turbo=0.6142
   2024-02-21: gpt-4=0.7543, claude-v1=0.6718, gpt-3.5-turbo=0.6138
   ...
   2024-03-20: gpt-4=0.7543, claude-v1=0.6718, gpt-3.5-turbo=0.6138
   ```

4. **Controls**:
   - Filter by Date Range: Date picker (start/end)
   - Filter by Models: Multi-select dropdown
   - Sort By: Dropdown (success_rate, attempts, median_success)
   - Limit: Input (default 10, max 50)
   - Auto-Refresh: Toggle (ON/OFF)
   - Refresh Now: Button

---

### Page 2: Language Difficulty Analysis

**Route**: `/dashboard/languages`

**Purpose**: Show programming language difficulty/success ranking

**UI Components**:

1. **Metric Cards**:
   - Total Languages Tested: 12
   - Easiest Language: (auto-calculate, e.g., SQL @ 82%)
   - Hardest Language: (auto-calculate, e.g., Rust @ 42%)
   - Total Language Prompts: 18K+

2. **Difficulty Table** (Main content)
   - Columns: Rank | Language | Success Rate | Difficulty Level | Sample Count | Median Score
   - Difficulty Color Coding:
     - Green (Easy): >75% success rate
     - Yellow (Medium): 50-75% success rate
     - Red (Hard): <50% success rate
   - Sort: By success rate

   | Rank | Language | Success Rate | Level   | Prompts | Median |
   |------|----------|--------------|---------|---------|--------|
   | 1    | sql      | 82.34%       | Easy    | 2,341   | 1.00   |
   | 2    | python   | 78.12%       | Easy    | 3,421   | 1.00   |
   | 3    | javascript | 64.23%     | Medium  | 1,892   | 0.75   |

3. **Horizontal Bar Chart** (Visual ranking)
   - Bars representing success_rate (0-100%)
   - Color-coded by difficulty level
   - Hover shows exact percentage and sample count
   - Sortable: Click column headers in table

4. **Controls**:
   - Minimum Samples: Slider (1-1000, filters noise)
   - Sort By: Dropdown (success_rate, prompts, median)
   - Limit: Input (default 20)

---

### Page 3: Prompt Feature Impact

**Route**: `/dashboard/features`

**Purpose**: Visualize how prompt features affect success

**UI Components**:

1. **Metric Cards**:
   - Best Combo Success Rate: (auto-calculate, e.g., 91%)
   - Worst Combo Success Rate: (auto-calculate, e.g., 42%)
   - Most Common Combo: (auto-calculate)

2. **Feature Matrix / Heatmap** (Main visualization)
   - 3D representation of feature combinations: examples × code × constraints
   - Cell color = success rate (green=high, red=low)
   - Cell size or label = sample count
   - Hover: Shows exact success rate and sample count

   **Template**:
   ```
   Features:
   ┌─────────────────────────────────────────────────┐
   │ Examples × Code × Constraints                   │
   ├─────────────┬─────────────┬─────────────┬───────┤
   │ E×C×Con     │ E×C×¬Con    │ E×¬C×Con    │ ...   │
   │ avg=0.91    │ avg=0.88    │ avg=0.72    │       │
   │ n=1523      │ n=2104      │ n=892       │       │
   └─────────────┴─────────────┴─────────────┴───────┘
   ```

3. **Feature Impact Table** (Detailed breakdown)
   - Columns: Examples | Code | Constraints | Sample Count | Success Rate | Impact
   - Show all 8 combinations ranked by success rate
   - Color-code rows by impact level

4. **Insights Section** (Auto-generated text)
   - "Best practice: Include examples + code (no constraints) → 91% success"
   - "Avoid: No features (baseline) → 42% success"
   - "Trade-off: Adding constraints decreases success by ~5-10%"

5. **Controls**:
   - Minimum Samples: Slider (filter noise)
   - Sort By: Dropdown (success_rate, count)
   - View Mode: Toggle (heatmap / table / both)

---

### Page 4: Top Prompt Templates

**Route**: `/dashboard/top-prompts`

**Purpose**: Show best-performing prompt templates (for reference/reuse)

**UI Components**:

1. **Metric Cards**:
   - Total Unique Templates: 2,341
   - Top Template Success Rate: 91.23%
   - Most Reused Template: 234 times
   - Average Success Rate: (auto-calculate)

2. **Templates Table** (Main content)
   - Columns: Rank | Template Preview | Success Rate | Uses | Median Score | Actions
   - Preview: First 100 chars of prompt (truncated with "...")
   - Expandable: Click row to see full prompt in modal/drawer
   - CTA: Copy prompt, View full prompt, Use in analysis

   | Rank | Template Preview                    | Success | Uses | Median | Actions  |
   |------|-------------------------------------|---------|------|--------|----------|
   | 1    | "Write a Python function that..."  | 91.23%  | 234  | 1.00   | View/Copy|
   | 2    | "Create a SQL query for..."        | 88.45%  | 187  | 1.00   | View/Copy|

3. **Full Prompt Modal** (Click to expand)
   - Show complete prompt text
   - Display: hash, usage count, success metrics
   - CTA: Copy to clipboard, Close

4. **Controls**:
   - Minimum Uses: Slider (filter one-off prompts)
   - Sort By: Dropdown (success_rate, uses)
   - Search: Text input (searches prompt preview/hash)
   - Limit: Input (default 10)

---

### Page 5: Executive Dashboard (Optional Summary)

**Route**: `/dashboard/summary` or `/`

**Purpose**: Single-page high-level view for executives/stakeholders

**UI Components**:

1. **KPI Cards** (Top row):
   ```
   ┌──────────┬──────────┬──────────┬──────────┐
   │ Models   │ Languages│ Templates│ Success  │
   │ Tested   │ Supported│ Tracked  │ Overall  │
   │ 15       │ 12       │ 2,341    │ 68.5%    │
   └──────────┴──────────┴──────────┴──────────┘
   ```

2. **Winner Metrics**:
   - Top Model: gpt-4 (75.43% success)
   - Top Language: SQL (82.34% success)
   - Top Feature Combo: Examples + Code (91% success)

3. **Mini Charts**:
   - Model Performance (small bar chart, top 5)
   - Language Difficulty (small bar chart, top 5 + bottom 3)
   - Success Rate Trend (small line chart, 30 days)

4. **Quick Links**: Buttons to each detailed page

---

## Data Refresh Strategy

### Auto-Refresh Intervals

| Page | Data | Interval | Reason |
|------|------|----------|--------|
| Models | /analytics/model-performance-timeline | 60 sec | Trends change slowly |
| Languages | /analytics/language-performance | 300 sec | Static unless new data |
| Features | /analytics/prompt-features | 300 sec | Static unless retrained |
| Top Prompts | /analytics/top-prompts | 300 sec | Static unless new prompts |

### Manual Refresh
- Every page has "Refresh Now" button
- Show loading spinner while fetching
- Show last update timestamp below data
- Example: "Last updated: 2024-03-20 10:30:00 UTC"

---

## UI/UX Standards

### Color Scheme

| Element | Color | Usage |
|---------|-------|-------|
| Success/Good | #10b981 (Green) | High success rates, easy languages |
| Warning/Medium | #f59e0b (Amber) | Medium success rates |
| Danger/Hard | #ef4444 (Red) | Low success rates, hard languages |
| Primary | #3b82f6 (Blue) | Buttons, links, primary action |
| Background | #f3f4f6 (Light Gray) | Page background |
| Card | #ffffff (White) | Card backgrounds |
| Text | #374151 (Dark Gray) | Primary text |
| Border | #d1d5db (Medium Gray) | Dividers, borders |

### Typography

- **Page Title**: 32px, bold, dark gray
- **Section Title**: 24px, bold, dark gray
- **Card Title**: 18px, semibold, dark gray
- **Body Text**: 14px, regular, medium gray
- **Label/Caption**: 12px, regular, light gray

### Spacing

- Margin between sections: 24px
- Margin between cards: 16px
- Padding inside cards: 16px
- Gap between elements: 8-12px

### Responsive Design

- Desktop: Full layout (1200px+ width)
- Tablet: Stacked layout (768px+)
- Mobile: Single-column layout (<768px)
- Charts: Responsive sizing (CSS Media Queries)

---

## State Management

### Global State (if using React)

```javascript
// Context or Redux store
{
  api: {
    baseUrl: "http://localhost:8000",
    timeout: 5000
  },
  cache: {
    models: { data: [], timestamp, ttl: 60000 },
    languages: { data: [], timestamp, ttl: 300000 },
    features: { data: [], timestamp, ttl: 300000 }
  },
  ui: {
    loading: false,
    error: null,
    selectedModels: [],
    dateRange: { start: Date, end: Date }
  }
}
```

---

## API Integration Points

### Endpoints Called

| Page | Endpoint | Method | Params | Cache TTL |
|------|----------|--------|--------|-----------|
| Models | GET /analytics/model-performance-timeline | GET | days=30 | 60s |
| Models | GET /analytics/model-performance | GET | limit=10 | 60s |
| Languages | GET /analytics/language-performance | GET | limit=20 | 300s |
| Features | GET /analytics/prompt-features | GET | limit=8 | 300s |
| Top-Prompts | GET /analytics/top-prompts | GET | limit=10, min_uses=5 | 300s |

### Request/Response Handling

```javascript
// Pseudo-code pattern

async function fetchModelPerformance(params) {
  const cacheKey = `models_${JSON.stringify(params)}`;
  
  // Check cache
  const cached = cache.get(cacheKey);
  if (cached && !cached.isExpired) {
    return cached.data;
  }
  
  // Fetch from API
  setLoading(true);
  try {
    const response = await fetch(`${API_URL}/analytics/model-performance`, {
      params
    });
    
    if (!response.ok) {
      throw new Error(response.data.error.message);
    }
    
    const data = response.data;
    cache.set(cacheKey, { data, timestamp: Date.now(), ttl: 60000 });
    return data;
  } catch (error) {
    setError(error.message);
    return null;
  } finally {
    setLoading(false);
  }
}
```

---

## Error Handling

### User-Facing Error Messages

| Error | Message | Action |
|-------|---------|--------|
| Network Error | "Cannot reach API server. Check connection." | Retry button |
| Invalid Data | "API returned invalid data. Try refreshing." | Retry button |
| Server Error | "Database error. Try again in a few moments." | Retry button |
| Timeout | "Request took too long. Try with fewer filters." | Adjust params |

### Logging

- Log all API calls (method, endpoint, params, response time)
- Log all errors (timestamp, error code, message, stack trace)
- Use console or dedicated logging service (e.g., Sentry)

---

## Performance Requirements

### Rendering

- Page load: <2 seconds (with cached data)
- Chart interaction: <100ms (hover, click, sort)
- Sort/filter: <500ms
- Pagination: <200ms

### Network

- API response time: <500ms per endpoint (guaranteed by materialized views)
- Cable/network latency: Assume 100ms average
- Total page load: <2.5 seconds (data + rendering)

---

## Accessibility (A11y)

- Use semantic HTML (`<button>`, `<table>`, `<header>`, etc.)
- Add ARIA labels for interactive elements
- Ensure color contrast ratio ≥ 4.5:1 (WCAG AA)
- Support keyboard navigation (Tab, Enter, Arrow keys)
- Provide alt text for charts/images
- Test with screen readers

---

## Browser Support

- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+
- Mobile browsers: iOS Safari, Chrome Android

---

## Deployment & Hosting

### Options

1. **Docker Container** (Recommended)
   - Dockerfile: Node build stage → serve static files
   - Deployment: Docker Compose with PostgreSQL + FastAPI + Frontend

2. **Standalone Web Server** (Nginx, Apache)
   - Build: `npm run build`
   - Serve: Static files from `dist/` or `build/`
   - Proxy API: Configure reverse proxy to FastAPI server

3. **Cloud Platforms**
   - Vercel (Next.js)
   - Netlify (React SPA)
   - AWS S3 + CloudFront (static hosting)
   - Azure App Service (full-stack hosting)

---

## Implementation Checklist

- [ ] Set up project structure (React/Streamlit/etc.)
- [ ] Create layout components (Header, Sidebar, Footer)
- [ ] Implement Page 1: Model Performance (leaderboard + timeline)
- [ ] Implement Page 2: Language Difficulty (table + bar chart)
- [ ] Implement Page 3: Feature Impact (heatmap + table)
- [ ] Implement Page 4: Top Prompts (table + modal)
- [ ] Implement Page 5: Summary Dashboard (KPI cards + mini charts)
- [ ] Add API integration layer (fetch, caching, error handling)
- [ ] Add state management (Context/Redux)
- [ ] Add responsive design CSS
- [ ] Add error boundaries & error pages
- [ ] Test all endpoints with realistic data
- [ ] Add loading states & spinners
- [ ] Add refresh buttons & timestamps
- [ ] Test on mobile devices
- [ ] Performance testing (Lighthouse)
- [ ] Accessibility testing (axe, WAVE)
- [ ] Deploy and verify end-to-end

---

## Next Steps After Implementation

1. Frontend team completes dashboard implementation
2. User integrates API + Frontend containers
3. Full end-to-end test from PostgreSQL → API → Frontend
4. Deploy to production environment
5. Monitor performance & usability
6. Phase 4: Integrate ML model endpoints

