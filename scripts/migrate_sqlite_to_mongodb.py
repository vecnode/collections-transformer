#!/usr/bin/env python3
"""SQLite/JSON to MongoDB migration utilities."""

from __future__ import annotations

import argparse
import json
import traceback
from datetime import datetime
from pathlib import Path

from bson.objectid import ObjectId
from pymongo import InsertOne, MongoClient

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_DIR = ROOT_DIR / "server" / "db"

MONGODB_URI = "mongodb://127.0.0.1:27017"
DATABASE_NAME = "tanc_database"
JSON_DIR = DB_DIR / "sqlite2json"
BACKUP_DIR = DB_DIR / "migration_backups"

COLLECTION_MAPPINGS = {
    "classifier": "classifier",
    "dataset": "dataset",
    "category": "category",
    "artwork": "artwork",
    "text_label": "text_label",
    "sentence": "sentence",
    "sentence_label": "sentence_label",
    "constituent": "constituent",
    "constituent_label": "constituent_label",
}


class MigrationError(Exception):
    """Custom exception for migration errors."""


class MigrationManager:
    def __init__(self) -> None:
        self.client: MongoClient | None = None
        self.db = None
        self.backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_path = BACKUP_DIR / self.backup_timestamp
        self.errors: list[str] = []
        self.stats = {
            "collections_imported": 0,
            "documents_imported": 0,
            "references_updated": 0,
            "items_created": 0,
            "labels_created": 0,
            "labelsets_created": 0,
        }

    def connect(self, mongodb_uri: str = MONGODB_URI, database_name: str = DATABASE_NAME) -> None:
        try:
            self.client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            self.client.admin.command("ping")
            self.db = self.client[database_name]
            print(f"Connected to MongoDB database: {database_name}")
        except Exception as exc:
            raise MigrationError(f"Failed to connect to MongoDB: {exc}") from exc

    def create_backup(self) -> None:
        try:
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            self.backup_path.mkdir(parents=True, exist_ok=True)

            collections = self.db.list_collection_names()
            if not collections:
                return

            for collection_name in collections:
                collection = self.db[collection_name]
                count = collection.count_documents({})
                if count == 0:
                    continue

                backup_file = self.backup_path / f"{collection_name}.json"
                documents = list(collection.find({}))
                for doc in documents:
                    if "_id" in doc:
                        doc["_id"] = str(doc["_id"])
                    for key, value in doc.items():
                        if isinstance(value, ObjectId):
                            doc[key] = str(value)

                with backup_file.open("w", encoding="utf-8") as f:
                    json.dump(documents, f, indent=2, default=str)
        except Exception as exc:
            raise MigrationError(f"Backup failed: {exc}") from exc

    def validate_json_files(self) -> None:
        if not JSON_DIR.exists():
            raise MigrationError(f"JSON directory not found: {JSON_DIR}")

        invalid_files: list[str] = []
        for collection_name in COLLECTION_MAPPINGS:
            json_file = JSON_DIR / f"{collection_name}.json"
            if not json_file.exists():
                continue
            try:
                with json_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        invalid_files.append(f"{collection_name}.json")
            except Exception:
                invalid_files.append(f"{collection_name}.json")

        if invalid_files:
            raise MigrationError(f"Invalid JSON files: {', '.join(invalid_files)}")

    def reset_target_collections(self) -> None:
        targets = list(COLLECTION_MAPPINGS.values()) + ["item", "label", "labelset"]
        for name in targets:
            self.db[name].drop()
        print("Reset target collections before migration")

    def import_collections(self) -> None:
        for collection_name, target_collection in COLLECTION_MAPPINGS.items():
            json_file = JSON_DIR / f"{collection_name}.json"
            if not json_file.exists():
                continue

            collection = self.db[target_collection]
            existing_count = collection.count_documents({})
            if existing_count > 0:
                continue

            with json_file.open("r", encoding="utf-8") as f:
                json_data = json.load(f)

            operations = [
                InsertOne({k: v for k, v in doc.items() if v is not None or k == "id"})
                for doc in json_data
            ]
            if not operations:
                continue

            result = collection.bulk_write(operations, ordered=False)
            self.stats["documents_imported"] += result.inserted_count
            self.stats["collections_imported"] += 1

    def create_indexes(self) -> None:
        """Create indexes on id fields to speed up lookups during reference updates."""
        try:
            collections_to_index = ["classifier", "dataset", "category", "artwork", "text_label"]
            for collection_name in collections_to_index:
                collection = self.db[collection_name]
                if collection.count_documents({}) == 0:
                    continue
                try:
                    collection.create_index("id", unique=False, background=False)
                    print(f"Created index on {collection_name}.id")
                except Exception:
                    # Index may already exist, which is fine
                    pass
        except Exception as exc:
            print(f"Warning: Could not create indexes: {exc}")

    def create_refactor_indexes(self) -> None:
        """Create indexes used by refactor_collections duplicate checks and joins."""
        try:
            self.db["artwork"].create_index("dataset_id", background=False)
            self.db["artwork"].create_index("old_dataset_id", background=False)
            self.db["item"].create_index("old_item_id", background=False)
            self.db["label"].create_index(
                [
                    ("dataset_id", 1),
                    ("item_id", 1),
                    ("analyser_id", 1),
                    ("content_position", 1),
                ],
                background=False,
            )
        except Exception as exc:
            print(f"Warning: Could not create refactor indexes: {exc}")

    def update_references(self) -> None:
        try:
            category_collection = self.db["category"]
            analyser_collection = self.db["classifier"]
            dataset_collection = self.db["dataset"]
            item_collection = self.db["artwork"]
            text_label_collection = self.db["text_label"]

            rename_obj = {
                "dataset_id": "old_dataset_id",
                "category_id": "old_category_id",
                "artwork_id": "old_artwork_id",
                "sentence_id": "old_sentence_id",
                "classifier_id": "old_classifier_id",
                "constituent_id": "old_constituent_id",
            }

            for collection_name in ["classifier", "dataset", "category", "artwork", "text_label"]:
                collection = self.db[collection_name]
                for old_field, new_field in rename_obj.items():
                    result = collection.update_many(
                        {old_field: {"$exists": True}},
                        {"$rename": {old_field: new_field}},
                    )
                    self.stats["references_updated"] += result.modified_count

            for analyser in list(analyser_collection.find({})):
                if "old_dataset_id" not in analyser or "old_category_id" not in analyser:
                    continue
                dataset = dataset_collection.find_one({"id": analyser["old_dataset_id"]})
                category = category_collection.find_one({"id": analyser["old_category_id"]})
                if dataset and category:
                    analyser_collection.update_one(
                        {"id": analyser["id"]},
                        {"$set": {"dataset_id": dataset["_id"], "category_id": category["_id"]}},
                    )

            for item in list(item_collection.find({})):
                if "old_dataset_id" not in item:
                    continue
                dataset = dataset_collection.find_one({"id": item["old_dataset_id"]})
                if not dataset:
                    continue
                analyser_id = None
                if "old_classifier_id" in item and item["old_classifier_id"]:
                    analyser = analyser_collection.find_one({"id": item["old_classifier_id"]})
                    if analyser:
                        analyser_id = analyser["_id"]
                item_collection.update_one(
                    {"id": item["id"]} if "id" in item else {"_id": item["_id"]},
                    {"$set": {"dataset_id": dataset["_id"], "analyser_id": analyser_id}},
                )

            for label in list(text_label_collection.find({})):
                if "old_artwork_id" not in label:
                    continue
                item = item_collection.find_one({"id": label["old_artwork_id"]})
                if not item:
                    continue
                analyser_id = None
                if "old_classifier_id" in label and label["old_classifier_id"]:
                    analyser = analyser_collection.find_one({"id": label["old_classifier_id"]})
                    if analyser:
                        analyser_id = analyser["_id"]
                text_label_collection.update_one(
                    {"id": label["id"]},
                    {
                        "$set": {
                            "item_id": item["_id"],
                            "artwork_id": item["_id"],
                            "analyser_id": analyser_id,
                        }
                    },
                )

            for collection_name in ["artwork", "text_label"]:
                collection = self.db[collection_name]
                collection.update_many(
                    {"id": {"$exists": True}},
                    {"$rename": {"id": "position"}},
                )
        except Exception as exc:
            raise MigrationError(f"Error updating references: {exc}") from exc

    def refactor_collections(self) -> None:
        try:
            self.create_refactor_indexes()

            dataset_collection = self.db["dataset"]
            analyser_collection = self.db["classifier"]
            old_item_collection = self.db["artwork"]
            new_item_collection = self.db["item"]
            text_label_collection = self.db["text_label"]
            label_collection = self.db["label"]
            labelset_collection = self.db["labelset"]

            datasets = list(dataset_collection.find({}))
            total_items = 0
            for dataset in datasets:
                # Handle both migrated ObjectId refs and legacy integer refs.
                items = list(
                    old_item_collection.find(
                        {
                            "$or": [
                                {"dataset_id": dataset["_id"]},
                                {"old_dataset_id": dataset.get("id")},
                            ]
                        }
                    )
                )
                new_items = []
                for old_item in items:
                    if new_item_collection.find_one({"old_item_id": old_item["_id"]}):
                        continue
                    new_items.append(
                        {
                            "dataset_id": dataset["_id"],
                            "old_item_id": old_item["_id"],
                            "position": old_item.get("position", old_item.get("id", 0)),
                            "content": [
                                {
                                    "content_type": "text",
                                    "content_value": {
                                        "text": old_item.get("text", ""),
                                        "embedding_id": None,
                                    },
                                    "subcontent": None,
                                }
                            ],
                        }
                    )
                if new_items:
                    result = new_item_collection.insert_many(new_items)
                    total_items += len(result.inserted_ids)
            self.stats["items_created"] = total_items

            total_labels = 0
            for text_label in list(text_label_collection.find({})):
                item = new_item_collection.find_one({"old_item_id": text_label.get("item_id")})
                if not item and "artwork_id" in text_label:
                    item = new_item_collection.find_one({"old_item_id": text_label["artwork_id"]})
                if not item:
                    continue

                exists = label_collection.find_one(
                    {
                        "dataset_id": item["dataset_id"],
                        "item_id": item["_id"],
                        "analyser_id": text_label.get("analyser_id"),
                        "content_position": text_label.get("position", 0),
                    }
                )
                if exists:
                    continue

                label_collection.insert_one(
                    {
                        "dataset_id": item["dataset_id"],
                        "item_id": item["_id"],
                        "analyser_id": text_label.get("analyser_id"),
                        "type": "binary",
                        "content_level": "content",
                        "content_ref": str(text_label.get("item_id")),
                        "content_position": text_label.get("position", 0),
                        "content_type": "text",
                        "value": text_label.get("value", 0),
                        "rationale": "",
                    }
                )
                total_labels += 1
            self.stats["labels_created"] = total_labels

            labelsets_created = 0
            for analyser in list(analyser_collection.find({})):
                labels = list(label_collection.find({"analyser_id": analyser["_id"]}))
                if not labels:
                    continue
                existing = labelset_collection.find_one({"analyser_id": analyser["_id"]})
                if existing:
                    continue
                labelset_id = labelset_collection.insert_one(
                    {
                        "name": f"Analyser {analyser.get('name', 'Unknown')} - Labelset",
                        "label_type": "binary",
                        "analyser_id": analyser["_id"],
                        "dataset_id": labels[0].get("dataset_id", analyser.get("dataset_id")),
                        "origin": "user",
                    }
                ).inserted_id
                label_collection.update_many(
                    {"analyser_id": analyser["_id"]},
                    {"$set": {"labelset_id": labelset_id}},
                )
                labelsets_created += 1

            for dataset in datasets:
                labels = list(
                    label_collection.find(
                        {
                            "dataset_id": dataset["_id"],
                            "$or": [
                                {"analyser_id": None},
                                {"analyser_id": {"$exists": False}},
                            ],
                        }
                    )
                )
                if not labels:
                    continue
                existing = labelset_collection.find_one(
                    {
                        "dataset_id": dataset["_id"],
                        "$or": [
                            {"analyser_id": None},
                            {"analyser_id": {"$exists": False}},
                        ],
                    }
                )
                if existing:
                    continue

                labelset_id = labelset_collection.insert_one(
                    {
                        "name": f"Dataset {dataset.get('name', 'Unknown')} - Labelset",
                        "label_type": "binary",
                        "dataset_id": dataset["_id"],
                        "analyser_id": None,
                        "origin": "user",
                    }
                ).inserted_id
                label_collection.update_many(
                    {
                        "dataset_id": dataset["_id"],
                        "$or": [
                            {"analyser_id": None},
                            {"analyser_id": {"$exists": False}},
                        ],
                    },
                    {"$set": {"labelset_id": labelset_id}},
                )
                labelsets_created += 1

            self.stats["labelsets_created"] = labelsets_created
        except Exception as exc:
            raise MigrationError(f"Error refactoring collections: {exc}") from exc

    def verify_migration(self) -> bool:
        collections_to_check = ["dataset", "classifier", "item", "label", "labelset"]
        counts = {name: self.db[name].count_documents({}) for name in collections_to_check}
        print("Verification counts:", counts)
        return counts["dataset"] > 0 and counts["item"] > 0

    def print_summary(self) -> None:
        print("Migration summary:")
        for key, value in self.stats.items():
            print(f"  {key}: {value}")
        print(f"  backup: {self.backup_path}")
        if self.errors:
            for err in self.errors:
                print(f"  error: {err}")

    def close(self) -> None:
        if self.client:
            self.client.close()


def run_migration(
    *,
    auto_confirm: bool = False,
    mongodb_uri: str = MONGODB_URI,
    reset_existing: bool = False,
) -> int:
    manager = MigrationManager()
    try:
        manager.connect(mongodb_uri=mongodb_uri)
        if not auto_confirm:
            response = input("Proceed with migration? (yes/no): ").strip().lower()
            if response != "yes":
                print("Migration cancelled")
                return 1

        manager.create_backup()
        manager.validate_json_files()
        if reset_existing:
            manager.reset_target_collections()
        manager.import_collections()
        manager.create_indexes()
        manager.update_references()
        manager.refactor_collections()
        manager.verify_migration()
        manager.print_summary()
        return 0
    except MigrationError as exc:
        print(f"Migration error: {exc}")
        return 1
    except KeyboardInterrupt:
        print("Interrupted by user")
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Unexpected error: {exc}")
        traceback.print_exc()
        return 1
    finally:
        manager.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--yes", action="store_true", help="Run without interactive confirmation")
    parser.add_argument("--mongodb-uri", default=MONGODB_URI)
    parser.add_argument(
        "--reset-existing",
        action="store_true",
        help="Drop target collections before importing (backup is created first)",
    )
    args = parser.parse_args()
    return run_migration(
        auto_confirm=args.yes,
        mongodb_uri=args.mongodb_uri,
        reset_existing=args.reset_existing,
    )


if __name__ == "__main__":
    raise SystemExit(main())