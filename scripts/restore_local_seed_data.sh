#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
SEED_ARCHIVE="${ROOT_DIR}/server/db/tanc_database.archive.gz"
FORCE_RESTORE="false"

if [ "${1:-}" = "--force" ]; then
    FORCE_RESTORE="true"
fi

if [ -f "${ENV_FILE}" ]; then
    set -a
    # shellcheck disable=SC1090
    source "${ENV_FILE}"
    set +a
fi

MONGODB_URI_VALUE="${MONGODB_URI:-mongodb://127.0.0.1:27017}"
MONGODB_DATABASE_VALUE="${MONGODB_DATABASE:-tanc_database}"

if [[ ! -f "${SEED_ARCHIVE}" ]]; then
    echo "Seed archive not found at ${SEED_ARCHIVE}." >&2
    exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "Docker is required for seed restore because this helper uses mongo:7 tools." >&2
    exit 1
fi

"${SCRIPT_DIR}/ensure_mongodb.sh"

run_mongosh() {
    mongosh "${MONGODB_URI_VALUE}/${MONGODB_DATABASE_VALUE}" --quiet --eval "$1"
}

dataset_count="$(run_mongosh 'db.dataset.countDocuments()' 2>/dev/null || echo 0)"
item_count="$(run_mongosh 'db.item.countDocuments()' 2>/dev/null || echo 0)"
labelset_count="$(run_mongosh 'db.labelset.countDocuments()' 2>/dev/null || echo 0)"
agent_count="$(run_mongosh 'db.agent.countDocuments()' 2>/dev/null || echo 0)"

if [ "${FORCE_RESTORE}" != "true" ] && { [ "${dataset_count}" != "0" ] || [ "${item_count}" != "0" ] || [ "${labelset_count}" != "0" ] || [ "${agent_count}" != "0" ]; }; then
    echo "Local MongoDB already has data:" >&2
    echo "dataset=${dataset_count} item=${item_count} labelset=${labelset_count} agent=${agent_count}" >&2
    echo "Re-run with --force to replace it from ${SEED_ARCHIVE}." >&2
    exit 0
fi

echo "Restoring bundled seed data into ${MONGODB_DATABASE_VALUE}..."
docker run --rm --network host \
    -v "${ROOT_DIR}/server/db:/seed:ro" \
    mongo:7 \
    sh -lc "mongorestore --uri='${MONGODB_URI_VALUE}' --archive=/seed/tanc_database.archive.gz --gzip --nsInclude '${MONGODB_DATABASE_VALUE}.*' --drop"

restored_dataset_count="$(run_mongosh 'db.dataset.countDocuments()' 2>/dev/null || echo 0)"
restored_item_count="$(run_mongosh 'db.item.countDocuments()' 2>/dev/null || echo 0)"
restored_labelset_count="$(run_mongosh 'db.labelset.countDocuments()' 2>/dev/null || echo 0)"
restored_agent_count="$(run_mongosh 'db.agent.countDocuments()' 2>/dev/null || echo 0)"

echo "Seed restore complete: dataset=${restored_dataset_count} item=${restored_item_count} labelset=${restored_labelset_count} agent=${restored_agent_count}"