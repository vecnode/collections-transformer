# Bruno Collection

This folder contains an importable Bruno collection for the live FastAPI routes exposed by this repository.

Groups mirror the current router layout:

- `01 Health` -> `server/app/routers/v1/health.py`
- `02 Transforms` -> `server/app/routers/v1/transforms.py`
- `03 User` -> `server/app/routers/backend/auth.py`
- `04 Datasets` -> `server/app/routers/backend/datasets.py`
- `05 Agents` -> `server/app/routers/backend/agents.py`
- `06 Labelsets` -> `server/app/routers/backend/labelsets.py`
- `07 Analysis` -> `server/app/routers/backend/analysis.py`
- `08 System` -> `server/app/routers/backend/system.py`

Usage:

1. Open the `bruno/` folder in Bruno.
2. Select the `Local` environment.
3. Update the placeholder IDs in `environments/Local.bru` before running requests that require existing resources.
4. For dataset upload requests, replace the example file paths/body values with real files from your machine.

Base URL defaults to `http://localhost`, which matches the Docker + Caddy setup in this repository.
todo