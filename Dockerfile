# ── Stage 1: build (install deps into a venv) ──────────────
FROM python:3.12-slim AS builder

ENV POETRY_VERSION=1.8.5 \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

# Install Poetry
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

WORKDIR /app

# Copy only dependency manifests first (layer caching)
COPY pyproject.toml poetry.lock ./

# Install runtime deps only (no dev/docs groups)
RUN poetry install --only main --no-root

# Copy source tree + data assets
COPY src/ src/
COPY conf/ conf/
COPY notebooks/Companies-AI-Initiatives.zip notebooks/
COPY README.md .

# Install the project itself (editable-style into the venv)
RUN poetry install --only main


# ── Stage 2: runtime (slim final image) ────────────────────
FROM python:3.12-slim AS runtime

# Streamlit telemetry off, unbuffered output
ENV PYTHONUNBUFFERED=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_HEADLESS=true

WORKDIR /app

# Copy the pre-built venv and project files from builder
COPY --from=builder /app/.venv .venv
COPY --from=builder /app/src src
COPY --from=builder /app/conf conf
COPY --from=builder /app/notebooks/Companies-AI-Initiatives.zip notebooks/
COPY --from=builder /app/pyproject.toml .

# Activate venv by prepending it to PATH
ENV PATH="/app/.venv/bin:${PATH}" \
    VIRTUAL_ENV="/app/.venv"

# Streamlit default port
EXPOSE 8510

# Health check – Streamlit exposes /_stcore/health
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8510/_stcore/health', timeout=3)"

# Run the Streamlit app
ENTRYPOINT ["streamlit", "run", "src/duallens_analytics/app.py", \
            "--server.port=8510", \
            "--server.address=0.0.0.0"]
