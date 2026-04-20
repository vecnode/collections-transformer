#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"

if [ -f "${ENV_FILE}" ]; then
    set -a
    # shellcheck disable=SC1090
    source "${ENV_FILE}"
    set +a
fi

MONGODB_URI_VALUE="${MONGODB_URI:-mongodb://127.0.0.1:27017}"
MONGODB_URI_NO_SCHEME="${MONGODB_URI_VALUE#mongodb://}"
MONGODB_URI_HOSTPORT="${MONGODB_URI_NO_SCHEME%%/*}"
MONGODB_HOST="${MONGODB_URI_HOSTPORT%%:*}"
MONGODB_PORT="${MONGODB_URI_HOSTPORT##*:}"
WAIT_SECONDS="${ENSURE_MONGODB_WAIT_SECONDS:-20}"

if [ -z "${MONGODB_HOST}" ] || [ -z "${MONGODB_PORT}" ]; then
    echo "Unable to parse MONGODB_URI=${MONGODB_URI_VALUE}" >&2
    exit 1
fi

is_port_open() {
    timeout 1 bash -c "cat < /dev/null > /dev/tcp/$1/$2" >/dev/null 2>&1
}

has_mongosh() {
    command -v mongosh >/dev/null 2>&1
}

can_ping_mongodb() {
    if has_mongosh; then
        mongosh "${MONGODB_URI_VALUE}" --quiet --eval "db.adminCommand({ ping: 1 }).ok" \
            >/dev/null 2>&1
        return $?
    fi

    is_port_open "${MONGODB_HOST}" "${MONGODB_PORT}"
}

wait_for_mongodb() {
    local elapsed=0

    while [ "${elapsed}" -lt "${WAIT_SECONDS}" ]; do
        if can_ping_mongodb; then
            return 0
        fi

        sleep 1
        elapsed=$((elapsed + 1))
    done

    return 1
}

print_failure_diagnostics() {
    echo "MongoDB is still not reachable at ${MONGODB_HOST}:${MONGODB_PORT}." >&2

    if command -v systemctl >/dev/null 2>&1; then
        echo "systemd state: $(systemctl is-active mongod 2>/dev/null || echo unknown)" >&2
        systemctl status mongod --no-pager -l 2>/dev/null | tail -n 12 >&2 || true
    fi

    if command -v ss >/dev/null 2>&1; then
        echo "Listening sockets on port ${MONGODB_PORT}:" >&2
        ss -ltn 2>/dev/null | grep ":${MONGODB_PORT} " >&2 || echo "none" >&2
    fi

    echo "If you prefer Docker-backed datastores for manual app development, run:" >&2
    echo "docker compose -f docker/docker-compose.yml up -d mongodb redis mongo-seed" >&2
}

if can_ping_mongodb; then
    echo "MongoDB already reachable at ${MONGODB_HOST}:${MONGODB_PORT}."
    exit 0
fi

case "${MONGODB_HOST}" in
    localhost|127.0.0.1)
        ;;
    *)
        echo "MongoDB is not reachable at ${MONGODB_HOST}:${MONGODB_PORT}." >&2
        echo "Configured URI is not local, so this helper will not try to start it automatically." >&2
        exit 1
        ;;
esac

if ! command -v systemctl >/dev/null 2>&1; then
    echo "MongoDB is not reachable at ${MONGODB_HOST}:${MONGODB_PORT}." >&2
    echo "systemctl is unavailable. Start MongoDB manually and retry." >&2
    exit 1
fi

if ! systemctl list-unit-files mongod.service >/dev/null 2>&1; then
    echo "MongoDB is not reachable at ${MONGODB_HOST}:${MONGODB_PORT}." >&2
    echo "mongod.service is not installed. Start MongoDB manually or use Docker datastores:" >&2
    echo "docker compose -f docker/docker-compose.yml up -d mongodb redis mongo-seed" >&2
    exit 1
fi

echo "Starting mongod via systemd..."
sudo systemctl start mongod

if wait_for_mongodb; then
    echo "MongoDB is now reachable at ${MONGODB_HOST}:${MONGODB_PORT}."
    exit 0
fi

print_failure_diagnostics
exit 1