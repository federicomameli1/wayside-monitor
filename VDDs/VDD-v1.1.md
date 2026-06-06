## Introduction

### Purpose
This Version Description Document (VDD) describes the software release v1.1 (Release test) of the Wayside Monitor System (WMS), intended for promotion from DEV to TEST stage.

### Applicability
This document applies to the WMS release v1.1 and supersedes any prior VDD for this software baseline.

### Terms, Acronyms and Abbreviations
_No release notes provided._

### Reference Documents (Contractual / Project / Tender / Standards / GBMS)
- APCS_Requirements.txt (Requirements Master List, Candidate 2.1.0-rc.1)
- APCS_Module_Version_Inventory.txt (Module / Version Inventory, Candidate 2.1.0-rc.1)
- APCS_Test_Procedure.txt (Pre-Promotion Test Procedure, Candidate 2.2.0-rc.1)
- APCS_VDD.txt (Version Description Document, Candidate 2.1.0-rc.1)
- APCS_Emails.txt (Release Email Thread, Candidate 2.1.0-rc.1)

### Description of Changes from the Previous Revision
The release v1.1 represents the same baseline as v0.10, introducing the three-class vibration anomaly classifier in anomaly-engine and the corresponding payload update in alert-dispatcher. The sensor-collector module remains unchanged at version 1.3.0.

Changed modules:
- anomaly-engine: 2.0.1 → 2.1.0-rc.1 (vibration classifier upgrade, new confidence field)
- alert-dispatcher: 1.1.3 → 1.2.0-rc.1 (payload schema v1.0 → v1.1, DEGRADED severity support)
- ci.yml: 1.0.1 → 1.0.2 (model artefact checksum verification step)
- wms-chart: 0.2.2 → 0.3.0 (anomalyEngine.modelVersion value added)

## Version Description

### Inventory of materials released
- Container image: ghcr.io/federicomameli1/wayside-monitor:2.1.0-rc.1 (multi-arch, linux/amd64 + linux/arm64)
- Helm chart: deploy/helm/wms-chart 0.3.0
- Validated model artefact: vibration_model_v2.pkl bundled in image

### Inventory of software configuration items contents — identification, checksums, reference of components used
| Module | Version | Source |
|---|---|---|
| alert_dispatcher | 1.2.0-rc.1 | alert_dispatcher/__init__.py |
| anomaly_engine | 2.1.0-rc.1 | anomaly_engine/__init__.py |
| sensor_collector | 1.3.0 | sensor_collector/__init__.py |

Model artefact:
- vibration_model_v2.pkl (SHA-256: a3f9e2b14cc87d3f6501a9e4bc2f77a8d1e043bc9f28a51d6c3b0e7f4d9a2c1)

## Documentation Related to the Baseline

### Requirements specification documents
APCS_Requirements.txt defines the following requirements applicable to this release:
- REQ-WMS-001: Sensor collection at minimum 10 Hz sampling rate
- REQ-WMS-002: Unknown sensor type rejection
- REQ-WMS-003: Hot-reload of sensor registry (SHOULD)
- REQ-WMS-004: Prometheus /metrics endpoint (COULD)
- REQ-WMS-005: Anomaly processing within 500 ms
- REQ-WMS-006: Rail temperature CRITICAL classification above 60°C
- REQ-WMS-007: Vibration classifier validation against reference dataset
- REQ-WMS-008: Three severity classes (NOMINAL, DEGRADED, CRITICAL)
- REQ-WMS-009: No event loss with queue back-pressure
- REQ-WMS-010: Confidence score attachment (SHOULD)
- REQ-WMS-011: Model version traceability (SHOULD)
- REQ-WMS-012: CRITICAL alert delivery within 2 seconds
- REQ-WMS-013: JSON payload structure with required fields
- REQ-WMS-014: Exponential back-off retry with dead-letter logging
- REQ-WMS-015: Payload schema backward compatibility
- REQ-WMS-016: Multiple endpoint types (SHOULD)
- REQ-WMS-017: NOMINAL alert batching (COULD)
- REQ-WMS-018: Internal event schema versioning
- REQ-WMS-019: Severity field label constraints
- REQ-WMS-020: Redis Streams for inter-module communication
- REQ-WMS-021: /health endpoint per module
- REQ-WMS-022: No silent exception swallowing
- REQ-WMS-023: 500 events/sec throughput (SHOULD)
- REQ-WMS-024: JSON structured logging (SHOULD)
- REQ-WMS-025: Graceful shutdown (COULD)
- REQ-WMS-026: CRITICAL alert deduplication within 30 seconds
- REQ-WMS-027: /health/stats endpoint
- REQ-WMS-028: Sensor sequence number (SHOULD)
- REQ-WMS-029: Sensor silence detection with configurable timeout
- REQ-WMS-030: Per-sensor rail wear rate-of-change detection (MUST)

### Software conception, design, programming documents
_Evidence not available in this release bundle._

### Testing documentation
APCS_Test_Procedure.txt defines the following test cases:
- TC-WMS-001: Nominal sensor ingestion (MUST) - PASS
- TC-WMS-002: Unknown sensor type rejection (MUST) - PASS
- TC-WMS-003: Vibration model accuracy validation (MUST) - PASS (97.2% accuracy)
- TC-WMS-004: Rail temperature CRITICAL gate (MUST) - PASS
- TC-WMS-005: Three-class severity label contract (MUST) - PASS
- TC-WMS-006: Alert-dispatcher JSON schema compliance (MUST) - PASS
- TC-WMS-007: CRITICAL alert delivery latency under load (MUST) - PASS
- TC-WMS-008: Retry and dead-letter on endpoint failure (MUST) - PASS
- TC-WMS-009: Module health endpoints (MUST) - PASS
- TC-WMS-010: Confidence score presence (SHOULD) - PASS with soft warning
- TC-WMS-011: Model version traceability in payload (SHOULD) - PASS
- TC-WMS-012: Model artefact checksum verification (MUST) - PASS
- TC-WMS-013: CRITICAL alert deduplication (MUST) - PASS
- TC-WMS-014: Health stats endpoint availability (MUST) - PASS
- TC-WMS-015: Sensor sequence number continuity (SHOULD) - PASS

### Other documents
APCS_VDD.txt and APCS_Emails.txt provide additional release context and approval communications.

## Sw Version Build

### SW Configuration items list (source files) — list only application source modules and configuration files that constitute the released software
- alert_dispatcher/ (Python package, version 1.2.0-rc.1)
- anomaly_engine/ (Python package, version 2.1.0-rc.1)
- sensor_collector/ (Python package, version 1.3.0)
- config/thresholds.yaml (version 1.1.0)

### Build Environment for Reproducibility
_Evidence not available in this release bundle._

## Changes Incorporated

### List of changes taken into account in this SW version
- anomaly-engine 2.0.1 → 2.1.0-rc.1: 2-class threshold model replaced with 3-class statistical model (NOMINAL/DEGRADED/CRITICAL), new confidence field added
- alert-dispatcher 1.1.3 → 1.2.0-rc.1: payload schema v1.0 → v1.1, DEGRADED severity support, model_ver field added
- ci.yml 1.0.1 → 1.0.2: model artefact checksum verification step added
- wms-chart 0.2.2 → 0.3.0: anomalyEngine.modelVersion value added

### List of changes NOT taken into account in this SW version
- Migration of sensor-collector to async I/O (planned for v1.4.0)
- DEGRADED alert batching (REQ-WMS-017, deferred to v1.3.0 of alert-dispatcher)
- Prometheus /metrics endpoint on sensor-collector (REQ-WMS-004, COULD)
- Graceful shutdown drain (REQ-WMS-025, COULD)

##