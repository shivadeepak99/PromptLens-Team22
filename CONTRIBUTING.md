# Contributing to PromptLens

We welcome contributions from the engineering community to expand the capabilities of PromptLens. As a platform focused on large-scale AI telemetry and data engineering, we prioritize robust, well-tested, and optimized code.

## Development Workflow

1. **Fork and Branch:** Fork the repository and create your feature branch from `main` (`git checkout -b feature/amazing-feature`).
2. **Environment Setup:** Follow the Quick Start guide in the `README.md` to configure your local development environment. 
3. **Commit Standards:** Use conventional commit messages (e.g., `feat:`, `fix:`, `refactor:`, `docs:`).
4. **Testing:** Ensure your changes are covered by tests. Run the test suite before submitting a PR.
5. **Pull Request:** Open a PR against the `main` branch. Provide a clear description of the problem solved or the feature added.

## Areas for Contribution

- **ETL Adapters:** New dataset ingestion adapters for platforms like HuggingFace or proprietary formats.
- **Warehouse Optimization:** Improvements to the OLAP queries, indexes, or materialized views.
- **ML Models:** Incorporating advanced embedding models or alternative clustering algorithms.
- **Dashboard UI:** Enhancing the Next.js visual components and adding new telemetry views.

## Code Style

- **Python (ETL & API):** Follow PEP 8 guidelines. Type hints are strongly encouraged.
- **R (Analytics):** Use `styler` or adhere to standard tidyverse style guides.
- **Frontend (TypeScript):** Adhere to the configured ESLint and Prettier rules.
