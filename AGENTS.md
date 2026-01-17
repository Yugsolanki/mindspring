# Agent Guidelines for Mindspring API

This document provides guidelines for AI agents working on the Mindspring API codebase.

## Project Overview

Mindspring API is a FastAPI-based web scraping and content extraction service with:
- Python 3.11+ with async/await throughout
- SQLAlchemy 2.0 with async database operations
- Pydantic v2 for validation
- Celery for background task processing
- Redis for caching and message broker
- PostgreSQL database
- Docker Compose for local development

## Build, Lint, and Test Commands

### Package Management (uv)
```bash
# Install dependencies
uv sync

# Add a new dependency
uv add <package>

# Add a dev dependency
uv add --dev <package>

# Update dependencies
uv lock --upgrade
```

### Running the Application
```bash
# Development (with auto-reload)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Celery Workers
```bash
# Start Celery worker
celery -A app.core.celery_app worker --loglevel=info

# Start flower for monitoring
celery -A app.core.celery_app flower --loglevel=info --port=5555
```

### Database Migrations (Alembic)
```bash
# Generate a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Check current migration status
alembic current
```

### Linting and Formatting
```bash
# Run ruff linter (auto-fix)
ruff check --fix

# Run ruff formatter
ruff format

# Run pre-commit hooks on all files
pre-commit run --all-files
```

### Testing
```bash
# Run all tests
pytest

# Run a single test file
pytest tests/test_file.py

# Run a specific test
pytest tests/test_file.py::test_function_name

# Run tests with verbose output
pytest -v

# Run tests and show coverage
pytest --cov=app --cov-report=term-missing
```

### Docker
```bash
# Start all services (postgres, redis, api, celery)
docker compose up -d

# Start only debug profile (postgres, redis)
docker compose --profile debug up -d

# Start production profile
docker compose --profile prod up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

## Code Style Guidelines

### Imports
- Use absolute imports with `app.` prefix: `from app.core.config import settings`
- Group imports in this order: standard library, third-party, local application
- Do NOT add comments separating import groups (per project style)

### Formatting
- Line length: 88 characters (ruff default)
- Use ruff formatter - do not manually format
- No trailing whitespace
- Use 4 spaces for indentation (no tabs)

### Type Hints
- Use Python 3.11+ syntax with built-in generic types
- Always specify return types for functions
- Use `list[T]`, `dict[K, V]`, `Optional[T]` instead of List, Dict, Optional from typing
- Use `|` operator for unions: `str | None` instead of `Optional[str]`

### Naming Conventions
- **Files**: snake_case (e.g., `content_scraper.py`, `scraped_resource.py`)
- **Classes**: PascalCase (e.g., `ScrapedResource`, `AppException`)
- **Functions/methods**: snake_case (e.g., `get_content()`, `run_scraper()`)
- **Variables**: snake_case (e.g., `content_hash`, `resource_id`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_RETRY_COUNT`)
- **Private methods**: prefix with `_` (e.g., `_internal_helper()`)

### Async/Await
- Use async/await for all I/O-bound operations (database, HTTP, file I/O)
- Never block in async code - use `await` or run in executor
- Keep async functions non-blocking

### Error Handling
- Use custom exception hierarchy from `app/core/exceptions.py`
- Base exception: `AppException` with message and status_code
- Specific exceptions: `NotFoundException`, `BadRequestException`, `DatabaseException`
- Always log exceptions with context before re-raising
- Return proper JSON responses with `SuccessResponseModel` or error responses

### Database Operations (SQLAlchemy 2.0)
- Use async sessionmaker: `AsyncSession`
- Always use `await session.commit()` after writes
- Use try/except with explicit `await session.rollback()` on failures
- Use `model_dump()` for Pydantic serialization
- Use `from_attributes = True` in Pydantic ConfigDict for ORM models

### Pydantic Models
- Use Pydantic v2 syntax (`model_config = ConfigDict(...)`)
- Define schemas in `app/schemas/`
- Base schemas: `*Base`, `*Create`, `*Update`, `*Response`
- Use `Field()` with descriptions for API documentation
- Use `model_validator` for cross-field validation

### API Endpoints
- Use FastAPI with type hints and dependency injection
- Return `SuccessResponseModel[T]` wrapper for all responses
- Use status codes: 201 for created, 204 for deleted (no content)
- Document endpoints with docstrings

### Response Format
```python
from app.core.response import SuccessResponseModel

return SuccessResponseModel(
    message="Operation completed",
    data=result
)
```

### Logging
- Use structured logging via `app.core.logging.logger`
- Log at appropriate levels: DEBUG, INFO, WARNING, ERROR
- Include context (request path, method, user_id) in log extras

### Git Workflow
- Write meaningful commit messages
- Create small, focused PRs
- Run `ruff check --fix` and `ruff format` before committing
- Do NOT commit changes to `__pycache__`, `.pyc`, or `.ruff_cache`

### Pre-commit Hooks
- Install hooks: `pre-commit install`
- Hooks run ruff check and format automatically on commit
- Fix any issues before committing

### File Structure
```
app/
  api/v1/endpoints/  # FastAPI route handlers
  core/              # Config, exceptions, database, logging
  models/            # SQLAlchemy ORM models
  repositories/      # Database access layer
  schemas/           # Pydantic validation schemas
  services/          # Business logic
  utils/             # Helper functions
  workers/           # Celery tasks
```
