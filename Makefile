PROJECT_DIR ?= ./project
REPORT_FILE ?= comprehensive_report.json
EXTERNAL_PROJECT_DIR ?=

.PHONY: help install scan scan-verbose scan-external frontend frontend-dev run-assistant test clean docker-build docker-up docker-down

help:  ## Show this help message
	@echo "FastAPI Documentation Assistant"
	@echo "==============================="
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies with Poetry (fallback to pip if Poetry fails)
	@echo "Installing dependencies..."
	@if command -v poetry >/dev/null 2>&1; then \
		echo "Using Poetry..."; \
		poetry install || (echo "Poetry failed, falling back to pip..."; pip install typer fastapi uvicorn); \
	else \
		echo "Poetry not found, using pip..."; \
		pip install typer fastapi uvicorn; \
	fi
	@echo "Dependencies installed"

install-dev:  ## Install development dependencies
	@echo "🔧 Installing development dependencies..."
	@if command -v poetry >/dev/null 2>&1; then \
		poetry install --with dev || pip install -e ".[dev]"; \
	else \
		pip install -e ".[dev]"; \
	fi
	@echo "✅ Development dependencies installed"

install-pip:  ## Install using pip only
	@echo "Installing with pip..."
	pip install typer fastapi uvicorn
	@echo "Dependencies installed via pip"

scan:  ## Scan FastAPI project for documentation analysis
	@if [ -n "$(EXTERNAL_PROJECT_DIR)" ]; then \
		echo "Scanning external project: $(EXTERNAL_PROJECT_DIR)"; \
		docker run --rm -v "$(EXTERNAL_PROJECT_DIR):/app/external_project:ro" -v "$(PWD)/reports:/app/reports" \
			$$(docker-compose config --services | head -1) \
			python fastdoc/cli.py /app/external_project --out /app/reports/$(REPORT_FILE); \
	else \
		echo "Scanning default project: $(PROJECT_DIR)"; \
		docker-compose --profile scanner run --rm docs-scanner; \
	fi

scan-verbose:  ## Scan project with verbose output
	@if [ -n "$(EXTERNAL_PROJECT_DIR)" ]; then \
		echo "Scanning external project: $(EXTERNAL_PROJECT_DIR) (verbose)"; \
		docker run --rm -v "$(EXTERNAL_PROJECT_DIR):/app/external_project:ro" -v "$(PWD)/reports:/app/reports" \
			$$(docker-compose config --services | head -1) \
			python fastdoc/cli.py /app/external_project --out /app/reports/$(REPORT_FILE) --verbose; \
	else \
		echo "Scanning default project: $(PROJECT_DIR) (verbose)"; \
		docker-compose --profile scanner run --rm docs-scanner; \
	fi

scan-external:  ## Scan external project directory (usage: make scan-external EXTERNAL_PROJECT_DIR=/path/to/project)
	@if [ -z "$(EXTERNAL_PROJECT_DIR)" ]; then \
		echo "Error: Please specify EXTERNAL_PROJECT_DIR"; \
		echo "Usage: make scan-external EXTERNAL_PROJECT_DIR=/path/to/your/project"; \
		exit 1; \
	fi
	@echo "Scanning external project: $(EXTERNAL_PROJECT_DIR)"
	@if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then \
		echo "Using Docker for scanning..."; \
		docker run --rm \
			-v "$(EXTERNAL_PROJECT_DIR):/app/external_project:ro" \
			-v "$(PWD)/reports:/app/reports" \
			$$(docker build -q .) \
			python fastdoc/cli.py /app/external_project --out /app/reports/$(REPORT_FILE) --verbose; \
	else \
		echo "Docker not available, using local Python..."; \
		mkdir -p reports; \
		PYTHONPATH=$$PWD python fastdoc/cli.py "$(EXTERNAL_PROJECT_DIR)" --out reports/$(REPORT_FILE) --verbose; \
	fi

scan-local:  ## Scan project using local Python (no Docker required)
	@if [ -z "$(EXTERNAL_PROJECT_DIR)" ]; then \
		echo "Error: Please specify EXTERNAL_PROJECT_DIR"; \
		echo "Usage: make scan-local EXTERNAL_PROJECT_DIR=/path/to/your/project"; \
		exit 1; \
	fi
	@echo "Scanning project locally: $(EXTERNAL_PROJECT_DIR)"
	@mkdir -p reports
	PYTHONPATH=$$PWD python fastdoc/cli.py "$(EXTERNAL_PROJECT_DIR)" --out reports/$(REPORT_FILE) --verbose

frontend:  ## Launch HTML frontend with FastAPI backend (using Docker)
	@echo "Starting FastAPI Documentation Assistant..."
	@echo "Frontend: http://localhost:8200"
	@echo "API docs: http://localhost:8200/docs"
	@mkdir -p reports backups
	docker run --rm -p 8200:8200 \
		-v "$(PWD)/reports:/app/reports" \
		-v "$(PWD)/backups:/app/backups" \
		$$(docker build -q .) \
		uvicorn main:app --host 0.0.0.0 --port 8200 --reload

frontend-dev:  ## Launch frontend for development (direct host)
	@echo "Starting frontend in development mode..."
	@echo "Frontend: http://localhost:8200"
	uvicorn main:app --host 0.0.0.0 --port 8200 --reload

run-assistant:  ## Run complete documentation assistant workflow
	@echo "🎯 Starting FastAPI Documentation Assistant"
	python archive/run_docs_assistant.py

test-scanner:  ## Test scanner on example project
	@echo "🧪 Testing scanner with example project"
	python -c "from fastdoc.scanner import scan_file; items = scan_file('archive/example.py'); print(f'Found {len(items)} items in archive/example.py')"

test-patcher:  ## Test patcher functionality
	@echo "🧪 Testing patcher functionality"
	python -c "from services.patcher import validate_docstring_syntax; result = validate_docstring_syntax('Test docstring.'); print(f'Validation: {result}')"

clean:  ## Clean generated files
	@echo "🧹 Cleaning generated files"
	rm -f *.json
	rm -f *.backup_*
	rm -f **/*.backup_*
	@echo "✅ Cleaned generated files"

docker-build:  ## Build Docker image
	@echo "🐳 Building Docker image"
	docker build -t fastapi-docs-assistant .

docker-run:  ## Run Docker container
	@echo "Running Docker container"
	docker run -p 8200:8200 -v $(PWD):/workspace fastapi-docs-assistant

docker-up:  ## Start services with docker-compose
	@echo "Starting services with docker-compose"
	@mkdir -p reports backups
	docker-compose up --build

docker-down:  ## Stop docker-compose services
	@echo "Stopping docker-compose services"
	docker-compose down

docker-compose-up:  ## Start services with docker-compose (alias)
	make docker-up

docker-compose-down:  ## Stop docker-compose services (alias)
	make docker-down

# Environment setup
check-env:  ## Check environment setup
	@echo "🔍 Checking environment"
	@python -c "import sys; print(f'Python: {sys.version}'); import fastapi; print(f'FastAPI: {fastapi.__version__}'); import uvicorn; print(f'Uvicorn: {uvicorn.__version__}'); import pandas; print(f'Pandas: {pandas.__version__}')"
	@if [ -n "$$OPENAI_API_KEY" ]; then echo "✅ OPENAI_API_KEY is set"; else echo "⚠️  OPENAI_API_KEY not set (optional)"; fi

# Development commands
format:  ## Format code with black
	black fastdoc/ scripts/ *.py

lint:  ## Lint code with flake8
	flake8 fastdoc/ scripts/ *.py

type-check:  ## Type check with mypy
	mypy fastdoc/ scripts/

dev-setup:  ## Complete development setup
	make install-dev
	make check-env
	@echo "🎉 Development environment ready!"

# Confluence integration commands
confluence-status:  ## Check Confluence integration status
	@echo "🔗 Checking Confluence status..."
	PYTHONPATH=$$PWD python fastdoc/cli.py confluence-status

publish-coverage:  ## Publish coverage report to Confluence (usage: make publish-coverage REPORT_FILE=report.json)
	@if [ -z "$(REPORT_FILE)" ]; then \
		echo "Error: Please specify REPORT_FILE"; \
		echo "Usage: make publish-coverage REPORT_FILE=reports/my_report.json"; \
		exit 1; \
	fi
	@echo "📊 Publishing coverage report to Confluence..."
	PYTHONPATH=$$PWD python fastdoc/cli.py publish-coverage "$(REPORT_FILE)" --to-confluence

publish-endpoints:  ## Publish endpoint docs to Confluence (usage: make publish-endpoints REPORT_FILE=report.json)
	@if [ -z "$(REPORT_FILE)" ]; then \
		echo "Error: Please specify REPORT_FILE"; \
		echo "Usage: make publish-endpoints REPORT_FILE=reports/my_report.json"; \
		exit 1; \
	fi
	@echo "🚀 Publishing endpoints to Confluence..."
	PYTHONPATH=$$PWD python fastdoc/cli.py publish-endpoints "$(REPORT_FILE)" --to-confluence

publish-all:  ## Publish both coverage report and endpoints (usage: make publish-all REPORT_FILE=report.json)
	@if [ -z "$(REPORT_FILE)" ]; then \
		echo "Error: Please specify REPORT_FILE"; \
		echo "Usage: make publish-all REPORT_FILE=reports/my_report.json"; \
		exit 1; \
	fi
	@echo "📚 Publishing everything to Confluence..."
	make publish-coverage REPORT_FILE="$(REPORT_FILE)"
	make publish-endpoints REPORT_FILE="$(REPORT_FILE)"