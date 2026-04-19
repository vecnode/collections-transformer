#!/bin/bash

set -euo pipefail

MONGO_URI="${MONGO_URI:-mongodb://mongodb:27017}"
DB_NAME="${DB_NAME:-tanc_database}"
SEED_ARCHIVE="${SEED_ARCHIVE:-/seed/tanc_database.archive.gz}"

echo "[mongo-seed] Waiting for MongoDB at ${MONGO_URI}..."
for i in $(seq 1 120); do
  if mongosh "${MONGO_URI}/admin" --quiet --eval "db.runCommand({ ping: 1 }).ok" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if [[ ! -f "${SEED_ARCHIVE}" ]]; then
  echo "[mongo-seed] Seed archive not found (${SEED_ARCHIVE}). Skipping restore."
  exit 0
fi

existing_count=$(mongosh "${MONGO_URI}/${DB_NAME}" --quiet --eval "db.dataset.countDocuments()" 2>/dev/null || echo 0)
if [[ "${existing_count}" != "0" ]]; then
  echo "[mongo-seed] Database already populated (${existing_count} datasets). Skipping restore."
  exit 0
fi

echo "[mongo-seed] Restoring seed archive into ${DB_NAME}..."
mongorestore \
  --uri "${MONGO_URI}" \
  --archive="${SEED_ARCHIVE}" \
  --gzip \
  --nsInclude "${DB_NAME}.*" \
  --drop

restored_count=$(mongosh "${MONGO_URI}/${DB_NAME}" --quiet --eval "db.dataset.countDocuments()" 2>/dev/null || echo 0)
echo "[mongo-seed] Restore complete. Dataset count: ${restored_count}"