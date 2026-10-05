FROM apache/airflow:2.8.1-python3.11

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

USER airflow
COPY --chown=airflow:0 pyproject.toml README.md LICENSE /opt/lakeforge/
COPY --chown=airflow:0 src /opt/lakeforge/src
COPY --chown=airflow:0 config /opt/lakeforge/config

RUN pip install --no-cache-dir -e /opt/lakeforge[spark]

ENV PYTHONPATH=/opt/lakeforge/src
COPY --chown=airflow:0 airflow/dags /opt/airflow/dags
