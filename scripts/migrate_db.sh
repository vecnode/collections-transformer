#!/bin/bash

set -euo pipefail

# Database Migration Helper Script
# Exports SQLite to JSON and migrates to MongoDB
# Usage: ./scripts/migrate_db.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SERVER_DIR="${ROOT_DIR}/server"

echo "=============================================="
echo "Collections Transformer Database Migration"
echo "=============================================="

# Activate Python environment
echo "Activating Python environment..."
source "${ROOT_DIR}/venv/bin/activate"

cd "${SERVER_DIR}"

# Step 1: Export SQLite to JSON if db.sqlite exists and is newer
if [ -f "db/db.sqlite" ]; then
    SQLITE_FILE="db/db.sqlite"
    JSON_DIR="db/sqlite2json"
    
    echo ""
    echo "Step 1: Checking SQLite file..."
    echo "SQLite file found: $SQLITE_FILE"
    
    # Check if we need to export (SQLite is newer than JSON files)
    SHOULD_EXPORT=false
    if [ -d "$JSON_DIR" ]; then
        # Get modification times
        SQLITE_TIME=$(stat -f%m "$SQLITE_FILE" 2>/dev/null || stat -c%Y "$SQLITE_FILE" 2>/dev/null || echo 0)
        JSON_TIME=$(stat -f%m "$JSON_DIR" 2>/dev/null || stat -c%Y "$JSON_DIR" 2>/dev/null || echo 0)
        
        if [ "$SQLITE_TIME" -gt "$JSON_TIME" ]; then
            SHOULD_EXPORT=true
        fi
    else
        SHOULD_EXPORT=true
    fi
    
    if [ "$SHOULD_EXPORT" = true ]; then
        echo "  → SQLite file is newer than JSON exports, exporting..."
        python "${ROOT_DIR}/scripts/export_sqlite_to_json.py"
        echo "  ✓ SQLite exported to JSON"
    else
        echo "  ✓ Using existing JSON exports (SQLite not modified)"
    fi
else
    echo ""
    echo "Step 1: No db.sqlite file found"
    echo "  → If you have a SQLite database, place it at: server/db/db.sqlite"
    echo "  → Proceeding with existing JSON exports if available..."
fi

# Step 2: Run MongoDB migration
echo ""
echo "Step 2: Migrating data to MongoDB..."
python "${ROOT_DIR}/scripts/migrate_sqlite_to_mongodb.py" --yes --reset-existing

echo ""
echo "=============================================="
echo "✓ Migration complete!"
echo "=============================================="
