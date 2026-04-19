# Caddy Reverse Proxy Deployment

This project now includes a Caddy edge container for production-like deployment.

## What changed

- Added a Caddy service in docker/docker-compose.yml.
- Added docker/Caddyfile with path-based routing.
- Exposed a single public entrypoint: port 80.
- Kept client and api internal-only behind Caddy.

## How it works

Request flow:

- Browser -> Caddy (:80)
- / -> client:3000 (Next.js UI)
- /backend* -> api:8080 (FastAPI legacy/backend routes)
- /api* -> api:8080 (versioned API routes)

Internal service flow:

- api -> mongodb
- api <-> redis
- worker <-> redis and mongodb
- api <-> ollama (via OLLAMA_BASE_URL)

## Why this is useful

- One public port instead of exposing frontend and backend separately.
- Cleaner deployment model for VPS/cloud/container platforms.
- Central place for compression and security headers.
- Easier future TLS setup with Caddy.

## Run

docker compose -f docker/docker-compose.yml up -d --build

Open: http://localhost

## Notes

- OLLAMA_BASE_URL must be reachable from containers.
- Default compose value is http://host.docker.internal:11434.
- If Ollama runs elsewhere, set OLLAMA_BASE_URL accordingly in .env.
