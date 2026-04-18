# Correct by Construction JetBrains Sidecar Stub

This folder is a lightweight Phase 10 shell, not a full buildable plugin.

## Purpose

- Point a JetBrains-side UI shell to the local sidecar API.
- Keep IDE surface thin and artifact-driven.
- Avoid adding brittle build or packaging complexity during the hackathon phase.

## Expected Local API

Base URL default: `http://127.0.0.1:8765`

Endpoints:

- `GET /healthz`
- `GET /runs?limit=50`
- `GET /runs/{run_id}`
- `GET /benchmarks?limit=50`

## Suggested Integration Pattern

1. Read `sidecar-config.json` for base URL.
2. Poll `/runs` and `/benchmarks` to populate tool window lists.
3. Open `/runs/{run_id}` to render review summary and merge-gate verdict.
4. Keep trust logic in backend artifacts, never in UI.
