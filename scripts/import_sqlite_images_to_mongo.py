#!/usr/bin/env python3
"""Backfill Mongo item images from a local image folder.

This script is intended for migrated datasets where Mongo `item` documents only
contain filename strings like `0.jpg` instead of the current image structure
with `content_type=image` and `image_storage_id`.

It updates existing Mongo `item` documents in place by:
1. Matching items to image files by filename
2. Writing image bytes into GridFS
3. Replacing the item content with the current image content schema

Example:
  /home/luisarandas/Desktop/collections-transformer/venv/bin/python \
    scripts/import_sqlite_images_to_mongo.py \
    --dataset-id 42 \
    --image-dir /path/to/images
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import gridfs
from dotenv import load_dotenv
from pymongo import MongoClient


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SQLITE_FILE = ROOT_DIR / "server" / "db" / "db.sqlite"
DEFAULT_ENV_FILE = ROOT_DIR / ".env"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import image files into existing Mongo item documents",
    )
    parser.add_argument(
        "--sqlite-file",
        type=Path,
        default=DEFAULT_SQLITE_FILE,
        help="Path to the source SQLite file",
    )
    parser.add_argument(
        "--image-dir",
        type=Path,
        required=True,
        help="Directory containing the source image files",
    )
    parser.add_argument(
        "--dataset-id",
        type=int,
        action="append",
        dest="dataset_ids",
        help="Legacy SQLite dataset id to backfill. Repeat to process multiple datasets.",
    )
    parser.add_argument(
        "--mongo-uri",
        default=None,
        help="MongoDB URI. Defaults to MONGODB_URI from .env or mongodb://127.0.0.1:27017",
    )
    parser.add_argument(
        "--database",
        default=None,
        help="MongoDB database name. Defaults to MONGODB_DATABASE from .env or tanc_database",
    )
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Replace existing image_storage_id values instead of skipping them",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be updated without writing to MongoDB",
    )
    return parser.parse_args()


def is_image_filename(value: str | None) -> bool:
    return isinstance(value, str) and Path(value).suffix.lower() in IMAGE_SUFFIXES


def resolve_mongo_settings(args: argparse.Namespace) -> tuple[str, str]:
    load_dotenv(DEFAULT_ENV_FILE)
    mongo_uri = args.mongo_uri or os.getenv("MONGODB_URI") or "mongodb://127.0.0.1:27017"
    database = args.database or os.getenv("MONGODB_DATABASE") or "tanc_database"
    return mongo_uri, database


def build_image_index(image_dir: Path) -> dict[str, list[Path]]:
    image_index: dict[str, list[Path]] = defaultdict(list)
    for path in image_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
            image_index[path.name].append(path)
    return image_index


def get_target_dataset_ids(conn: sqlite3.Connection, requested_ids: list[int] | None) -> list[int]:
    cursor = conn.cursor()
    if requested_ids:
        return requested_ids

    rows = cursor.execute("SELECT DISTINCT dataset_id, text FROM artwork").fetchall()
    dataset_ids: set[int] = set()
    for dataset_id, text in rows:
        if is_image_filename(text):
            dataset_ids.add(int(dataset_id))
    return sorted(dataset_ids)


def get_sqlite_filenames(conn: sqlite3.Connection, dataset_id: int) -> list[str]:
    cursor = conn.cursor()
    rows = cursor.execute(
        "SELECT text FROM artwork WHERE dataset_id = ? ORDER BY id",
        (dataset_id,),
    ).fetchall()
    return [row[0] for row in rows if is_image_filename(row[0])]


def extract_item_filename(item: dict[str, Any]) -> str | None:
    content = item.get("content") or []
    if not isinstance(content, list):
        return None

    for entry in content:
        if not isinstance(entry, dict):
            continue
        content_value = entry.get("content_value") or {}
        text_value = content_value.get("text")
        url_value = content_value.get("url")
        candidate = text_value if isinstance(text_value, str) else url_value
        if is_image_filename(candidate):
            return candidate
    return None


def import_dataset_images(
    db: Any,
    fs: gridfs.GridFS,
    conn: sqlite3.Connection,
    image_index: dict[str, list[Path]],
    dataset_id: int,
    replace_existing: bool,
    dry_run: bool,
) -> dict[str, int]:
    summary = {
        "matched": 0,
        "updated": 0,
        "skipped_existing": 0,
        "missing_files": 0,
        "ambiguous_files": 0,
        "missing_items": 0,
    }

    dataset = db["dataset"].find_one({"id": dataset_id})
    if not dataset:
        raise RuntimeError(f"Mongo dataset with id={dataset_id} was not found")

    items = list(db["item"].find({"dataset_id": dataset["_id"]}))
    items_by_filename: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        filename = extract_item_filename(item)
        if filename:
            items_by_filename[filename].append(item)

    stored_file_ids: dict[Path, Any] = {}
    filenames = get_sqlite_filenames(conn, dataset_id)

    for filename in filenames:
        matching_items = items_by_filename.get(filename, [])
        if not matching_items:
            summary["missing_items"] += 1
            continue

        matching_paths = image_index.get(filename, [])
        if not matching_paths:
            summary["missing_files"] += len(matching_items)
            continue
        if len(matching_paths) > 1:
            summary["ambiguous_files"] += len(matching_items)
            continue

        image_path = matching_paths[0]
        summary["matched"] += len(matching_items)

        for item in matching_items:
            existing_storage_id = None
            content = item.get("content") or []
            if isinstance(content, list) and content:
                content_value = content[0].get("content_value") or {}
                existing_storage_id = content_value.get("image_storage_id")

            if existing_storage_id and not replace_existing:
                summary["skipped_existing"] += 1
                continue

            if dry_run:
                summary["updated"] += 1
                continue

            if image_path not in stored_file_ids:
                with image_path.open("rb") as image_file:
                    stored_file_ids[image_path] = fs.put(image_file.read(), filename=filename)

            image_storage_id = stored_file_ids[image_path]
            db["item"].update_one(
                {"_id": item["_id"]},
                {
                    "$set": {
                        "content": [
                            {
                                "content_type": "image",
                                "content_value": {
                                    "image_storage_id": image_storage_id,
                                    "text": filename,
                                    "embedding_ids": [],
                                },
                                "subcontent": None,
                            }
                        ]
                    }
                },
            )
            summary["updated"] += 1

    if not dry_run and summary["updated"] > 0:
        db["dataset"].update_one(
            {"_id": dataset["_id"]},
            {"$set": {"dataset_type": "image"}},
        )

    return summary


def main() -> int:
    args = parse_args()

    if not args.sqlite_file.exists():
        print(f"SQLite file not found: {args.sqlite_file}", file=sys.stderr)
        return 1

    if not args.image_dir.exists():
        print(f"Image directory not found: {args.image_dir}", file=sys.stderr)
        return 1

    mongo_uri, database_name = resolve_mongo_settings(args)
    image_index = build_image_index(args.image_dir)
    if not image_index:
        print(f"No image files found under: {args.image_dir}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(args.sqlite_file)
    dataset_ids = get_target_dataset_ids(conn, args.dataset_ids)
    if not dataset_ids:
        print("No candidate datasets found in SQLite", file=sys.stderr)
        return 1

    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    db = client[database_name]
    fs = gridfs.GridFS(db)

    try:
        print(f"Using SQLite: {args.sqlite_file}")
        print(f"Using image dir: {args.image_dir}")
        print(f"Using MongoDB: {mongo_uri}/{database_name}")
        print(f"Datasets: {', '.join(str(dataset_id) for dataset_id in dataset_ids)}")
        if args.dry_run:
            print("Dry run enabled; no MongoDB writes will be performed")

        total = defaultdict(int)
        for dataset_id in dataset_ids:
            summary = import_dataset_images(
                db=db,
                fs=fs,
                conn=conn,
                image_index=image_index,
                dataset_id=dataset_id,
                replace_existing=args.replace_existing,
                dry_run=args.dry_run,
            )
            print(f"Dataset {dataset_id}: {dict(summary)}")
            for key, value in summary.items():
                total[key] += value

        print(f"Total: {dict(total)}")
        return 0
    finally:
        conn.close()
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())