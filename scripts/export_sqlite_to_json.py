#!/usr/bin/env python3
"""Export SQLite tables to JSON files used by MongoDB migration."""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_DIR = ROOT_DIR / "server" / "db"
SQLITE_FILE = DB_DIR / "db.sqlite"
JSON_OUTPUT_DIR = DB_DIR / "sqlite2json"

TABLES_TO_EXPORT = {
    "artwork": "artwork.json",
    "category": "category.json",
    "classifier": "classifier.json",
    "constituent": "constituent.json",
    "constituent_label": "constituent_label.json",
    "dataset": "dataset.json",
    "sentence": "sentence.json",
    "sentence_label": "sentence_label.json",
    "text_label": "text_label.json",
}


def _dict_factory(cursor: sqlite3.Cursor, row: tuple[object, ...]) -> dict[str, object]:
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def export_sqlite_to_json() -> bool:
    if not SQLITE_FILE.exists():
        print(f"Error: SQLite file not found at {SQLITE_FILE}")
        return False

    print(f"Exporting SQLite database: {SQLITE_FILE}")
    JSON_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        conn = sqlite3.connect(str(SQLITE_FILE))
        conn.row_factory = _dict_factory
        cursor = conn.cursor()
        total_exported = 0

        for table_name, json_filename in TABLES_TO_EXPORT.items():
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,),
            )
            if not cursor.fetchone():
                print(f"  Skipping missing table: {table_name}")
                continue

            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()

            out_file = JSON_OUTPUT_DIR / json_filename
            with out_file.open("w", encoding="utf-8") as f:
                json.dump(rows, f, indent=2, default=_json_serializer)

            print(f"  Exported {table_name}: {len(rows)} rows")
            total_exported += len(rows)

        conn.close()
        print(f"Export complete: {total_exported} total rows")
        return True
    except sqlite3.Error as exc:
        print(f"SQLite error: {exc}")
        return False
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Unexpected error: {exc}")
        return False


def _json_serializer(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


if __name__ == "__main__":
    ok = export_sqlite_to_json()
    raise SystemExit(0 if ok else 1)