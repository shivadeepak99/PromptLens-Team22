# Project Title: Prompt Intelligence Mining and Analytics Engine (PromptLens)

## Team Members
BALAGA LOKESH – 2023BCS0141  
BARUKULA BRIJESH BENAAYAAH – 2022BCS0153  
SHANIGARAM SHIVA DEEPAK – 2023BCD0048  
BHUPALAM YASWANTH SAI – 2023BCD0057  

## Problem Statement
The effectiveness of Large Language Models (LLMs) heavily relies on the structure, constraints, and vocabulary used in input prompts. Currently, developers lack data-driven methods to understand why certain prompts fail while others succeed. Without structured analysis, prompt engineering remains largely trial-and-error, leading to inefficient development cycles and wasted computational resources. 

## Objectives
* Collect real prompt execution logs from multiple real-world sources and community repositories.
* Transform raw prompt logs into a highly structured data warehouse using a custom ETL pipeline mapping to a star schema.
* Apply Data Mining techniques (Classification, Clustering, Association Rules) and OLAP operations to discover actionable patterns in prompt engineering.
* Identify which AI models perform better and how specific internal text features (code inclusion, constraint counts) influence positive outcomes.
* Build an analytics engine that exposes these insights effectively through a dedicated API and Dashboard.

## Dataset
* **Source of the dataset:** Open-source AI prompt repositories (`chatbot_arena`, `prompt_library`, `sharegpt_code_interpreter`, `sharegpt_conversation_chronicles`).
* **Number of observations:** $\approx$ 4.6 million execution events mapped into `fact_promptexecution`.
* **Number of variables:** Over 15 feature-engineered attributes generated per prompt event, linked via dimension schema.
* **Brief description of important attributes:** 
  * `success_score`: Target metric indicating if the prompt generation was successful.
  * `complexity_score`: Calculated density/complexity of the prompt instructions.
  * `contains_code`, `contains_examples`, `contains_constraints`: Boolean structure flags.
  * `prompt_length`, `token_estimate`: Quantitative measures of the textual volume.
  * `language`, `model_name`: Categorical dimensions tracking tools and environment constraints. 

## Methodology
- **Data preprocessing:** Raw dataset logic is parsed utilizing specialized dataset adapters to normalize overlapping formats. Features representing structure, tokens, and densities are programmatically extracted into standard `prompt_events.jsonl` formats. This parsed data is then bulk upserted into a robust PostgreSQL Data Warehouse optimized by Star Schema layouts (`fact_promptexecution`, `dim_prompt`, etc.). Clean vectors without high-null rates are queried back out into an RDS object using R.
- **Exploratory analysis:** Executed utilizing R (`ggplot2`, `corrplot`, `dplyr`) to map feature covariance, analyze variance in success rates by targeted programming language constraints, and determine density comparisons against code feature flags.
- **Models used:**
  - *K-Means Clustering:* Applied upon continuous numeric constraints (complexity, length, estimated tokens) extracting distinct user behavior groupings defined around semantic complexity.
  - *Association Rule Mining (Apriori):* Applied to textual categorical features discovering implicit linkages bridging complex features to success mapping. 
  - *Logistic Regression:* Implemented acting as our baseline binomial classification mechanism projecting success probability via trained feature weights.
- **Evaluation methods:** Validated through continuous predictions utilizing ROC/AUC curves and discrete cross-tabulated Confusion Matrices evaluating Accuracy, Precision, and Baseline statistical alignment.

## Results
A complete data warehouse structure of 4.6 million event rows directly facilitates highly performant multidimensional OLAP analytic matrices. Exploring prompt dimensionality revealed explicit links dictating the predictability of failure rates across differing programmatic targets, while Apriori networks verified structured constraints universally amplify outcome predictability. The benchmark models demonstrated that explicit components mapped against model variants form heavily structured, non-random clustering distributions.

## Key Visualizations
*(Generated automatically by R scripts inside `results/figures/`)*

### Feature Correlation Matrix
![Correlation Matrix](results/figures/correlation_matrix.png)

### Model Success Density
![Success Density](results/figures/success_density.png)

### Average Success Rate by Coding Language
![Language Difficulty](results/figures/language_difficulty.png)

### K-Means Clustering Space
![Cluster Plot](results/figures/cluster_plot.png)

### Association Rules Representation
![Association Rules](results/figures/association_rules.png)

### Classification Evaluation
![ROC Curve](results/figures/roc_curve.png)

## How to Run the Project
This project is already fully deployed (PostgreSQL warehouse on Neon.tech and FastAPI backend running in a Docker container on a cloud host), so running it locally is **optional**. 

If you want to reproduce the full pipeline locally, follow the service-by-service steps below.

### 1. ETL / Data Warehouse Service
1. Ensure you have PostgreSQL available (or configure access to the Neon instance).
2. Create the `promptlens` database using the SQL schema files in `warehouse/`.
3. Run the Python loader to stream JSONL into the warehouse:
  * `python warehouse/load_streaming.py`
4. (Optional) Re-run the R data extraction to confirm analytical views:
  * `Rscript scripts/01_data_preparation.R`

### 2. R Analytics Service
1. Install necessary R packages via the provided script:
  * `Rscript scripts/requirements.R`
2. Execute the analytical pipeline sequentially to generate figures and evaluation tables:
  * `Rscript scripts/01_data_preparation.R`
  * `Rscript scripts/02_exploratory_analysis.R`
  * `Rscript scripts/03_modeling.R`
  * `Rscript scripts/04_evaluation.R`

### 3. Backend API Service (FastAPI)
1. Install necessary Python backend dependencies:
  * `pip install -r requirements.txt`
2. Configure the `DATABASE_URL` environment variable to point to your warehouse (local PostgreSQL or Neon).
3. Start the API locally:
  * `uvicorn app.main:app --reload`
4. The interactive API docs will be available at `http://localhost:8000/docs`.

### 4. Frontend Dashboard (Planned)
The dashboard/frontend layer will connect to the FastAPI analytics endpoints to visualize OLAP and model insights. Frontend start-up instructions will be added once the UI is finalized.

**Folder organization (summary):**
* `scripts/`: Central R logic scripts sequentially numbering data preparation -> modeling -> evaluation loops. Also includes package requirement lists.
* `results/figures/`: Repository holding graphical PNG visualizations automatically constructed via R.
* `results/tables/`: Serialized mathematical metrics capturing cross-validation scores.
* `app/` & `ml_service/`: Python ML pipeline inferences and web API framework endpoints.
* `warehouse/`: Physical load and setup schemas targeting local/remote PostgreSQL data warehousing components.

## R Libraries Used
The following R libraries are used throughout the analysis pipeline (installed via `scripts/requirements.R`):

* `DBI`, `RPostgres` – Database connectivity to the Neon/PostgreSQL warehouse.
* `dplyr`, `tidyr` – Data manipulation, filtering, and reshaping.
* `ggplot2`, `corrplot` – Exploratory data analysis and plotting.
* `arules`, `arulesViz` – Association rule mining and rule visualization.
* `cluster`, `factoextra` – K-Means clustering and cluster visualization.
* `caret` – Train/test splitting and classification utilities.
* `pROC` – ROC curve and AUC computation for model evaluation.

## Conclusion
The project has successfully bridged the gap isolating massive unstructured dialogue datasets into highly disciplined OLAP architectures. Empowered by Exploratory Analysis and Data Mining schemas (K-Means, Apriori, Modeling matrices), PromptLens quantitatively proves that conversational AI failures are heavily structured phenomena dependent entirely upon instruction density, structural composition, and dataset environment dimensionality.

## Contribution
* **BALAGA LOKESH (2023BCS0141) |** Data Mining / ML Engineer: Classification model, clustering analysis, association rule mining, exporting model results.
* **BARUKULA BRIJESH BENAAYAAH (2022BCS0153) |** Documentation & Dashboard Developer: Analytical SQL queries, materialized views, dashboard visualizations, frontend integration.
* **SHANIGARAM SHIVA DEEPAK (2023BCD0048) |** ETL Pipeline Engineer, Database Designer & AI Agent Developer: Dataset ingestion, transformation pipeline, feature extraction, star schema design, PostgreSQL database setup, loader implementation, warehouse validation.
* **BHUPALAM YASWANTH SAI (2023BCD0057) |** FastAPI Backend Architect: API development, analytics endpoints, integration with database, API security and validation.

## References
1. Zheng, L. et al. (2023). "Judging LLM-as-a-Judge with Chatbot Arena". HuggingFace Open Repositories. ShareGPT Code Frameworks. 
2. Comprehensive R-Project analytical systems (`ggplot2` Wickham, H., `arules` Hahsler, M., `caret` Kuhn, M.).
3. PostgreSQL Data Warehouse OLAP Architectural Documentations.
