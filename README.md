# Wayside Monitor System (WM)

Real-time trackside anomaly detection pipeline for railway infrastructure.
Collects sensor data, classifies anomalies, and dispatches alerts to operators.

## Architecture

```
trackside sensors
      │
      ▼
sensor-collector   ──[wms:sensor-events]──▶   anomaly-engine   ──[wms:anomaly-events]──▶   alert-dispatcher
  validates type                                classifies                                    routes alerts
  drops unknowns                                attaches confidence                           retries/dead-letter
```

## Modules

| Module | Version | Responsibility |
|--------|---------|----------------|
| `sensor_collector` | 1.3.0 | Reads trackside sensors, validates against registry, forwards to message bus |
| `anomaly_engine` | 2.1.0-rc.1 | Classifies events into NOMINAL / DEGRADED / CRITICAL; emits confidence scores |
| `alert_dispatcher` | 1.2.0-rc.1 | Routes alerts to operator endpoints with retry and dead-letter |

## Sensor types

| Type | Unit | Classification |
|------|------|---------------|
| TEMPERATURE | celsius | Rule-based: ≥ 60°C → CRITICAL |
| VIBRATION | m/s² | 3-class statistical model (vibration_model_v2.pkl) |
| RAIL_WEAR | mm | Threshold: ≥ 8 mm → CRITICAL, ≥ 5 mm → DEGRADED |
| CURRENT | A | Threshold-based |

## Running tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Configuration

Thresholds and sensor registry are in [config/thresholds.yaml](config/thresholds.yaml).

Environment variables:

| Variable | Module | Default | Purpose |
|----------|--------|---------|---------|
| `ANOMALY_ENGINE_MODEL_VER` | anomaly-engine | `vibration_model_v2.pkl` | Model version tag emitted in every event |
| `COLLECTOR_STREAM` | sensor-collector | `wms:sensor-events` | Redis Streams stream name |
| `ENGINE_STREAM` | anomaly-engine | `wms:anomaly-events` | Redis Streams stream name |
| `ALERT_WEBHOOK_URLS` | alert-dispatcher | — | Comma-separated webhook URLs for CRITICAL alerts |
| `MONITOR_WEBHOOK_URLS` | alert-dispatcher | — | Comma-separated webhook URLs for DEGRADED/NOMINAL |
| `DEAD_LETTER_PATH` | alert-dispatcher | `/tmp/wms-dead-letter.jsonl` | Dead-letter log path |

## Release documentation

APCS release documents are in [docs/](docs/):

- [APCS_Requirements.txt](docs/APCS_Requirements.txt)
- [APCS_Module_Version_Inventory.txt](docs/APCS_Module_Version_Inventory.txt)
- [APCS_Test_Procedure.txt](docs/APCS_Test_Procedure.txt)
- [APCS_VDD.txt](docs/APCS_VDD.txt)
- [APCS_Emails.txt](docs/APCS_Emails.txt)

## CI integration with challenge-app

On every push to `main`, the CI workflow notifies `challenge-app` via webhook.
`challenge-app` runs Agent 4 against the APCS bundle in `docs/` and produces
a release-readiness report. Configure `CHALLENGE_APP_WEBHOOK` as a repository
secret pointing to the challenge-app instance on CrownLabs.
