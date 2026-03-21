# ==============================================================================
# Script 01: Data Preparation & ETL from Data Warehouse
# ==============================================================================
# Student: Shanigaram Shiva Deepak (2023BCD0048) / Team PromptLens
# Description: Connects to the Neon PostgreSQL database, extracts the 
# necessary analytical columns via SQL, performs data cleaning, and 
# saves an optimized R data object locally for downstream use.
# ==============================================================================

# --- SECTION 1: Setup and Package Installation ---
# Ensure all required packages are installed and loaded
required_packages <- c("DBI", "RPostgres", "dplyr", "tidyr")
new_packages <- required_packages[!(required_packages %in% installed.packages()[,"Package"])]
if (length(new_packages)) {
  install.packages(new_packages, repos = "http://cran.us.r-project.org")
}

library(DBI)
library(RPostgres)
library(dplyr)
library(tidyr)

# --- SECTION 2: Database Connection ---
print("--> Connecting to Neon Cloud Data Warehouse...")

# Hardcoding read-only credentials for academic reproducibility
con <- dbConnect(
  RPostgres::Postgres(),
  dbname = "neondb",
  host = "ep-curly-breeze-ae5y3slu-pooler.c-2.us-east-2.aws.neon.tech",
  port = 5432,
  user = "neondb_owner",
  password = "npg_S8fJIRnguOh7"
)

# --- SECTION 3: Data Extraction ---
# Extracting a representative sample to optimize memory during modeling
print("--> Fetching Star Schema Fact & Dimension Tables (LIMIT 25,000)...")
query <- "
  SELECT 
    p.prompt_length, p.token_estimate, p.contains_code, p.contains_examples, 
    p.contains_constraints, p.language, p.complexity_score, p.instruction_density, 
    f.success_score, f.latency, f.tokens, f.response_tokens
  FROM fact_promptexecution f
  JOIN dim_prompt p ON f.prompt_key = p.prompt_key
  WHERE f.success_score IS NOT NULL
  ORDER BY RANDOM()
  LIMIT 25000;
"
df <- dbGetQuery(con, query)

# Close the database connection to free up resources
dbDisconnect(con)

# --- SECTION 4: Data Cleaning and Transformation ---
print("--> Cleaning, imputing, and refactoring dataset...")

# 4.1. Convert boolean and categorical features to Factors for modeling
df$contains_code <- as.factor(df$contains_code)
df$contains_examples <- as.factor(df$contains_examples)
df$contains_constraints <- as.factor(df$contains_constraints)
df$language <- as.factor(df$language)

# 4.2. Create Classification Target Layer: is_successful (Binary Outcome)
# Threshold set at 0.5 success_score
df$is_successful <- as.factor(ifelse(df$success_score >= 0.5, 1, 0))

# 4.3. Handle Missing Values
# Drop columns that are mostly nulls (e.g., latency)
df <- df %>% select(-latency)
# Explicitly remove rows where our critical model variables are NA
df <- df %>% drop_na(success_score, complexity_score, prompt_length)

# --- SECTION 5: Save Processed Data ---
# Save the cleaned dataset for local caching in subsequent scripts
dir.create("data", showWarnings = FALSE)
saveRDS(df, "data/processed_data.rds")

print("--> SUCCESS! Processed data saved locally to data/processed_data.rds. Ready for EDA.")

