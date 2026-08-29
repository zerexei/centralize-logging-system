# Set base image
FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim

# Set the working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV UV_PROJECT_ENVIRONMENT=/app/.venv

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Copy application
COPY . .

# Run the app
ENV PATH="/app/.venv/bin:$PATH"

CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "3001"]