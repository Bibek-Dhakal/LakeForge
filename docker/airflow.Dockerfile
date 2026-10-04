FROM apache/airflow:2.10.5-python3.11

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

USER airflow
COPY --chown=airflow:root pyproject.toml README.md LICENSE /opt/lakeforge/
COPY --chown=airflow:root src /opt/lakeforge/src
COPY --chown=airflow:root config /opt/lakeforge/config
RUN pip install --no-cache-dir "/opt/lakeforge[spark]"
COPY --chown=airflow:root airflow/dags /opt/airflow/dags

ENV CONFIG_DIR=/opt/lakeforge/config \
    LAKE_ROOT=/data/lake \
    SOURCE_DB_PATH=/data/source/reference.db
