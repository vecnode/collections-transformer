#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CLIENT_DIR="${ROOT_DIR}/client"

cd "${CLIENT_DIR}"

if [ -s "$HOME/.nvm/nvm.sh" ]; then
    source "$HOME/.nvm/nvm.sh"
    nvm use >/dev/null 2>&1 || nvm install
fi

if [ ! -d node_modules ]; then
    echo "Installing client dependencies..."
    npm install
fi

exec npm run dev
