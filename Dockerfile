# Flask Documentation Assistant Docker Image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry (specific version)
RUN pip install poetry==1.7.1

# Configure Poetry to not create virtual environment (we're in a container)
ENV POETRY_VENV_IN_PROJECT=false
ENV POETRY_NO_INTERACTION=1
ENV POETRY_CACHE_DIR=/tmp/poetry_cache

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies (try both new and old syntax)
RUN poetry install --only=main || poetry install --no-dev && rm -rf $POETRY_CACHE_DIR

# Copy application code
COPY . .

# Create directory for reports and backups
RUN mkdir -p /app/reports /app/backups

# Expose port for Flask
EXPOSE 8200

# Set environment variables
ENV PYTHONPATH=/app
ENV PROJECT_BASE_PATH=/app/demo_sample_project
ENV REPORTS_DIR=/app/reports
ENV BACKUPS_DIR=/app/backups
ENV DEMO_MODE=true

# Health check for Flask
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8200/health || exit 1

# Default command - run the Flask application
CMD ["python", "main.py"]