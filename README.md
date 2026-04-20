# Collections Transformer

Under heavy development.

Agent-based platform for multimodal LLM analysis of datasets in the GLAM sector.

Code developed in the context of the UKRI project "Transforming Collections" undertaken at UAL "Towards a National Collection (TaNC)".




## Reproduce

```bash
sudo systemctl stop mongod

# Start all services
docker compose -f docker/docker-compose.yml up -d --build

# App entrypoint
# http://localhost

# Stop services
docker compose -f docker/docker-compose.yml down
```


### Manual

```bash
c
```



## Server configuration

Runtime settings are loaded from `.env` (project root), using:

- `server/app/core/config.py` (FastAPI app and worker)
- `server/config.py` (legacy compatibility entrypoints)

1. Choose an environment profile template and copy it to `.env` in the project root:

```bash
# Local/manual backend + frontend dev
cp .env.local.template .env

# Docker deployment via compose + caddy
cp .env.docker.template .env
```

2. If you need a single generic baseline, `.env.template` is also available.
3. Set the values you need for your environment.
4. Restart containers/services after changing env vars.

Profile guidance:

- Local profile (`.env.local.template`)
	- Uses localhost datastore URLs (`127.0.0.1`, `localhost`).
	- Sets `NEXT_PUBLIC_SERVER_URL=http://localhost:8080` for manual frontend-to-backend calls.
- Docker profile (`.env.docker.template`)
	- Uses container service DNS (`mongodb`, `redis`) for backend runtime.
	- Sets `NEXT_PUBLIC_SERVER_URL=http://localhost` so browser traffic goes through Caddy.
	- Uses `OLLAMA_BASE_URL=http://host.docker.internal:11434` by default.

For Docker deployments, set `OLLAMA_BASE_URL` to a network-reachable endpoint from containers.
Default in compose is `http://host.docker.internal:11434`.

Important variables:

- `ENVIRONMENT`, `LOG_LEVEL`
- `API_HOST`, `API_PORT`, `API_RELOAD`, `SECRET_KEY`
- `MONGODB_URI`, `MONGODB_DATABASE`
- `REDIS_URL`
- `NEXT_PUBLIC_SERVER_URL`
- `OLLAMA_MODEL_OPTION`, `OLLAMA_BASE_URL`
- `BLIP2_MODEL_NAME`

Inference providers:

- Text inference: Ollama (`OLLAMA_BASE_URL`, `OLLAMA_MODEL_OPTION`)
- Image inference: Blip2 (`BLIP2_MODEL_NAME`, default `Salesforce/blip2-opt-2.7b`)

### Current deployment

Current Docker Compose topology (`docker/docker-compose.yml`):

- `caddy` (reverse proxy / edge) on `:80` (public entrypoint)
- `client` (Next.js, internal)
- `api` (FastAPI, internal)
- `worker` (background job processor)
- `mongodb` on `:27017`
- `redis` on `:6379`
- `mongo-seed` (one-shot seed restore)

Proxy routing:

- `/` -> `client:3000`
- `/backend*` -> `api:8080`
- `/api*` -> `api:8080`

### API contract convergence

Canonical API surface is versioned under `/api/v1/*`.

- Native v1 routes: `/api/v1/health`, `/api/v1/readiness`, `/api/v1/transforms*`
- Backend application routes: `/api/v1/backend/*`

Examples:

- `/api/v1/backend/agents`
- `/api/v1/backend/datasets`
- `/api/v1/backend/analysis/*`
- `/api/v1/backend/user/*`
- `/api/v1/backend/ollama/models`

Legacy `/backend/*` endpoints have been removed from the FastAPI application.
New integrations should target `/api/v1/*` only.

### Bruno API collection

An importable Bruno collection for the live API is stored in [bruno/README.md](/home/luisarandas/Desktop/collections-transformer/bruno/README.md) and the surrounding `bruno/` folder.

The collection mirrors the active FastAPI router groups:

- `01 Health` -> `/api/v1/health`, `/api/v1/readiness`
- `02 Transforms` -> `/api/v1/transforms*`
- `03 User` -> `/api/v1/backend/user/*`
- `04 Datasets` -> `/api/v1/backend/dataset*`
- `05 Agents` -> `/api/v1/backend/agent*`
- `06 Labelsets` -> `/api/v1/backend/labelsets`, `/api/v1/backend/update_label`
- `07 Analysis` -> `/api/v1/backend/analysis/*`, `/api/v1/backend/item*`
- `08 System` -> `/api/v1/backend/ollama/models`

To use it:

1. Open the `bruno/` folder in Bruno.
2. Select the `Local` environment.
3. Update the placeholder IDs in `bruno/environments/Local.bru`.
4. Run requests against `http://localhost`, which matches the Docker + Caddy setup.

Connection flow for deployment:

- Browser -> `caddy` -> `client`
- Browser -> `caddy` -> `api` (`/backend` and `/api` routes)
- `api` <-> `mongodb`
- `api` <-> `redis`
- `worker` <-> `redis` and `mongodb`
- `api` <-> Ollama (`OLLAMA_BASE_URL`, external or reachable network endpoint)

Notes:

- Public entrypoint is `http://localhost` (via Caddy on port 80)
- `api` and `client` are intentionally internal-only in this deployment mode

