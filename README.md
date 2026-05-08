# PromptLens

**PromptLens** is an end-to-end prompt intelligence mining and analytics engine designed to transform unstructured LLM conversational logs into structured, actionable telemetry. 

By employing robust ETL pipelines, a highly optimized OLAP data warehouse (PostgreSQL), and advanced data mining techniques, PromptLens brings data-driven engineering to prompt development. It allows engineering teams to stop relying on trial-and-error prompt engineering, instead utilizing multidimensional OLAP schemas to expose how constraint density, internal text features, and formatting correlate with prompt execution success across various language models.

---

## 🏗 System Architecture

PromptLens is built as a highly scalable, multi-component data platform separated into distinct layers:

- **ETL & Data Engineering (`/etl`)**: Parses, normalizes, and extracts over 15 feature-engineered attributes from ~4.6M raw execution events. Data is then streamed into a local or remote PostgreSQL instance utilizing a Star Schema layout.
- **Analytics & Machine Learning (`/analytics`)**: Employs R-based and Python-based pipelines to run clustering (K-Means), association rule mining (Apriori), and baseline logistic regression to uncover hidden prompt outcome correlations.
- **Serving Layer (`/api`)**: A robust FastAPI application that interfaces with the data warehouse, enabling real-time queries against OLAP indexes and materialized views.
- **Frontend Dashboard (`/frontend`)**: A Next.js-based web interface designed to visualize prompt engineering telemetry and model performance patterns dynamically.

*For deeper architectural insights, please refer to [ARCHITECTURE.md](ARCHITECTURE.md) and [DATA_PIPELINE.md](DATA_PIPELINE.md).*

---

## ✨ Core Features

* **Large-Scale Prompt Telemetry**: Ingests, normalizes, and processes ~4.6M prompt execution events from diverse real-world AI repositories (e.g., ShareGPT, Chatbot Arena).
* **Star Schema Warehouse Design**: Maps event tracking data into `fact_promptexecution` and dimensional tables, heavily optimized via indices and materialized views.
* **Feature Engineering Engine**: Extracts boolean structure flags (`contains_code`, `contains_constraints`) and quantitative metrics (`complexity_score`, `token_estimate`) programmatically.
* **OLAP Analytics & ML Insights**: Discovers structural patterns that dictate prompt success or failure using Classification, Clustering, and Association Rules.
* **API & Dashboard Interface**: Presents data securely and efficiently to end users via a FastAPI layer integrated with a Next.js front-end.

---

## 🚀 Quick Start

PromptLens is designed for containerized cloud deployment but can be reproduced locally.

### 1. Environment Setup

Copy the example environment file and configure it:
```bash
cp .env.example .env
```

### 2. ETL & Warehouse Ingestion
Ensure PostgreSQL is running and accessible. Run the following to build the schemas and load data:
```bash
python etl/warehouse/load_streaming.py
```

### 3. API Serving
Start the FastAPI backend server:
```bash
cd api
pip install -r ../requirements.txt
uvicorn main:app --reload
```
The API docs are available at `http://localhost:8000/docs`.

### 4. ML / Analytics (Optional)
To run the R-based or Python-based analytical models locally:
```bash
cd analytics/r_scripts
Rscript requirements.R
Rscript 01_data_preparation.R
# Followed by remaining scripts...
```

---

## 📖 Documentation Directory

- **[Architecture & Systems Design](ARCHITECTURE.md)**: Deep dive into the PromptLens component layers.
- **[Data Pipeline & ETL](DATA_PIPELINE.md)**: Details regarding ingestion, transformation logic, and warehouse schema.
- **[API Reference](API_REFERENCE.md)**: Documentation covering the FastAPI layer and endpoints.
- **[Contributing](CONTRIBUTING.md)**: Guidelines for contributing code and expanding PromptLens.
- **[Changelog](CHANGELOG.md)**: History of features, fixes, and performance updates.

---

## 📈 Visual Telemetry

The analytics engine continually updates insights. Key automatically generated telemetry visualizations (accessible via the dashboard or `analytics/results/figures/`):
- Feature Correlation Matrices
- Model Success Density Comparisons
- K-Means Clustering of Semantic Complexity
- Classification Evaluation (ROC/AUC)

---

## 📄 License & Legal
[MIT License](LICENSE) (If applicable). Built as a professional-grade prompt intelligence platform.
