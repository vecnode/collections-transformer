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

```bash
# Migrate your SQLite file (optional)
cp ~/my_old_data/db.sqlite server/db/db.sqlite
./scripts/build_seed_archive_from_sqlite.sh
# server/db/tanc_database.archive.gz
```

After that, fresh deployments use the archive automatically:

### Manual

```bash
# Set up backend and frontend environments
uv venv venv
source venv/bin/activate
uv pip install -r requirements.txt

# Set up frontend (from root in another terminal)
cd client/
nvm install 20
nvm use 20
npm install

# Start services
# Terminal 1 (from root, backend - development):
cd server/
python3 app.py

# Terminal 1 (from root, backend - production with Gunicorn):
./scripts/run_server_prod.sh

# Terminal 2 (from root/client, frontend):
npm run dev
```



## Server configuration

Runtime settings are loaded from `.env` (project root), using:

- `server/app/core/config.py` (FastAPI app and worker)
- `server/config.py` (legacy compatibility entrypoints)

1. Copy `.env.template` to `.env` in the project root.
2. Set the values you need for your environment.
3. Restart containers/services after changing env vars.

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

Canonical API surface is now versioned under `/api/v1/*`.

- Existing versioned routes: `/api/v1/health`, `/api/v1/readiness`, `/api/v1/transforms*`
- Legacy backend routes are also exposed under versioned paths using compatibility shims:
	- `/backend/agents` -> `/api/v1/backend/agents`
	- `/backend/datasets` -> `/api/v1/backend/datasets`
	- `/backend/analysis/*` -> `/api/v1/backend/analysis/*`
	- and other `/backend/*` routes under `/api/v1/backend/*`

Deprecation plan:

- `/backend/*` remains functional to avoid frontend regressions.
- `/backend/*` responses include deprecation headers (`Deprecation`, `Sunset`, `Warning`, `Link`).
- New integrations should target `/api/v1/*` only.

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

