#!/usr/bin/env python3
"""Relink Mongo item image references to existing GridFS files.

This script repairs migrated data where item content contains image filenames
(e.g. "10.jpg") but lacks content_value.image_storage_id.

It does not import new files. It only links items to files already present in
fs.files/fs.chunks.
"""

from __future__ import annotations

import argparse
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_ENV_FILE = ROOT_DIR / ".env"
IMAGE_RE = re.compile(r"\.(jpg|jpeg|png|gif|webp|svg)$", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Relink item image filenames to existing GridFS file IDs"
    )
    parser.add_argument(
        "--mongo-uri",
        default=None,
        help="MongoDB URI (defaults to MONGODB_URI from .env)",
    )
    parser.add_argument(
        "--database",
        default=None,
        help="MongoDB database name (defaults to MONGODB_DATABASE from .env)",
    )
    parser.add_argument(
        "--dataset-object-id",
        action="append",
        dest="dataset_object_ids",
        help="Mongo dataset ObjectId to process (repeatable)",
    )
    parser.add_argument(
        "--dataset-legacy-id",
        type=int,
        action="append",
        dest="dataset_legacy_ids",
        help="Legacy dataset id field value to process (repeatable)",
    )
    parser.add_argument(
        "--candidate-index",
        type=int,
        default=0,
        help=(
            "Which fs.files candidate to use when a filename appears multiple times "
            "(sorted by uploadDate desc, then _id desc). 0 = newest"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report planned updates without writing",
    )
    return parser.parse_args()


def resolve_mongo_settings(args: argparse.Namespace) -> tuple[str, str]:
    load_dotenv(DEFAULT_ENV_FILE)
    mongo_uri = args.mongo_uri or os.getenv("MONGODB_URI") or "mongodb://127.0.0.1:27017"
    database = args.database or os.getenv("MONGODB_DATABASE") or "tanc_database"
    return mongo_uri, database


def get_target_dataset_ids(db: Any, args: argparse.Namespace) -> list[ObjectId]:
    ids: list[ObjectId] = []

    if args.dataset_object_ids:
        for oid in args.dataset_object_ids:
            ids.append(ObjectId(oid))

    if args.dataset_legacy_ids:
        for legacy_id in args.dataset_legacy_ids:
            dataset = db["dataset"].find_one({"id": legacy_id}, {"_id": 1})
            if not dataset:
                raise RuntimeError(f"No dataset found with legacy id={legacy_id}")
            ids.append(dataset["_id"])

    if ids:
        return list(dict.fromkeys(ids))

    # Auto-discover datasets with items that look like image filenames and no linkage.
    pipeline = [
        {
            "$match": {
                "content.content_value.image_storage_id": {"$exists": False},
                "content.content_value.text": {"$type": "string"},
            }
        },
        {"$unwind": "$content"},
        {
            "$match": {
                "content.content_value.image_storage_id": {"$exists": False},
                "content.content_value.text": {"$regex": "\\.(jpg|jpeg|png|gif|webp|svg)$", "$options": "i"},
            }
        },
        {"$group": {"_id": "$dataset_id"}},
    ]
    return [row["_id"] for row in db["item"].aggregate(pipeline)]


def extract_filename_and_index(item: dict[str, Any]) -> tuple[str | None, int | None]:
    content = item.get("content")
    if not isinstance(content, list):
        return None, None

    for idx, entry in enumerate(content):
        if not isinstance(entry, dict):
            continue
        content_value = entry.get("content_value")
        if not isinstance(content_value, dict):
            continue

        # Skip entries that are already linked.
        if content_value.get("image_storage_id"):
            continue

        text_value = content_value.get("text")
        url_value = content_value.get("url")
        candidate = text_value if isinstance(text_value, str) else (url_value if isinstance(url_value, str) else None)
        if candidate and IMAGE_RE.search(candidate.strip()):
            return candidate.strip(), idx

    return None, None


def build_file_map(db: Any, filenames: set[str], candidate_index: int) -> tuple[dict[str, ObjectId], dict[str, int]]:
    chosen: dict[str, ObjectId] = {}
    counts: dict[str, int] = {}

    if not filenames:
        return chosen, counts

    cursor = db["fs.files"].find(
        {"filename": {"$in": list(filenames)}},
        {"filename": 1, "uploadDate": 1},
    ).sort([("uploadDate", -1), ("_id", -1)])

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for doc in cursor:
        grouped[doc["filename"]].append(doc)

    for filename, docs in grouped.items():
        counts[filename] = len(docs)
        if len(docs) > candidate_index:
            chosen[filename] = docs[candidate_index]["_id"]

    for filename in filenames:
        counts.setdefault(filename, 0)

    return chosen, counts


def relink_dataset(db: Any, dataset_id: ObjectId, candidate_index: int, dry_run: bool) -> dict[str, int]:
    summary = {
        "items_scanned": 0,
        "items_eligible": 0,
        "items_updated": 0,
        "missing_files": 0,
        "ambiguous_filenames": 0,
    }

    items = list(
        db["item"].find(
            {"dataset_id": dataset_id},
            {"content": 1, "position": 1},
        )
    )
    summary["items_scanned"] = len(items)

    filename_to_items: dict[str, list[tuple[ObjectId, int]]] = defaultdict(list)
    for item in items:
        filename, content_idx = extract_filename_and_index(item)
        if filename is None or content_idx is None:
            continue
        summary["items_eligible"] += 1
        filename_to_items[filename].append((item["_id"], content_idx))

    file_map, file_counts = build_file_map(db, set(filename_to_items.keys()), candidate_index)

    for filename, item_refs in filename_to_items.items():
        candidate_count = file_counts.get(filename, 0)
        if candidate_count == 0:
            summary["missing_files"] += len(item_refs)
            continue
        if candidate_count > 1:
            summary["ambiguous_filenames"] += len(item_refs)

        fs_id = file_map.get(filename)
        if not fs_id:
            summary["missing_files"] += len(item_refs)
            continue

        for item_id, content_idx in item_refs:
            if dry_run:
                summary["items_updated"] += 1
                continue

            db["item"].update_one(
                {"_id": item_id},
                {
                    "$set": {
                        f"content.{content_idx}.content_type": "image",
                        f"content.{content_idx}.content_value.image_storage_id": fs_id,
                        f"content.{content_idx}.content_value.text": filename,
                        f"content.{content_idx}.content_value.embedding_ids": [],
                    },
                    "$unset": {
                        f"content.{content_idx}.content_value.embedding_id": "",
                    },
                },
            )
            summary["items_updated"] += 1

    return summary


def main() -> int:
    args = parse_args()
    if args.candidate_index < 0:
        raise SystemExit("--candidate-index must be >= 0")

    mongo_uri, database_name = resolve_mongo_settings(args)
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    db = client[database_name]

    try:
        dataset_ids = get_target_dataset_ids(db, args)
        if not dataset_ids:
            print("No datasets with filename-only image references found")
            return 0

        print(f"Using MongoDB: {mongo_uri}/{database_name}")
        print(f"Datasets to process: {len(dataset_ids)}")
        print(f"Candidate index: {args.candidate_index} (0=newest)")
        if args.dry_run:
            print("Dry run enabled; no writes will be performed")

        totals = defaultdict(int)
        for dataset_id in dataset_ids:
            summary = relink_dataset(
                db=db,
                dataset_id=dataset_id,
                candidate_index=args.candidate_index,
                dry_run=args.dry_run,
            )
            print(f"Dataset {dataset_id}: {dict(summary)}")
            for key, value in summary.items():
                totals[key] += value

        print(f"Total: {dict(totals)}")
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
