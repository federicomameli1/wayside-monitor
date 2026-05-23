"""HTTP entrypoint for the Wayside Monitor container.

Exposes /healthz for Kubernetes probes and / for module version inventory.
The pipeline modules themselves are imported so import errors surface at
startup rather than on first event."""

from fastapi import FastAPI

import alert_dispatcher
import anomaly_engine
import sensor_collector

app = FastAPI(title="Wayside Monitor")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def index() -> dict[str, object]:
    return {
        "service": "wayside-monitor",
        "modules": {
            "sensor_collector": sensor_collector.__version__,
            "anomaly_engine": anomaly_engine.__version__,
            "alert_dispatcher": alert_dispatcher.__version__,
        },
    }
