"""HTTP entrypoint for the Wayside Monitor container.

Exposes /healthz for Kubernetes probes, / for module version inventory,
and /health/stats for operations dashboards (REQ-WMS-027).
The pipeline modules themselves are imported so import errors surface at
startup rather than on first event."""

from fastapi import FastAPI

import alert_dispatcher
import anomaly_engine
import sensor_collector
from alert_dispatcher.dispatcher import AlertDispatcher

app = FastAPI(title="Wayside Monitor")

# Module-level dispatcher instance used for /health/stats reporting.
# In the full pipeline this instance would be shared with the event loop.
_dispatcher = AlertDispatcher()


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


@app.get("/health/stats")
def health_stats() -> dict[str, object]:
    """Aggregated health and delivery statistics (REQ-WMS-027).

    Returns module versions and alert_dispatcher delivery counters so
    operations dashboards and the Verdict cluster health poller can
    monitor the system without scraping individual module endpoints.
    """
    return {
        "module_versions": {
            "sensor_collector": sensor_collector.__version__,
            "anomaly_engine": anomaly_engine.__version__,
            "alert_dispatcher": alert_dispatcher.__version__,
        },
        "alert_dispatcher_stats": _dispatcher.stats(),
    }
