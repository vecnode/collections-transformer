#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SERVER_DIR="${ROOT_DIR}/server"

"${SCRIPT_DIR}/create_server_env.sh"

cd "${SERVER_DIR}"
source "${ROOT_DIR}/venv/bin/activate"

# Run with Gunicorn in production mode
# Using gevent workers for async support
gunicorn \
  --worker-class gevent \
  --workers 4 \
  --worker-connections 1000 \
  --bind 0.0.0.0:8080 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  'api:create_app()'
