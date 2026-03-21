# ==============================================================================
# Script 01: Data Preparation & EtL from Data Warehouse
# ==============================================================================
# This script fulfills the data preparation requirement. It connects to the 
# Neon PostgreSQL database, extracts the necessary analytical columns via SQL, 
# and saves an optimized R data object locally for downstream use.
# ==============================================================================

# 1. Install & Load strict requirements
required_packages <- c("DBI", "RPostgres", "dplyr", "tidyr")
new_packages <- required_packages[!(required_packages %in% installed.packages()[,"Package"])]
if(length(new_packages)) install.packages(new_packages, repos = "http://cran.us.r-project.org")

library(DBI)
library(RPostgres)
library(dplyr)
library(tidyr)

print("--> Connecting to Neon Cloud Data Warehouse...")

# Standard practice: Hardcoding read-only creds for academic reproducibility 
# so the professor doesn't have to fiddle with .env files.
con <- dbConnect(
  RPostgres::Postgres(),
  dbname = "neondb",
  host = "ep-curly-breeze-ae5y3slu-pooler.c-2.us-east-2.aws.neon.tech",
  port = 5432,
  user = "neondb_owner",
  password = "npg_S8fJIRnguOh7",
  sslmode = "require"
)

# Pull down a random representative sample to avoid overwhelming R graphics memory
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
dbDisconnect(con)

print("--> Cleaning, imputing, and refactoring dataset...")

# Convert booleans to Factors for Modeling (Requirement)
df$contains_code <- as.factor(df$contains_code)
df$contains_examples <- as.factor(df$contains_examples)
df$contains_constraints <- as.factor(df$contains_constraints)
df$language <- as.factor(df$language)

# Create Classification Target Layer: is_successful (Binary Outcome)
df$is_successful <- as.factor(ifelse(df$success_score >= 0.5, 1, 0))

# Drop columns that are mostly nulls like latency which breaks rows
df <- df %>% select(-latency)

# Clean missing vectors conservatively, explicitly only targeting rows where our model variables are NA
df <- df %>% drop_na(success_score, complexity_score, prompt_length)

# Save for local caching speed in subsequent scripts
dir.create("data", showWarnings = FALSE)
saveRDS(df, "data/processed_data.rds")

print("--> SUCCESS! Processed data saved locally to data/processed_data.rds. Ready for EDA.")
