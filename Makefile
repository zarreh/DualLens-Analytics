# ──────────────────────────────────────────────────────────────
# DualLens Analytics – Makefile
# ──────────────────────────────────────────────────────────────
.DEFAULT_GOAL := help
SHELL := /bin/bash

# ── Variables ────────────────────────────────────────────────
SRC      := src/duallens_analytics
TESTS    := tests
APP      := $(SRC)/app.py
CONF     := conf/config.yaml

# ── Help ─────────────────────────────────────────────────────
.PHONY: help
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ── Install ──────────────────────────────────────────────────
.PHONY: install
install: ## Install all dependencies (main + dev)
	poetry install

# ── Run ──────────────────────────────────────────────────────
.PHONY: run
run: ## Launch the Streamlit app
	poetry run streamlit run $(APP)

.PHONY: hydra
hydra: ## Print resolved Hydra config (accepts ARGS=, e.g. make hydra ARGS="llm.model=gpt-4o")
	poetry run python -m duallens_analytics.cli $(ARGS)

# ── Quality ──────────────────────────────────────────────────
.PHONY: lint
lint: ## Run Ruff linter (check mode)
	poetry run ruff check $(SRC) $(TESTS)

.PHONY: lint-fix
lint-fix: ## Run Ruff linter and auto-fix
	poetry run ruff check --fix $(SRC) $(TESTS)

.PHONY: format
format: ## Format code with Ruff
	poetry run ruff format $(SRC) $(TESTS)

.PHONY: format-check
format-check: ## Check formatting without changing files
	poetry run ruff format --check $(SRC) $(TESTS)

# ── Tests ────────────────────────────────────────────────────
.PHONY: test
test: ## Run unit tests with pytest
	poetry run pytest $(TESTS)

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	poetry run pytest --cov=$(SRC) --cov-report=term-missing $(TESTS)

# ── Documentation ─────────────────────────────────────────────
.PHONY: docs
docs: ## Build MkDocs site (output in site/)
	poetry run mkdocs build --strict

.PHONY: docs-serve
docs-serve: ## Serve docs locally with live-reload
	poetry run mkdocs serve

# ── All-in-one ───────────────────────────────────────────────
.PHONY: check
check: lint format-check test ## Run lint + format-check + tests

.PHONY: clean
clean: ## Remove generated artifacts
	rm -rf data/ .ruff_cache/ .pytest_cache/ outputs/ site/ \
		$(SRC)/__pycache__ $(TESTS)/__pycache__ .coverage
