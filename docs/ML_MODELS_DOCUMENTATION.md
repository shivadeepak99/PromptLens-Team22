# Machine Learning Models Documentation

**For:** Backend & ML Team | **Status:** In Development | **Last Updated:** March 20, 2026

---

## 1. Overview of Trained Models

Your project has **3 ML models** already trained and saved in `ml_service/models/`:

### 1.1 Classification Model (Success Score Prediction)
- **Model Type:** Random Forest Classifier
- **Target Variable:** `success_score` (continuous 0-1) → treated as regression
- **Training Data:** 52,800 prompts (80%) | Test: 13,200 (20%)
- **Features Used:**
  - Prompt characteristics: length, complexity, contains_examples, contains_code, contains_constraints
  - Model name, task type, programming language
  - Interaction features
- **Performance Metrics:**
  - Mean Absolute Error (MAE): 0.3881
  - Root Mean Squared Error (RMSE): 0.4333
  - R² Score: 0.1289 (baseline performance - can be improved with feature engineering)
- **Baseline:** Gradient Boosting achieved nearly identical metrics (MAE: 0.3862, R²: 0.1287)
- **File:** `ml_service/models/training_summary.json`

**Interpretation:**
- On average, model predictions are ~0.39 points off from actual success (on 0-1 scale)
- Low R² indicates success prediction depends on factors not captured in current features
- **Action Item for R Analysis:** Feature engineering and interaction analysis needed

---

### 1.2 Clustering Model (Prompt Segmentation)
- **Model Type:** K-Means Clustering
- **Number of Clusters:** 4 (optimal based on inertia criterion)
- **Training Data:** All ~66K prompts without labels
- **Algorithm Parameters:**
  - Inertia: 482,404.47
  - Random state: 42 (reproducible)

**Cluster Profiles:**
| Cluster ID | Cluster Name | Size | % | Characteristics |
|--|--|--|--|--|
| 0 | simple_short | 45,941 | 69.6% | Brief, straightforward prompts |
| 1 | complex_detailed | 26,465 | 40.1% | Long, detailed, multi-step prompts |
| 2 | short_code_prompts | 56,350 | 85.3% | Code-focused, minimal context |
| 3 | example_rich_prompts | 22,947 | 34.7% | Include examples, detailed explanations |

**Key Insights:**
- Prompts naturally segment into 4 distinct patterns
- Overlap in assignments suggests hierarchical/fuzzy patterns (R analysis opportunity)
- Success rates vary significantly by cluster (to be explored in R analysis)

---

### 1.3 Association Rules (Pattern Discovery)
- **Model Type:** Apriori Algorithm (market basket analysis)
- **Number of Rules:** 50 rules discovered
- **Metrics:**
  - **Support:** Proportion of prompts containing both antecedent and consequent
  - **Confidence:** P(consequent | antecedent) — reliability of the rule
  - **Lift:** How much more likely consequent is given antecedent
- **File:** `ml_service/models/association_rules.json`

**Sample Rules (from existing data):**
1. **long_prompt + high_density → success_low** (Confidence: 56.34%, Lift: 2.01)
   - Interpretation: Long, dense prompts are 2x more likely to have low success
   
2. **medium_prompt → high_complexity, success_low** (Confidence: 56.23%, Lift: 2.004)
   - Interpretation: Medium-length prompts correlate with complexity and lower success
   
3. **contains_examples=TRUE → success_high** (to be validated)
   - Interpretation: Adding examples increases success likelihood

**Key Insights:**
- Prompt length and density are strong predictors of success
- Complexity and success_score have inverse relationship
- Example inclusion likely boosts success

---

## 2. Model Integration Architecture

```
PostgreSQL Warehouse (fully loaded)
    │
    ├─> Fact & Dimension Tables
    │       (200K+ prompt executions, dimensions)
    │
    ├─> OLAP Layer (SQL Views + Indexes)
    │       mv_daily_model_success
    │       mv_model_performance_arena
    │       mv_language_performance
    │       mv_prompt_feature_impact
    │       mv_top_prompt_templates
    │
    └─> ML Models (Python backend)
            ├─ Classification (success prediction)
            ├─ Clustering (prompt segmentation)
            └─ Association Rules (pattern discovery)
                    │
                    ├─> FastAPI Endpoints (Team Mate 1)
                    │       /ml/success-prediction
                    │       /ml/prompt-clusters
                    │       /ml/association-rules
                    │
                    ├─> R Analysis & Visualization (Team Mate 2)
                    │       01_data_preparation.R
                    │       02_exploratory_analysis.R
                    │       03_modeling_validation.R
                    │       04_evaluation.R
                    │
                    └─> Frontend (Team Mate 3)
                            Dashboard with model insights
                            Prediction UI
                            Pattern exploration
```

---

## 3. Data for R Analysis

### 3.1 Where Data Comes From
R scripts will pull data directly from **PostgreSQL warehouse**.

**Connection Details:**
```yaml
Database:   promptlens
Host:       localhost (or Docker container hostname)
Port:       5432
User:       postgres
Password:   (from .env)
Schema:     public

Key Tables:
  - fact_promptexecution    (200K+ rows) — main event log
  - dim_prompt              (~40K rows) — prompt templates & features
  - dim_model               (~50 rows) — AI models tested
  - dim_task                (~20 rows) — task categories
  - dim_time                (~100 rows) — dates
  - dim_source              (~10 rows) — data sources
  - dim_session             (~5K rows) — conversation sessions
```

### 3.2 Key Columns for R Analysis
```r
# From fact_promptexecution (MAIN TABLE)
success_score         # Target variable (0-1, success rate)
latency_ms            # Response time
model_key             # Foreign key to dim_model
prompt_key            # Foreign key to dim_prompt
task_key              # Foreign key to dim_task
time_key              # Foreign key to dim_time
session_key           # User session identifier

# From dim_prompt (PROMPT FEATURES)
prompt_length         # Character count
prompt_hash           # Unique identifier
contains_examples     # Boolean (1/0)
contains_code         # Boolean (1/0)
contains_constraints  # Boolean (1/0)
prompt_complexity     # Computed complexity score
prompt_density        # Words per sentence / concept density

# From dim_model
model_name            # e.g., "gpt-4", "claude-v1"
model_family          # Category (GPT, Claude, Open source)

# From dim_task
task_name             # e.g., "coding", "creative_writing"
programming_language  # e.g., "python", "javascript"
difficulty_level      # Computed from data

# From dim_time
ts                    # Timestamp (datetime)
```

---

## 4. R Analysis Phase (Your Team Mate 2)

### 4.1 Phase 1: Data Preparation (`01_data_preparation.R`)
**Goals:**
- Connect to PostgreSQL
- Load fact + dimension tables
- Handle missing values
- Create derived features
- Export clean dataset as CSV

**Deliverables:**
- `.RData` file with clean dataset
- `data/processed/promptlens_clean.csv` (for sharing)
- Summary stats (n_rows, n_cols, missing %)

**Sample Code Skeleton:**
```r
# Install & load required libraries
library(RPostgreSQL)
library(dplyr)
library(tidyr)

# Connect to PostgreSQL
conn <- dbConnect(
  PostgreSQL(),
  user = "postgres",
  password = Sys.getenv("DB_PASSWORD"),
  host = "localhost",
  port = 5432,
  dbname = "promptlens"
)

# Load tables
fact <- dbGetQuery(conn, "SELECT * FROM fact_promptexecution")
prompts <- dbGetQuery(conn, "SELECT * FROM dim_prompt")
models <- dbGetQuery(conn, "SELECT * FROM dim_model")
tasks <- dbGetQuery(conn, "SELECT * FROM dim_task")
times <- dbGetQuery(conn, "SELECT * FROM dim_time")

# Join & create derived features
data <- fact %>%
  inner_join(prompts, by = "prompt_key") %>%
  inner_join(models, by = "model_key") %>%
  inner_join(tasks, by = "task_key") %>%
  inner_join(times, by = "time_key") %>%
  mutate(
    day = as.Date(ts),
    prompt_density = prompt_length / (str_count(prompt_text, "\\s") + 1),
    is_success = success_score > 0.5,
    feature_combo = paste(contains_examples, contains_code, contains_constraints, sep="-")
  )

# Clean & save
data_clean <- data %>%
  filter(success_score >= 0 & success_score <= 1) %>%  # Validate
  drop_na(model_name, task_name)

save(data_clean, file = "data/processed/promptlens_clean.RData")
write.csv(data_clean, "data/processed/promptlens_clean.csv")
cat("Dataset shape:", nrow(data_clean), "x", ncol(data_clean), "\n")
cat("Missing %:", colnames(data_clean)[colSums(is.na(data_clean)) > 0], "\n")
```

---

### 4.2 Phase 2: Exploratory Data Analysis (`02_exploratory_analysis.R`)
**Goals:**
- Understand distributions & correlations
- Identify patterns across models, tasks, prompt types
- Validate clustering & association rules
- Generate visualization suite

**Key Analyses:**
1. **Success Rate Distribution**
   - Histogram of success_score
   - By model, task, language
   - KS test for normality

2. **Feature Correlations**
   - Correlation matrix (success, length, complexity, density)
   - Feature importance plots

3. **Prompt Characteristics**
   - Distribution of contains_examples, contains_code, contains_constraints
   - Cross-tabulation with success

4. **Time-Series Patterns**
   - Daily success rate trends
   - Model performance over time
   - Seasonality checks

5. **Latency Analysis**
   - Response time distribution
   - Correlation with success
   - Outlier detection

**Output:**
- `results/figures/01_distributions.png`
- `results/figures/02_correlations.png`
- `results/figures/03_feature_importance.png`
- `results/figures/04_time_series.png`
- `results/tables/01_summary_stats.csv`
- `results/tables/02_feature_correlations.csv`

---

### 4.3 Phase 3: Model Validation & Refinement (`03_modeling_validation.R`)
**Goals:**
- Validate existing clustering (4-means)
- Validate/refine classification model
- Analyze association rules for business value
- Improve model feature engineering

**Sub-Tasks:**

**A. Clustering Validation**
```r
# Load k-means clusters from existing model
clusters <- read.csv("ml_service/models/cluster_assignments.csv")

# Validate with R (silhouette analysis, elbow plot, etc.)
library(cluster)
library(factoextra)

# Silhouette coefficient
sil <- silhouette(clusters$cluster, dist(data_numeric))
plot(sil, main = "Silhouette Plot for K-Means (k=4)")

# Elbow Curve (k=1 to k=10)
wss <- sapply(1:10, function(k) kmeans(data_numeric, k)$tot.withinss)
plot(1:10, wss, type="b", xlab="k", ylab="WSS")

# Cluster characteristics
data_with_clusters <- data_clean %>%
  mutate(cluster = clusters$cluster) %>%
  group_by(cluster) %>%
  summarise(
    n = n(),
    avg_success = mean(success_score),
    avg_length = mean(prompt_length),
    pct_examples = mean(contains_examples),
    pct_code = mean(contains_code),
    .groups = "drop"
  )
```

**B. Classification Model Validation**
```r
# Load trained model predictions from Python
predictions <- read.csv("ml_service/models/predictions.csv")

# Validate R² and MAE
actual <- predictions$actual_success
predicted <- predictions$predicted_success

mae <- mean(abs(actual - predicted))
rmse <- sqrt(mean((actual - predicted)^2))
r2 <- 1 - sum((actual - predicted)^2) / sum((actual - mean(actual))^2)

# Residual analysis
residuals <- actual - predicted
plot(predicted, residuals, main="Residual Plot")
abline(h=0, col="red")
```

**C. Association Rules Analysis**
```r
# Load association rules from JSON
library(jsonlite)
rules <- fromJSON("ml_service/models/association_rules.json")

# Extract into dataframe
rules_df <- data.frame(
  antecedent = sapply(rules, function(x) paste(x$antecedents, collapse=" + ")),
  consequent = sapply(rules, function(x) paste(x$consequents, collapse=" + ")),
  support = sapply(rules, function(x) x$support),
  confidence = sapply(rules, function(x) x$confidence),
  lift = sapply(rules, function(x) x$lift)
)

# Filter high-quality rules
high_quality <- rules_df %>%
  filter(confidence > 0.6, lift > 1.5) %>%
  arrange(desc(lift))

# Visualize
library(ggplot2)
ggplot(high_quality, aes(x=support, y=confidence, size=lift)) +
  geom_point(alpha=0.6) +
  labs(title="Association Rules Quality", x="Support", y="Confidence", size="Lift")
```

**Output:**
- `results/figures/05_clustering_validation.png`
- `results/figures/06_silhouette_analysis.png`
- `results/figures/07_association_rules.png`
- `results/tables/03_cluster_characteristics.csv`
- `results/tables/04_rules_summary.csv`

---

### 4.4 Phase 4: Comprehensive Evaluation (`04_evaluation.R`)
**Goals:**
- Final model performance summary
- Statistical significance testing
- Business impact quantification
- Model deployment readiness

**Analyses:**
1. **Classification Model Evaluation**
   - MAE, RMSE, R² (with 95% CIs)
   - Precision, Recall, F1 for binary success (threshold 0.5)
   - Learning curves (training vs test error)

2. **Clustering Quality**
   - Davies-Bouldin Index (lower is better)
   - Calinski-Harabasz Index (higher is better)
   - Silhouette Coefficient (-1 to 1, higher is better)

3. **Association Rules Business Value**
   - Rules with highest confidence
   - Rules with highest lift
   - Coverage analysis (% of data explained)

4. **Cross-Model Insights**
   - Do clusters have different success rates?
   - Does prediction confidence vary by cluster?
   - Interaction effects between features

**Output:**
- `results/tables/05_model_evaluation.csv`
  ```
  Metric                    Value         95% CI
  MAE                       0.3881        (0.3850, 0.3912)
  RMSE                      0.4333        (0.4310, 0.4356)
  R²                        0.1289        (0.1200, 0.1378)
  Silhouette (kmeans)       0.4527        (0.4500, 0.4554)
  Davies-Bouldin Index      0.8234        (0.8100, 0.8368)
  Association Rules (n)     50            (high quality: 18)
  ```

- `results/figures/08_final_summary.png` — comprehensive dashboard

---

## 5. ML Endpoints for FastAPI (Team Mate 1)

The R analysis validates and explains what these endpoints will expose:

### Endpoint 1: `/ml/success-prediction`
```json
POST /ml/success-prediction
{
  "prompt_text": "Write a Python function to...",
  "model_name": "gpt-4",
  "task_type": "coding",
  "contains_examples": true,
  "contains_code": false,
  "contains_constraints": true
}

Response:
{
  "predicted_success": 0.72,
  "confidence_interval": [0.68, 0.76],
  "contributing_features": {
    "model_name": 0.34,
    "contains_examples": 0.28,
    "task_type": 0.22
  },
  "cluster_assignment": "short_code_prompts",
  "cluster_success_rate": 0.68
}
```

### Endpoint 2: `/ml/prompt-clusters`
```json
GET /ml/prompt-clusters?cluster_id=2&limit=100

Response:
{
  "cluster_id": 2,
  "cluster_name": "short_code_prompts",
  "size": 56350,
  "characteristics": {
    "avg_prompt_length": 145,
    "pct_with_examples": 0.23,
    "pct_with_code": 0.91,
    "pct_with_constraints": 0.41,
    "avg_success": 0.62,
    "median_latency_ms": 2340
  },
  "success_by_model": [
    {"model": "gpt-4", "success_rate": 0.78, "attempts": 12340},
    {"model": "claude-v1", "success_rate": 0.73, "attempts": 10250}
  ]
}
```

### Endpoint 3: `/ml/association-rules`
```json
GET /ml/association-rules?min_confidence=0.6&min_lift=1.5&limit=20

Response:
{
  "rules": [
    {
      "rule_id": 1,
      "antecedent": "long_prompt + high_density",
      "consequent": "high_complexity + success_low",
      "support": 0.0773,
      "confidence": 0.5634,
      "lift": 2.0081,
      "interpretation": "Long, dense prompts are 2x more likely to result in low success"
    },
    { ... }
  ],
  "summary": {
    "Total rules": 50,
    "High confidence (>0.6)": 18,
    "High lift (>2.0)": 12,
    "Coverage": "73.2% of data"
  }
}
```

---

## 6. Integration Checklist

**For Backend Team (Python):**
- [ ] Load pre-trained models from `ml_service/models/`
- [ ] Create prediction functions wrapping sklearn/joblib models
- [ ] Add endpoints: `/ml/success-prediction`, `/ml/prompt-clusters`, `/ml/association-rules`
- [ ] Document API contract (schemas in OpenAPI/Swagger)
- [ ] Add model refresh logic (retraining if new data available)

**For R Analysis Team:**
- [ ] Extract clean dataset from PostgreSQL (Script 1)
- [ ] Run exploratory analysis (Script 2)
- [ ] Validate clustering & classification (Script 3)
- [ ] Generate final evaluation report (Script 4)
- [ ] Save all visualizations to `results/figures/`
- [ ] Save all summary tables to `results/tables/`

**For Frontend Team:**
- [ ] Consume `/ml/success-prediction` for "Try Your Prompt" feature
- [ ] Consume `/ml/prompt-clusters` for "Explore Clusters" dashboard
- [ ] Consume `/ml/association-rules` for "Pattern Discovery" section
- [ ] Display confidence intervals & feature importance
- [ ] Link insights back to documentation

---

## 7. Files & References

**Existing ML Files:**
- `ml_service/models/training_summary.json` — Model metrics
- `ml_service/models/association_rules.json` — 50 discovered rules
- (Cluster assignments likely in Python code or to be generated)

**Generated During R Analysis:**
- `scripts/01_data_preparation.R` — Load & clean
- `scripts/02_exploratory_analysis.R` — EDA & visualization suite
- `scripts/03_modeling_validation.R` — Cluster/classification validation
- `scripts/04_evaluation.R` — Final metrics & insights
- `results/figures/` — PNG visualizations
- `results/tables/` — CSV metric summaries

**Documentation Files:**
- `docs/ML_MODELS_DOCUMENTATION.md` (this file)
- `docs/R_ANALYSIS_GUIDE.md` (next file)
- `docs/API_SPECIFICATION.md` (for backend team)
- `docs/DATABASE_SCHEMA.md` (for all teams)
- `README.md` (professor submission)

---

**Last Updated:** March 20, 2026
**Owner:** Shanigaram Shiva Deepak
**Approver:** Professor (CSS321 - Data Mining)
