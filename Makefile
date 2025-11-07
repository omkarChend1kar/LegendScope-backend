.PHONY: help install install-dev venv clean lint format test run docker-build docker-run docker-stop deploy

PYTHON := python3.11
VENV := .venv
BIN := $(VENV)/bin
DOCKER_IMAGE := legendscope-backend
DOCKER_TAG := latest

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

venv: ## Create virtual environment
	$(PYTHON) -m venv $(VENV)
	@echo "Virtual environment created. Activate with: source $(BIN)/activate"

install: venv ## Install production dependencies
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements.txt

install-dev: venv ## Install development dependencies
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements-dev.txt

clean: ## Remove virtual environment and cache files
	rm -rf $(VENV)
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +

lint: ## Run ruff linter
	$(BIN)/ruff check .

format: ## Format code with ruff
	$(BIN)/ruff format .

format-check: ## Check code formatting without changes
	$(BIN)/ruff format --check .

test: ## Run tests with pytest
	$(BIN)/pytest

test-cov: ## Run tests with coverage report
	$(BIN)/pytest --cov=app --cov-report=html --cov-report=term

run: ## Run the FastAPI application locally
	$(BIN)/uvicorn app.main:app --reload --host 0.0.0.0 --port 3000

run-prod: ## Run the FastAPI application in production mode
	$(BIN)/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

docker-build: ## Build Docker image
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

docker-run: ## Run application in Docker container
	docker run -d --name legendscope -p 8000:8000 --env-file .env $(DOCKER_IMAGE):$(DOCKER_TAG)

docker-stop: ## Stop and remove Docker container
	docker stop legendscope || true
	docker rm legendscope || true

docker-compose-up: ## Start services with docker-compose
	docker-compose up -d

docker-compose-down: ## Stop services with docker-compose
	docker-compose down

docker-logs: ## View Docker container logs
	docker logs -f legendscope

deploy: ## Deploy to EC2 (requires SSH access)
	@echo "Creating deployment archive..."
	tar -czf release.tar.gz app requirements.txt pyproject.toml .env.example scripts infra
	@echo "Uploading to EC2..."
	scp release.tar.gz $(EC2_USER)@$(EC2_HOST):~/deployments/legendscope/
	@echo "Running deployment script..."
	ssh $(EC2_USER)@$(EC2_HOST) "cd ~/deployments/legendscope && tar -xzf release.tar.gz && bash scripts/deploy.sh"
	@echo "Deployment complete!"
	rm release.tar.gz

all: install-dev lint format test ## Install, lint, format, and test
