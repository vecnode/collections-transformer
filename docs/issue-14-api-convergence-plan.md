# Issue #14 API Convergence Plan

## Goal
Converge legacy `/backend/*` endpoints and existing `/api/v1/*` endpoints under a single versioned contract, without breaking current frontend behavior.

## Canonical contract
Use `/api/v1/*` as the canonical API surface.

### Native v1 routes
- `/api/v1/health`
- `/api/v1/readiness`
- `/api/v1/transforms`
- `/api/v1/transforms/{job_id}`

### Versioned compatibility shims for legacy backend
Legacy backend routes are also available under `/api/v1/backend/*`.

Examples:
- `/backend/agents` -> `/api/v1/backend/agents`
- `/backend/dataset` -> `/api/v1/backend/dataset`
- `/backend/datasets` -> `/api/v1/backend/datasets`
- `/backend/analysis/save` -> `/api/v1/backend/analysis/save`
- `/backend/analysis/history` -> `/api/v1/backend/analysis/history`
- `/backend/analysis/delete` -> `/api/v1/backend/analysis/delete`
- `/backend/ollama/models` -> `/api/v1/backend/ollama/models`

## Deprecation policy
`/backend/*` remains available as a compatibility layer to prevent frontend regressions.

Every `/backend/*` response includes:
- `Deprecation: true`
- `Sunset: Wed, 31 Dec 2026 23:59:59 GMT`
- `Warning: 299 - "Legacy /backend endpoints are deprecated; use /api/v1/backend"`
- `Link: </api/v1/backend>; rel="successor-version"`

## Migration phases
1. New integrations must use `/api/v1/*` only.
2. Frontend fetch calls should migrate from `/backend/*` to `/api/v1/backend/*`.
3. Bruno/API collections should switch defaults to versioned paths.
4. After migration completion, remove `/backend/*` routes.

## Non-goals for this issue
- No behavioral changes to business logic.
- No endpoint removal yet.
- No frontend rewrite in this issue.
