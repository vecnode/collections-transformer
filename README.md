# Collections Transformer

Under heavy development.

Agent-based platform for multimodal LLM analysis of datasets in the GLAM sector.

Code developed in the context of the UKRI project "Transforming Collections" undertaken at UAL "Towards a National Collection (TaNC)".




## Reproduce


```bash
sudo systemctl stop mongod

# Start all services
docker compose -f docker/docker-compose.yml up -d --build

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

- `client` (Next.js) on `:3000`
- `api` (FastAPI) on `:8080`
- `worker` (background job processor)
- `mongodb` on `:27017`
- `redis` on `:6379`
- `mongo-seed` (one-shot seed restore)

