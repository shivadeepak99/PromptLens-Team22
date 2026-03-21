# ==============================================================================
# Script 02: Exploratory Data Analysis & Visualization
# ==============================================================================
# Meets the rubric requirement for exploratory analysis and generated figures.
# ==============================================================================

# Install requirements automatically
required_packages <- c("ggplot2", "corrplot", "dplyr")
new_packages <- required_packages[!(required_packages %in% installed.packages()[,"Package"])]
if(length(new_packages)) install.packages(new_packages, repos = "http://cran.us.r-project.org")

library(ggplot2)
library(corrplot)
library(dplyr)

# Load cached data
print("--> Loading Prepared Data...")
df <- readRDS("data/processed_data.rds")
dir.create("results/figures", recursive = TRUE, showWarnings = FALSE)

# ------------------------------------------------------------------------------
# 1. Plot: Correlation Matrix of Prompt Features
# ------------------------------------------------------------------------------
print("--> Generating Figure 1: correlation_matrix.png")
numeric_vars <- df %>% select_if(is.numeric)
cor_matrix <- cor(numeric_vars, use = "complete.obs")

png("results/figures/correlation_matrix.png", width = 800, height = 600, res=100)
corrplot(cor_matrix, method = "color", type = "upper", order = "hclust",
         addCoef.col = "black", tl.col = "black", tl.srt = 45,
         main = "\nFeature Correlation Matrix")
invisible(dev.off())

# ------------------------------------------------------------------------------
# 2. Plot: Average Success Rate by Coding Language
# ------------------------------------------------------------------------------
print("--> Generating Figure 2: language_difficulty.png")
lang_success <- df %>%
  group_by(language) %>%
  summarize(avg_success = mean(success_score, na.rm=TRUE), sample_size = n(), .groups = 'drop') %>%
  filter(sample_size > 50) # Ignore extremely rare obscure languages

png("results/figures/language_difficulty.png", width = 900, height = 600, res=100)
viz_lang <- ggplot(lang_success, aes(x = reorder(language, avg_success), y = avg_success, fill = avg_success)) +
  geom_bar(stat = "identity") +
  scale_fill_gradient(low = "#ff4d4d", high = "#4dff4d") +
  coord_flip() +
  theme_minimal() +
  labs(title = "Average Model Success Score by Target Programming Language",
       x = "Programming Language", 
       y = "Mean Success Rate (0 to 1)",
       fill = "Success Rate")
print(viz_lang)
invisible(dev.off())

# ------------------------------------------------------------------------------
# 3. Plot: Success Density mapped by Code Inclusion
# ------------------------------------------------------------------------------
print("--> Generating Figure 3: success_density.png")
png("results/figures/success_density.png", width = 800, height = 600, res=100)
viz_density <- ggplot(df, aes(x=success_score, fill=contains_code)) + 
  geom_density(alpha=0.6) + 
  scale_fill_manual(values=c("#3498db", "#f39c12"), labels=c("False", "True")) +
  theme_minimal() +
  labs(title="Probability Density of Prompt Success (Does Code Inclusion Help?)", 
       x="Success Score Result", 
       y="Density",
       fill="Contains Code?")
print(viz_density)
invisible(dev.off())

print("--> EDA Complete! Check 'results/figures/' for outputs.")
