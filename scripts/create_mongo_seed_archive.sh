#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SEED_DIR="${ROOT_DIR}/server/db"
SEED_ARCHIVE="${SEED_DIR}/tanc_database.archive.gz"

MONGO_URI="${MONGO_URI:-mongodb://127.0.0.1:27017/tanc_database}"

echo "Creating MongoDB seed archive..."
echo "Source URI: ${MONGO_URI}"
echo "Target file: ${SEED_ARCHIVE}"

mkdir -p "${SEED_DIR}"

# Use Mongo tools from an official container to avoid host dependency issues.
docker run --rm --network host \
  -v "${SEED_DIR}:/seed" \
  mongo:7 \
  sh -lc "mongodump --uri='${MONGO_URI}' --archive=/seed/tanc_database.archive.gz --gzip --quiet"

echo "Seed archive created successfully: ${SEED_ARCHIVE}"