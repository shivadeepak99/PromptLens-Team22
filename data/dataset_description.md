# Dataset Name: PromptLens Multi-Source Prompt Database

**Source**: Open source prompt libraries (chatbot_arena_conversations, sharegpt, etc.)
**Number of instances**: ~190,000 executed prompts
**Number of attributes**: 15 main features (extracted via NLP)

**Description**:
This dataset contains vectorized syntax features extracted from massive open-source prompt libraries. It includes text complexity scores, token counts, boolean syntax indicators (contains code, contains constraints, contains examples), programming language classification, and their corresponding execution success rates (0.0 to 1.0).

**How to Download/Access**:
Do **NOT** download manually. The `scripts/01_data_preparation.R` script is natively hardcoded to connect directly to the project's cloud data warehouse (Neon PostgreSQL). Running the `01_` script will automatically execute the necessary SQL, download the prepared `data/processed_data.rds` file locally, and skip exposing large CSV files to GitHub.