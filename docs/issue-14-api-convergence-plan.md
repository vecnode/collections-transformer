# Issue #14 API Convergence Plan

## Goal
Converge legacy `/backend/*` endpoints and existing `/api/v1/*` endpoints under a single versioned contract.

## Canonical contract
Use `/api/v1/*` as the canonical API surface.

### Native v1 routes
- `/api/v1/health`
- `/api/v1/readiness`
- `/api/v1/transforms`
- `/api/v1/transforms/{job_id}`

### Versioned backend routes
Backend application routes live under `/api/v1/backend/*`.

Examples:
- `/api/v1/backend/agents`
- `/api/v1/backend/dataset`
- `/api/v1/backend/datasets`
- `/api/v1/backend/analysis/save`
- `/api/v1/backend/analysis/history`
- `/api/v1/backend/analysis/delete`
- `/api/v1/backend/ollama/models`
- `/api/v1/backend/item_image`
- `/api/v1/backend/update_label`

## Removed legacy routes
Legacy `/backend/*` endpoints have been removed from the FastAPI application.

Frontend callers were migrated to `/api/v1/backend/*`.

## Removed unused endpoint surface
- Authentication endpoints under `/backend/auth/*`
- Category endpoints under `/backend/category*` and `/backend/categories`
- Model source endpoint `/backend/model_source`
- Unused labelset mutation/read endpoints not referenced by the current frontend
- Debug database endpoints under `/backend/db/*`
- Unused text-only agent execution endpoint `/backend/agent_execute`

## Notes
- The Caddy proxy may still forward `/backend*` to the API container, but those routes are no longer served by FastAPI.
- New integrations should target `/api/v1/*` only.
