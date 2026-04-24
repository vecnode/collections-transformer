# Collections Transformer

Minimal agent-based platform for multimodal LLM analysis of datasets in the GLAM sector.


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

# 8) Local API tests (with backend + frontend running)
uv run tests/local/test_health.py
uv run tests/local/test_user_login.py

uv run tests/local/test_upload_csv_text.py --mode single
uv run tests/local/test_upload_csv_text.py --mode chunked

uv run tests/local/test_inference_img_1.py --mode caption # BLIP2 (img short-description)
uv run tests/local/test_inference_img_1.py --mode long-description # BLIP2 (img long-description)
uv run tests/local/test_inference_ocr_1.py --image assets/test_img_2.png # GLM-OCR TrOCR (img text-detection)

uv run tests/local/test_inference_txt_1.py --text assets/test_txt_1.txt # gemma3:27b (txt summarise, 3 sentences)
uv run tests/local/test_inference_txt_2.py --text assets/test_txt_1.txt # gemma3:27b (txt topic, single sentence)

uv run tests/local/test_embed_classifier_1.py # sentence-transformers/all-MiniLM-L6-v2 (txt classification, embedding)
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
- Local: `.env.local.template` — localhost datastores, MongoDB required, Redis optional, `NEXT_PUBLIC_SERVER_URL=http://localhost:8080`
- Docker: `.env.docker.template` — container DNS, `NEXT_PUBLIC_SERVER_URL=http://localhost`, `OLLAMA_BASE_URL=http://host.docker.internal:11434`

For Docker, `OLLAMA_BASE_URL` must be reachable from containers.

Model configuration:
- Text inference: Ollama (`OLLAMA_BASE_URL`, `OLLAMA_MODEL_OPTION`)
- Image inference: Blip2 (`BLIP2_MODEL_NAME`, default: `Salesforce/blip2-opt-2.7b`)
- OCR inference: GLM-OCR (`TROCR_MODEL_NAME`, default: `zai-org/GLM-OCR`)
- Text embedding/classification: Sentence Transformers (`EMBED_MODEL_NAME`, default: `sentence-transformers/all-MiniLM-L6-v2`)


