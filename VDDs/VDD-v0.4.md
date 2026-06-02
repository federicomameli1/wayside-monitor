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

### Software conception, design, programming