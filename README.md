# Collections Transformer

Under heavy development.

Agent-based platform for multimodal LLM analysis of datasets in the GLAM sector.

Code developed in the context of the UKRI project "Transforming Collections" undertaken at UAL "Towards a National Collection (TaNC)".




## Reproduce

- Frontend requirement: Node.js >= 18.17.0 (recommended: Node 20 LTS).

### Recommended: Mixed Mode (Containers + Local Development)

```bash
# 1. Place your SQLite file (optional)
cp ~/my_old_data/db.sqlite server/db/db.sqlite

# 2. Start Docker
docker compose -f docker/docker-compose.yml up redis mongodb worker

# 3. Start the app
./start_platform.sh
```

### Fast Mongo Seed Workflow (Recommended for Repeated Deployments)

Build a Mongo-native seed archive once from `server/db/db.sqlite`, then reuse it for fast container restores.

```bash
# One-time: build seed archive (this can take time)
./scripts/build_seed_archive_from_sqlite.sh

# Produces:
# server/db/tanc_database.archive.gz
```

After that, fresh deployments use the archive automatically:

```bash
# Fresh startup (mongo-seed restores if database is empty)
docker compose -f docker/docker-compose.yml up redis mongodb worker

# Start app locally
./start_platform.sh
```

Notes:
- `mongo-seed` restores from `server/db/tanc_database.archive.gz` only when Mongo is empty.
- If Mongo already has data, seed restore is skipped.
- This avoids repeated heavy SQLite-to-Mongo migrations on normal restarts.

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


```bash
./scripts/create_server_env.sh
./scripts/run_server.sh
./scripts/run_client.sh
```

### Full Docker Setup (All containerized)

```bash
# Start all services
docker compose -f docker/docker-compose.yml up --build

# Stop services
docker compose -f docker/docker-compose.yml down
```

## Server configuration

Server settings are centralized in `server/config.py`.

1. Copy `server/.env.template` to `server/.env`.
2. Configure Ollama settings (`OLLAMA_BASE_URL` and `OLLAMA_MODEL_OPTION`).
3. Adjust runtime values only if needed (`API_PORT`, `MONGODB_URI`, `LOG_LEVEL`, `OLLAMA_BASE_URL`).

Important variables:

- `ENVIRONMENT`, `LOG_LEVEL`
- `API_HOST`, `API_PORT`, `FLASK_DEBUG`, `FLASK_RELOAD`
- `MONGODB_URI`, `MONGODB_DATABASE`
- `OLLAMA_MODEL_OPTION`, `OLLAMA_BASE_URL`
- `BLIP2_MODEL_NAME`



## Quality checks

Run locally:

```bash
ruff check server/app.py server/config.py server/api/__init__.py server/api/provider_ollama.py
pytest
```

Text inference is Ollama-only, with Blip2 used for image processing.

### Current deployment

Testing


### Original deployment

Ubuntu 22.04.1 LTS  
AMD EPYC 7713 64-Core Processor  
Linode Akamai Cloud  


### Useful MongoDB commands
```
$ mongosh
$ use my_database
$ show collections
# Inspect dataset by name
$ db.dataset.find({"name": "set_1"})
# Count datasets
$ db.dataset.countDocuments()
```

