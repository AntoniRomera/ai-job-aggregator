# Convenience targets for the AI Job Aggregator.
# Run `make help` for a summary.

PYTHON ?= python3
PIP ?= pip

.DEFAULT_GOAL := help

.PHONY: help install install-browsers run serve seed estimate test lint format typecheck web-install web-dev clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Install backend runtime + dev dependencies
	$(PIP) install -r requirements.txt -r requirements-dev.txt

install-browsers: ## Install Playwright's headless Chromium (only needed for live sources)
	$(PYTHON) -m playwright install chromium

run: ## Collect -> store -> enrich using configured SOURCES (offline by default)
	$(PYTHON) -m collector run

serve: ## Start the FastAPI server (http://localhost:8000)
	$(PYTHON) -m collector serve

seed: ## Load the bundled sample/seed dataset into the database
	$(PYTHON) -m collector seed

estimate: ## Re-run the salary estimator over stored postings missing salary
	$(PYTHON) -m collector estimate

test: ## Run the offline test suite
	$(PYTHON) -m pytest

lint: ## Lint with ruff
	$(PYTHON) -m ruff check collector tests

format: ## Format with black + ruff import sorting
	$(PYTHON) -m black collector tests
	$(PYTHON) -m ruff check --fix collector tests

typecheck: ## Static type checking with mypy
	$(PYTHON) -m mypy collector

web-install: ## Install frontend dependencies
	cd web && npm install

web-dev: ## Start the Vite dev server (http://localhost:5173)
	cd web && npm run dev

clean: ## Remove generated database + caches
	rm -f collector/data/jobs.db
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache .mypy_cache
