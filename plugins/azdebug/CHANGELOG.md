# Changelog

## 0.3.0

### Added
- `/azdebug:loganalytics`: find a Log Analytics workspace and query it read-only. Seven canned queries for Container Apps (tables with data, console levels, failures, exceptions, failures by hour, system events, restarts) plus custom KQL.
- `loganalytics/report.md.tmpl`: a mandatory report template for `/azdebug:loganalytics`, so results always have the same sections and table columns. Presets output columns in the template's order.
- `loganalytics.py` shared helper: refuses control commands, caps rows and cell width, and the presets never print raw message bodies.

## 0.2.0

### Added
- `/azdebug:blobs`: find files in a storage account and pull them to local disk or read them into context (`--shape` summary, capped excerpts). Defaults to your login, with the account key only on request.
- `blobs.py` shared helper: read-only list, pull (no overwrite) and show.

## 0.1.0

### Added
- `/azdebug:foundry`: read-only debugging of Foundry / Azure OpenAI deployments with a structured table report from a mandatory template (`report.md.tmpl`).
- Shared rules and a `metrics.py` helper for Azure Monitor metrics.
