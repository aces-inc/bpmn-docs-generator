# process-to-pptx: YAML / mxGraph XML → PPTX
# Python + uv (Constraint: uv を使用)
FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Dependencies and package
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev \
    && chmod +x /app/scripts/docker-entrypoint.sh

# Default: convert all YAML in /input to /output
ENV INPUT_DIR=/input OUTPUT_DIR=/output
ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
