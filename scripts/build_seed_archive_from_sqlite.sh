#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

TEMP_CONTAINER="tanc-seed-build-mongo"
TEMP_PORT="27019"
TEMP_VOLUME="tanc_seed_build_data"
SEED_ARCHIVE="${ROOT_DIR}/server/db/tanc_database.archive.gz"

echo "[seed-build] Starting one-time seed build from server/db/db.sqlite"

# Clean previous temp resources if any.
docker rm -f "${TEMP_CONTAINER}" >/dev/null 2>&1 || true
docker volume rm "${TEMP_VOLUME}" >/dev/null 2>&1 || true

# Start temporary MongoDB used only for building the archive.
docker run -d --name "${TEMP_CONTAINER}" -p "${TEMP_PORT}:27017" -v "${TEMP_VOLUME}:/data/db" mongo:7 --bind_ip_all >/dev/null

cleanup() {
  docker rm -f "${TEMP_CONTAINER}" >/dev/null 2>&1 || true
  docker volume rm "${TEMP_VOLUME}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "[seed-build] Waiting for temporary MongoDB..."
for i in $(seq 1 120); do
  if mongosh "mongodb://127.0.0.1:${TEMP_PORT}/admin" --quiet --eval "db.runCommand({ ping: 1 }).ok" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

cd "${ROOT_DIR}"
source "${ROOT_DIR}/venv/bin/activate"

echo "[seed-build] Exporting SQLite -> JSON"
python3 scripts/export_sqlite_to_json.py

echo "[seed-build] Importing JSON -> temporary MongoDB"
python3 scripts/migrate_sqlite_to_mongodb.py --yes --reset-existing --mongodb-uri "mongodb://127.0.0.1:${TEMP_PORT}"

echo "[seed-build] Creating seed archive ${SEED_ARCHIVE}"
docker run --rm --network host -v "${ROOT_DIR}/server/db:/seed" mongo:7 \
  sh -lc "mongodump --uri='mongodb://127.0.0.1:${TEMP_PORT}/tanc_database' --archive=/seed/tanc_database.archive.gz --gzip --quiet"

echo "[seed-build] Seed archive ready: ${SEED_ARCHIVE}"
echo "[seed-build] Done."