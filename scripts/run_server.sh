#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SERVER_DIR="${ROOT_DIR}/server"

"${SCRIPT_DIR}/create_server_env.sh"

cd "${SERVER_DIR}"
source venv/bin/activate
exec python3 app.py
