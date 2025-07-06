PROJECT_DIR ?= project
REPORT_FILE ?= comprehensive_report.json

.PHONY: help install scan dashboard run-assistant test clean

help:  ## Show this help message
	@echo "FastAPI Documentation Assistant"
	@echo "==============================="
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies with Poetry (fallback to pip if Poetry fails)
	@echo "🔧 Installing dependencies..."
	@if command -v poetry >/dev/null 2>&1; then \
		echo "Using Poetry..."; \
		poetry install || (echo "⚠️ Poetry failed, falling back to pip..."; pip install -e .); \
	else \
		echo "Poetry not found, using pip..."; \
		pip install -e .; \
	fi
	@echo "✅ Dependencies installed"

install-dev:  ## Install development dependencies
	@echo "🔧 Installing development dependencies..."
	@if command -v poetry >/dev/null 2>&1; then \
		poetry install --with dev || pip install -e ".[dev]"; \
	else \
		pip install -e ".[dev]"; \
	fi
	@echo "✅ Development dependencies installed"

install-pip:  ## Install using pip only
	@echo "🔧 Installing with pip..."
	pip install -e .
	@echo "✅ Dependencies installed via pip"

scan:  ## Scan FastAPI project for documentation analysis
	@echo "🔍 Scanning project: $(PROJECT_DIR)"
	python -c "from fastdoc.scanner import scan_file; import json, os; \
	all_items = []; \
	[all_items.extend(scan_file(os.path.join(root, fn))) for root, _, files in os.walk('$(PROJECT_DIR)') for fn in files if fn.endswith('.py')]; \
	open('$(REPORT_FILE)', 'w').write(json.dumps([item.__dict__ for item in all_items], indent=2)); \
	print(f'✅ Generated report with {len(all_items)} items -> $(REPORT_FILE)')"

dashboard:  ## Launch Streamlit documentation dashboard
	@echo "🚀 Launching documentation dashboard..."
	streamlit run scripts/streamlit_app.py --theme.base light

run-assistant:  ## Run complete documentation assistant workflow
	@echo "🎯 Starting FastAPI Documentation Assistant"
	python run_docs_assistant.py

test-scanner:  ## Test scanner on example project
	@echo "🧪 Testing scanner with example project"
	python -c "from fastdoc.scanner import scan_file; items = scan_file('example.py'); print(f'Found {len(items)} items in example.py')"

test-patcher:  ## Test patcher functionality
	@echo "🧪 Testing patcher functionality"
	python -c "from scripts.patcher import validate_docstring_syntax; result = validate_docstring_syntax('Test docstring.'); print(f'Validation: {result}')"

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
	@echo "🐳 Running Docker container"
	docker run -p 8501:8501 -v $(PWD):/workspace fastapi-docs-assistant

docker-compose-up:  ## Start services with docker-compose
	@echo "🐳 Starting services with docker-compose"
	docker-compose up --build

docker-compose-down:  ## Stop docker-compose services
	@echo "🐳 Stopping docker-compose services"
	docker-compose down

# Environment setup
check-env:  ## Check environment setup
	@echo "🔍 Checking environment"
	@python -c "import sys; print(f'Python: {sys.version}'); import streamlit; print(f'Streamlit: {streamlit.__version__}'); import pandas; print(f'Pandas: {pandas.__version__}')"
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