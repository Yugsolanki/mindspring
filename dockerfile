# Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast Python package installer)
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Copy application code
COPY . .

# Install TurboScraper as a package
WORKDIR /app/libs/TurboScraper
RUN uv pip install --system -e .

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

WORKDIR /app

# Install Python dependencies using uv
RUN uv pip install --system -r pyproject.toml

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]