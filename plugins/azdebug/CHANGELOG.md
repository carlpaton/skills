# Changelog

## 0.2.0

### Added
- `/azdebug:blobs`: find files in a storage account and pull them to local disk or read them into context (`--shape` summary, capped excerpts). Defaults to your login, with the account key only on request.
- `blobs.py` shared helper: read-only list, pull (no overwrite) and show.

## 0.1.0

### Added
- `/azdebug:foundry`: read-only debugging of Foundry / Azure OpenAI deployments with a structured table report from a mandatory template (`report.md.tmpl`).
- Shared rules and a `metrics.py` helper for Azure Monitor metrics.
