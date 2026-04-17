# Collections Transformer

Agent-based platform for multimodal LLM analysis of datasets in the GLAM sector.

Code developed in the context of the UKRI project "Transforming Collections" undertaken at UAL "Towards a National Collection (TaNC)".




## Reproduce

- Frontend requirement: Node.js >= 18.17.0 (recommended: Node 20 LTS).

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

You can also use the helper scripts from the repository root:

```bash
./scripts/create_server_env.sh
./scripts/run_server.sh
./scripts/run_client.sh
```

**Setup alternatives:**
- Use `./scripts/create_server_env.sh` to set up just the server environment
- Use `./scripts/run_server.sh` (dev mode) or `./scripts/run_server_prod.sh` (production) to start the server
- Use `./scripts/run_client.sh` to start the client
- Use `environment.yml` with conda to set up environments

- See `requirements.txt` and `client/package.json` for a full set of dependencies. 
- Authentication uses Auth0. You can use an existing Auth0 Tenant. Create `.env` files, the following keys are needed.

## Server configuration

Server settings are centralized in `server/config.py`.

1. Copy `server/.env.template` to `server/.env`.
2. Fill in the provider keys you plan to use (`OPENAI_API_KEY`, `OPENROUTER_API_KEY`, etc.).
3. Adjust runtime values only if needed (`API_PORT`, `MONGODB_URI`, `LOG_LEVEL`, `OLLAMA_BASE_URL`).

Important variables:

- `ENVIRONMENT`, `LOG_LEVEL`
- `API_HOST`, `API_PORT`, `FLASK_DEBUG`, `FLASK_RELOAD`
- `MONGODB_URI`, `MONGODB_DATABASE`
- `OPENAI_API_KEY`, `OPENAI_MODEL_OPTION`
- `OLLAMA_MODEL_OPTION`, `OLLAMA_BASE_URL`
- `BLIP2_MODEL_NAME`

```
NEXT_PUBLIC_SERVER_URL = ""
AUTH0_SECRET = "{AUTH0 SECRET}"
AUTH0_ISSUER_BASE_URL = "{YOUR TENANT URL}"
AUTH0_CLIENT_ID = "{AUTH0 CLIENT ID}"
AUTH0_CLIENT_SECRET = "{AUTH0 CLIENT SECRET}"
AUTH0_DOMAIN = "{YOUR TENANT URL}"
```

## Quality checks

The repo includes minimal Python quality tooling configuration in `pyproject.toml` and CI in `.github/workflows/server-quality.yml`.

Run locally:

```bash
ruff check server/app.py server/config.py server/api/__init__.py server/api/provider_openai.py server/api/provider_ollama.py
pytest
```

Models used for inference are gpt4-o for OpenAI API. Alter the keys on the environment files respectively. For Azure the user might add Endpoints via Azure AI Studio.

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

