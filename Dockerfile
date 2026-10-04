FROM python:3.11-slim-bookworm AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LAKE_ROOT=/data/lake \
    SOURCE_DB_PATH=/data/source/reference.db \
    CONFIG_DIR=/app/config
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY config ./config

# ---- Analytics API (no Spark / Java) ----
FROM base AS serving
RUN pip install --no-cache-dir ".[serving]"
EXPOSE 8000
CMD ["uvicorn", "lakeforge.serving.app:app", "--host", "0.0.0.0", "--port", "8000"]

# ---- Batch pipeline (Spark + Delta, needs Java) ----
FROM base AS pipeline
RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jre-headless procps \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir ".[spark]"
ENTRYPOINT ["lakeforge"]
CMD ["--help"]
