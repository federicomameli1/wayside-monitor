## Introduction

### Purpose
This document provides the formal version description for the Wayside Monitor System (WMS) release v0.4, detailing the software configuration, changes, and validation evidence required for promotion from DEV to TEST.

### Applicability
This release applies to the trackside anomaly detection pipeline, specifically the `anomaly_engine`, `alert_dispatcher`, and `sensor_collector` modules, and the associated deployment configuration.

### Terms, Acronyms and Abbreviations
- **WMS**: Wayside Monitor System
- **SNR**: Signal-to-Noise Ratio
- **SHA-256**: Secure Hash Algorithm 256-bit
- **CI**: Continuous Integration
- **DEV/TEST/PROD**: Development, Testing, and Production environments

### Reference Documents (Contractual / Project / Tender / Standards / GBMS)
- APCS_Requirements.txt (Requirements Master List)
- APCS_Module_Version_Inventory.txt (Module / Version Inventory)
- APCS_Test_Procedure.txt (Pre-Promotion Test Procedure)
- APCS_VDD.txt (Candidate 2.1.0-rc.1 VDD)
- APCS_Emails.txt (Release Email Thread)

### Description of Changes from the Previous Revision
This release introduces the three-class vibration anomaly classifier in anomaly-engine and the corresponding payload update in alert-dispatcher. The sensor_collector module adds monotonic sequence number support per REQ-WMS-028 and sensor silence detection per REQ-WMS-029. The alert_dispatcher adds CRITICAL alert deduplication per REQ-WMS-026 and statistics endpoint per REQ-WMS-027.

## Version Description

### Inventory of materials released
- **Container Image**: `ghcr.io/federicomameli1/wayside-monitor:v0.4`
- **Helm Chart**: `wms-chart` version 0.3.0 (appVersion 0.1.1)
- **Configuration**: `config/thresholds.yaml` (vibration nominal_max_ms2 updated to 3.0)
- **APCS Bundle**: Requirements, Module Inventory, Test Procedure, and Release Email threads.

### Inventory of software configuration items contents — identification, checksums, reference of components used
| Component | Version | Identification/Checksum | Reference |
|---|---|---|---|
| `sensor_collector` | 1.3.0 | _Evidence not available_ | `sensor_collector/__init__.py` |
| `anomaly_engine` | 2.1.0-rc.1 | Model SHA-256: `a3f9e2b14cc87d3f6501a9e4bc2f77a8d1e043bc9f28a51d6c3b0e7f4d9a2c1` | `anomaly_engine/__init__.py` |
| `alert_dispatcher` | 1.2.0-rc.1 | _Evidence not available_ | `alert_dispatcher/__init__.py` |
| `wms-chart` | 0.3.0 | _Evidence not available_ | `deploy/helm/Chart.yaml` |

## Documentation Related to the Baseline

### Requirements specification documents
- **Requirements Master List**: APCS_Requirements.txt (Candidate 2.1.0-rc.1), including REQ-WMS-001 through REQ-WMS-029.

### Software conception, design, programming documents
_Evidence not available in this release bundle._

### Testing documentation
- **Pre-Promotion Test Procedure**: APCS_Test_Procedure.txt.
- **Test Results**: 
    - TC-WMS-001, TC-WMS-002, TC-WMS-004 through TC-WMS-009: PASS.
    - TC-WMS-003 (Vibration model accuracy): PASS (97.2% accuracy).
    - TC-WMS-010, TC-WMS-011: PASS (with soft warnings).
    - TC-WMS-012 (Checksum verification): PASS.

### Other documents
- **Release Email Thread**: APCS_Emails.txt (Safety sign-off by Sofia Bianchi).

## Sw Version Build

### SW Configuration items list (source files)
- `alert_dispatcher/dispatcher.py`
- `alert_dispatcher/models.py`
- `anomaly_engine/models.py`
- `sensor_collector/collector.py`
- `sensor_collector/models.py`
- `config/thresholds.yaml`
- `deploy/helm/Chart.yaml`
- `deploy/helm/templates/deployment.yaml`
- `deploy/docker/app.py`

### Build Environment for Reproducibility
- **Python Version**: 3.11
- **Dependencies**: `pydantic`, `python-docx`
- **CI Pipeline**: GitHub Actions (as defined in `.github/workflows/`)

## Changes Incorporated

### List of changes taken into account in this SW version
- **anomaly-engine (2.0.1 → 2.1.0-rc.1)**:
    - Implementation of 3-class statistical model (NOMINAL/DEGRADED/CRITICAL) per REQ-WMS-008.
    - Addition of optional `confidence` field to output events per REQ-WMS-010.
    - Integration of `vibration_model_v2.pkl`.
- **alert-dispatcher (1.1.3 → 1.2.0-rc.1)**:
    - Payload schema update (v1.0 → v1.1) to support DEGRADED severity per REQ-WMS-013.
    - New routing for DEGRADED alerts to "monitor" endpoint group.
    - Addition of `model_ver` field for traceability per REQ-WMS-011.
    - CRITICAL alert deduplication within 30-second window per REQ-WMS-026.
    - Statistics endpoint exposing dispatched, suppressed, dead_lettered counters per REQ-WMS-027.
- **sensor-collector (1.2.0 → 1.3.0)**:
    - Monotonic sequence number (`seq`) field on SensorReading events per REQ-WMS-028.
    - Sensor silence detection with DEGRADED health alert per REQ-WMS-029.
- **Infrastructure**:
    - `ci.yml` (1.0.1 → 1.0.2): Added model artefact checksum verification (TC-WMS-012).
    - `wms-chart` (0.2.2 → 0.3.0): Added `anomalyEngine.modelVersion` environment variable.

### List of changes NOT taken into account in this SW version
- Migration of `sensor-collector` to async I/O (planned for v1.4.0).
- DEGRADED alert batching (REQ-WMS-017, deferred to `alert-dispatcher` v1.3.0).
- Prometheus `/metrics` endpoint on `sensor-collector` (REQ-WMS-004).
- Graceful shutdown drain (REQ-WMS-025).

## Sw Version Limitation
- **Backward Compatibility**: `alert-dispatcher` 1.2.0 is NOT backward compatible with `anomaly-engine` 2.0.x payloads; incorrect deployment order will cause event rejection.
- **Operational**: The `confidence` field is not yet surfaced in the ops dashboard (accessible via syslog only).
- **Documentation**: Operator runbooks for the DEGRADED alert tier are currently in draft.

## Installation Instructions
_Evidence not available in this release bundle._

---
_Auto-drafted by Verdict on release `v0.4`._