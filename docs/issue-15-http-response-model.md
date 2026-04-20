# Issue #15 HTTP Response Model

## Goal
Standardize HTTP status codes and JSON response bodies across the FastAPI application without forcing an immediate frontend rewrite.

## Response contract
All API responses should now follow one of two shapes.

### Success
```json
{
  "ok": true,
  "status_code": 200,
  "status": "200",
  "message": "Optional success message",
  "data": {}
}
```

### Error
```json
{
  "ok": false,
  "status_code": 400,
  "status": "400",
  "message": "Human-readable error message",
  "error": {
    "code": "bad_request",
    "message": "Human-readable error message",
    "details": []
  },
  "data": {}
}
```

## Why both `status_code` and `status`
`status_code` is the canonical field for the new contract.
`status` is retained temporarily as a compatibility shim because the current frontend still reads string status values in multiple places.

## HTTP semantics
- Validation problems use `400` or `422`.
- Missing resources use `404`.
- Authorization failures use `403`.
- Queue/service availability issues use `503`.
- Successful creation flows use `201`.
- Successful async queue submission uses `202`.

## Shared implementation
The contract is implemented in `server/app/api_responses.py`.

## Exception handling
Global exception handlers in `server/app/main.py` normalize:
- `HTTPException`
- `RequestValidationError`
- unhandled exceptions

## Scope applied in this change
- Active `/api/v1/backend/*` routes
- `/api/v1/health`
- `/api/v1/readiness`
- `/api/v1/transforms*`

## Migration note
Frontend code can keep working during the transition because legacy body fields such as `status`, `message`, and `data` are still present.
Future cleanup can remove the compatibility `status` string once all callers consume `ok`, `status_code`, and structured `error` payloads.
