# ==============================================================================
# Script 03: Machine Learning & Modeling
# ==============================================================================
# Implements Association Rule Mining (Apriori), K-Means Clustering, and a 
# Logistic Regression Baseline to satisfy the required modeling tier.
# ==============================================================================

# Install requirements automatically
required_packages <- c("arules", "arulesViz", "cluster", "factoextra", "caret")
new_packages <- required_packages[!(required_packages %in% installed.packages()[,"Package"])]
if(length(new_packages)) install.packages(new_packages, repos = "http://cran.us.r-project.org")

library(arules)
library(arulesViz)
library(cluster)
library(factoextra)
library(caret)

df <- readRDS("data/processed_data.rds")
dir.create("results/figures", recursive = TRUE, showWarnings = FALSE)
dir.create("app/models", recursive = TRUE, showWarnings = FALSE)
set.seed(42)

# ------------------------------------------------------------------------------
# 1. K-Means Clustering
# ------------------------------------------------------------------------------
print("--> Modeling Phase 1: K-Means Complexity Clustering")
cluster_data <- df[, c("complexity_score", "prompt_length", "token_estimate")]
cluster_data <- scale(cluster_data) # Standardize bounds

# K=3 clusters based on prompt behavior
km.res <- kmeans(cluster_data, 3, nstart = 25)

png("results/figures/cluster_plot.png", width = 800, height = 600, res=100)
fviz_cluster(km.res, data = cluster_data,
             geom = "point", axes = c(1, 2),
             ellipse.type = "convex", 
             ggtheme = theme_bw(),
             main = "K-Means Space (Complexity vs Tokens)")
invisible(dev.off())

# ------------------------------------------------------------------------------
# 2. Association Rules (Apriori) Mining
# ------------------------------------------------------------------------------
print("--> Modeling Phase 2: Apriori Association Rules Mining")
# Extract only categorical data for the apriori algorithm
rules_df <- df[, c("contains_code", "contains_examples", "contains_constraints", "is_successful")]
# Rename factors for interpretability in rules
levels(rules_df$is_successful) <- c("Failure", "Success")

rules <- apriori(rules_df, parameter = list(supp = 0.05, conf = 0.6, maxlen = 4), 
                 control = list(verbose = FALSE))

png("results/figures/association_rules.png", width = 1000, height = 800, res=100)
plot(rules, method="grouped", main="Grouped Matrix for Feature Rules")
invisible(dev.off())

# ------------------------------------------------------------------------------
# 3. Logistic Regression (Baseline for comparison vs Python XGBoost)
# ------------------------------------------------------------------------------
print("--> Modeling Phase 3: Binary Logistic Classification Model")

sample_index <- createDataPartition(df$is_successful, p = 0.8, list = FALSE)
train_data <- df[sample_index, ]
test_data <- df[-sample_index, ]

model_glm <- glm(is_successful ~ prompt_length + complexity_score + instruction_density + 
                 contains_code + contains_examples + contains_constraints, 
                 data = train_data, family = "binomial")

# Dump artifacts for Evaluation script
saveRDS(model_glm, "app/models/baseline_glm.rds")
saveRDS(test_data, "data/test_data.rds")

print("--> Modeling Complete! Models cached in app/models.")