# syntax=docker/dockerfile:1.7

FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
        pyyaml>=6.0 \
        fastapi>=0.115.0 \
        uvicorn>=0.30.0

COPY sensor_collector ./sensor_collector
COPY anomaly_engine ./anomaly_engine
COPY alert_dispatcher ./alert_dispatcher
COPY config ./config
COPY deploy/docker/app.py ./app.py

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
