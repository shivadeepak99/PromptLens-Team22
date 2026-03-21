# ==============================================================================
# Script 04: Model Evaluation
# ==============================================================================
# Student: Balaga Lokesh (2023BCS0141) / Team PromptLens
# Description: Evaluates the Logistic Regression baseline model generating 
# performance metrics (Confusion Matrix) and visual analysis (ROC curves).
# Evaluates predictive strength upon out-of-sample data.
# ==============================================================================

# --- SECTION 1: Setup and Environment Preparation ---
# Validate evaluation specific packages exist within the environment
required_packages <- c("pROC", "caret")
new_packages <- required_packages[!(required_packages %in% installed.packages()[,"Package"])]
if (length(new_packages)) {
  install.packages(new_packages, repos = "http://cran.us.r-project.org")
}

library(pROC)
library(caret)

print("--> Loading saved test vectors and Logistic Model...")

# Ingest test split constructed during Script 03
test_data <- readRDS("data/test_data.rds")
# Ingest compiled logistic regression weights
model_glm <- readRDS("app/models/baseline_glm.rds")

# Generate destination paths for both statistical tables and graphic curves
dir.create("results/figures", recursive = TRUE, showWarnings = FALSE)
dir.create("results/tables", recursive = TRUE, showWarnings = FALSE)

# --- SECTION 2: Model Inference Pipeline ---
# Compute predictive probabilities mapping [0,1]
predictions_prob <- predict(model_glm, newdata = test_data, type = "response")

# Coerce probabilities through strictly separated mathematical threshold > 0.5 
predictions_class <- ifelse(predictions_prob > 0.5, 1, 0)

# Factorize resulting vector aligning dimension mapping with actuals
predictions_class <- factor(predictions_class, levels = c(0, 1))

# --- SECTION 3: Statistical Evaluation (Confusion Matrix) ---
print("--> Generating Confusion Matrix...")

# Use caret framework to calculate robust metrics (Accuracy, Precision, Recall, F1)
cm <- confusionMatrix(predictions_class, test_data$is_successful)

# Pipe output buffer directly into persistent evaluation log requirement
capture.output(print(cm), file = "results/tables/eval_confusion_matrix.txt")
print("Confusion Matrix written to results/tables/eval_confusion_matrix.txt")

# --- SECTION 4: Visual ROC Diagnostic Graphic ---
print("--> Plotting Receiver Operating Characteristic (ROC) curve...")

# Initialize the mathematical ROC structural object defining false/true positive rates
roc_obj <- roc(test_data$is_successful, predictions_prob, quiet=TRUE)

# Serialize mathematical layout into a formatted PNG projection matrix
png("results/figures/roc_curve.png", width = 800, height = 600, res=100)

# Render graphical curve attaching dynamically quantified Area Under Curve (AUC) value
plot(roc_obj, col="#2980b9", lwd=3, main=paste("Logistic Classification ROC Curve (AUC =", round(auc(roc_obj), 3), ")"))

# Overlay absolute baseline (Null hypothesis line representing coin toss) 
abline(a=0, b=1, col="gray", lty=2)

# Prevent spurious output blocks disrupting standard terminal flow
invisible(dev.off())

print("--> All Evaluations Complete! Full data science loop finished successfully.")
