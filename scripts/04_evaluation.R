# ==============================================================================
# Script 04: Model Evaluation
# ==============================================================================
# Generates ROC curve and cross-validates confusion matrix metrics.
# ==============================================================================

required_packages <- c("pROC", "caret")
new_packages <- required_packages[!(required_packages %in% installed.packages()[,"Package"])]
if(length(new_packages)) install.packages(new_packages, repos = "http://cran.us.r-project.org")

library(pROC)
library(caret)

print("--> Loading saved test vectors and Logistic Model...")
test_data <- readRDS("data/test_data.rds")
model_glm <- readRDS("app/models/baseline_glm.rds")

dir.create("results/figures", recursive = TRUE, showWarnings = FALSE)
dir.create("results/tables", recursive = TRUE, showWarnings = FALSE)

# Probabilistic Predictions
predictions_prob <- predict(model_glm, newdata = test_data, type = "response")
predictions_class <- ifelse(predictions_prob > 0.5, 1, 0)
predictions_class <- factor(predictions_class, levels = c(0, 1))

# Generate Confusion Matrix
print("--> Generating Confusion Matrix...")
cm <- confusionMatrix(predictions_class, test_data$is_successful)

# Save string output to report table folder
capture.output(print(cm), file = "results/tables/eval_confusion_matrix.txt")
print("Confusion Matrix written to results/tables/eval_confusion_matrix.txt")

# Generate ROC Curve Graphic
print("--> Plotting Receiver Operating Characteristic (ROC) curve...")
roc_obj <- roc(test_data$is_successful, predictions_prob, quiet=TRUE)

png("results/figures/roc_curve.png", width = 800, height = 600, res=100)
plot(roc_obj, col="#2980b9", lwd=3, main=paste("Logistic Classification ROC Curve (AUC =", round(auc(roc_obj), 3), ")"))
# Add diagonal reference line
abline(a=0, b=1, col="gray", lty=2)
invisible(dev.off())

print("--> All Evaluations Complete! Full data science loop finished successfully.")
