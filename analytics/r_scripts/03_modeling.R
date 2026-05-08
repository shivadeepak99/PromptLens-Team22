# ==============================================================================
# Script 03: Machine Learning & Modeling
# ==============================================================================
# Project: PromptLens
# Description: Implements Association Rule Mining (Apriori), K-Means Clustering, 
# and a Logistic Regression Model (Baseline).
# ==============================================================================

# --- SECTION 1: Setup and Data Loading ---
# Auto-install necessary mathematical modeling libraries
required_packages <- c("arules", "arulesViz", "cluster", "factoextra", "caret")
new_packages <- required_packages[!(required_packages %in% installed.packages()[,"Package"])]
if(length(new_packages)) {
  install.packages(new_packages, repos = "http://cran.us.r-project.org")
}

library(arules)
library(arulesViz)
library(cluster)
library(factoextra)
library(caret)

print("--> Loading Prepared Data for Modeling...")
df <- readRDS("data/processed_data.rds")
# Generate necessary structural directories for caching model artifacts and plots
dir.create("results/figures", recursive = TRUE, showWarnings = FALSE)
dir.create("app/models", recursive = TRUE, showWarnings = FALSE)

# Set global random seed across file execution for reproducibility
set.seed(42)

# --- SECTION 2: K-Means Clustering ---
print("--> Modeling Phase 1: K-Means Complexity Clustering")

# Extract only continuous numeric covariates for accurate distance-based clustering
cluster_data <- df[, c("complexity_score", "prompt_length", "token_estimate")]
# Standardize scaling so large variables (prompt_length) don't dominate small ones (complexity_score)
cluster_data <- scale(cluster_data) 

# Execute KMeans seeking 3 overarching prompt complexity groups
km.res <- kmeans(cluster_data, centers = 3, nstart = 25)

# Render clustering results in a 2D PCA reduced plane
png("results/figures/cluster_plot.png", width = 800, height = 600, res=100)
fviz_cluster(km.res, data = cluster_data,
             geom = "point", axes = c(1, 2),
             ellipse.type = "convex", 
             ggtheme = theme_bw(),
             main = "K-Means Space (Complexity vs Tokens)")
invisible(dev.off())

# --- SECTION 3: Association Rules (Apriori) Mining ---
print("--> Modeling Phase 2: Apriori Association Rules Mining")

# Filter DataFrame to solely Categorical/Boolean structures for pattern mining
rules_df <- df[, c("contains_code", "contains_examples", "contains_constraints", "is_successful")]

# Re-factor binary outcomes to natural text mapping for clearer rule interpretation
levels(rules_df$is_successful) <- c("Failure", "Success")

# Generate Rules based on moderate support and high confidence thresholds
rules <- apriori(rules_df, parameter = list(supp = 0.05, conf = 0.6, maxlen = 4), 
                 control = list(verbose = FALSE))

# Visualize relationships between categorical attributes determining success/failure
png("results/figures/association_rules.png", width = 1000, height = 800, res=100)
plot(rules, method="graph")
invisible(dev.off())

# --- SECTION 4: Logistic Regression Binary Classification ---
print("--> Modeling Phase 3: Binary Logistic Classification Model")

# Calculate stratified 80/20 train/test split utilizing the caret library
sample_index <- createDataPartition(df$is_successful, p = 0.8, list = FALSE)
train_data <- df[sample_index, ]
test_data <- df[-sample_index, ]

# Fit the Generalized Linear Model applying the binomial family suitable for Sigmoid functions
model_glm <- glm(is_successful ~ prompt_length + complexity_score + instruction_density + 
                 contains_code + contains_examples + contains_constraints, 
                 data = train_data, family = "binomial")

# --- SECTION 5: Cache Artifacts for Evaluation ---
# Store the GLM object and withheld test matrix for 04_evaluation.R
saveRDS(model_glm, "app/models/baseline_glm.rds")
saveRDS(test_data, "data/test_data.rds")

print("--> Modeling Complete! Models cached in app/models.")
