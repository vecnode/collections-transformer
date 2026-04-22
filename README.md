# Collections Transformer

Under heavy development.

Agent-based platform for multimodal LLM analysis of datasets in the GLAM sector.

Code developed in the context of the UKRI project "Transforming Collections" undertaken at UAL "Towards a National Collection (TaNC)".




## Reproduce

```bash
# 1) Use docker profile env
cp .env.docker.template .env

# 2) Optional: avoid host Mongo port conflict if installed locally
# Only do this for the Docker workflow below.
sudo systemctl stop mongod

# 3) Start full stack
docker compose -f docker/docker-compose.yml up -d --build

# 4) Smoke checks
curl -sS http://localhost/api/v1/health
curl -sS http://localhost/api/v1/readiness

# 5) App entrypoint
# http://localhost

# 6) Stop services when finished
docker compose -f docker/docker-compose.yml down
```


## Manual

```bash
# 1) Use local profile env
cp .env.local.template .env

# 2) Ensure MongoDB for local/manual mode
./scripts/ensure_mongodb.sh

# 2b) First-time local data restore so datasets, annotations and agents exist
./scripts/restore_local_seed_data.sh

# 3) Backend dependencies (one-time)
uv venv venv
source venv/bin/activate
uv pip install -r requirements.txt

# 4) Frontend dependencies (one-time)
cd client/
nvm install 20
nvm use 20
npm install
cd ..

# 5) Start backend with reload (Terminal 1)
./scripts/run_server.sh

# 6) Start frontend dev server (Terminal 2)
./scripts/run_client.sh

# 7) Local dev URLs
# Frontend: http://localhost:3000
# API:      http://localhost:8080/api/v1/health

# Optional quick API checks
curl -sS http://localhost:8080/api/v1/health
curl -sS http://localhost:8080/api/v1/readiness

# 8) Local API smoke tests (with backend + frontend running)
uv run tests/local/test_health.py
uv run tests/local/test_user_login.py
```



## Server configuration

Runtime settings are read from `.env` in the project root.

Quick setup:

```bash
# Local dev profile
cp .env.local.template .env

# Docker profile (compose + caddy)
cp .env.docker.template .env
```


Profile behavior:

- Local profile (`.env.local.template`)
  - Datastores on localhost (`127.0.0.1`, `localhost`)
  - Requires MongoDB listening on `127.0.0.1:27017`
  - `./scripts/ensure_mongodb.sh` will start `mongod` when available via systemd
  - `./scripts/restore_local_seed_data.sh` restores the bundled seed archive into local MongoDB
  - Redis is optional for app startup
  - `NEXT_PUBLIC_SERVER_URL=http://localhost:8080`
- Docker profile (`.env.docker.template`)
  - Datastores on container DNS (`mongodb`, `redis`)
  - `NEXT_PUBLIC_SERVER_URL=http://localhost` (browser via Caddy)
  - `OLLAMA_BASE_URL=http://host.docker.internal:11434` by default

For Docker, `OLLAMA_BASE_URL` must be reachable from containers.

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



### Bruno API collection

An importable Bruno collection for the live API is stored in [bruno/README.md](./bruno/README.md) and the surrounding `bruno/` folder.

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

