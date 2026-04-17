#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SERVER_DIR="${ROOT_DIR}/server"
VENV_DIR="${SERVER_DIR}/venv"
REQUIREMENTS_FILE="${SERVER_DIR}/requirements.txt"

if ! command -v uv >/dev/null 2>&1; then
    echo "Error: uv is required to set up the server environment." >&2
    echo "Install it with your package manager or use environment.yml to provision it." >&2
    exit 1
fi

if [ ! -d "${VENV_DIR}" ]; then
    echo "Creating server virtual environment with uv."
    uv venv "${VENV_DIR}"
fi

echo "Installing server dependencies with uv."
uv pip install --python "${VENV_DIR}/bin/python" -r "${REQUIREMENTS_FILE}"
