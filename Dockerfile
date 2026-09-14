
FROM python:3.12-slim

WORKDIR /app

# Install curl for health check
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home appuser && chown -R appuser:appuser /app

# Install uv
RUN pip install uv

# Copy dependency files first for Docker layer caching
COPY --chown=appuser:appuser pyproject.toml .
COPY --chown=appuser:appuser uv.lock* .

# Switch to non-root user
USER appuser

# Install dependencies without installing the project itself
RUN uv sync --no-dev --no-install-project

# Copy application code
COPY --chown=appuser:appuser app/ /app/app/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI directly from the virtual environment
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
