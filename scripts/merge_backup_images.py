#!/usr/bin/env python3
"""
Merge image data from backup MongoDB into current tanc_database.

This script:
1. Copies GridFS files (fs.files, fs.chunks) from backup to current
2. Updates items with image_storage_id references from backup
3. Preserves all existing data in current database
4. Only adds missing image data

Usage:
    python merge_backup_images.py [--dry-run] [--backup-port 27018]
"""

import argparse
import sys
from pathlib import Path
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import datetime

# Setup paths
ROOT_DIR = Path(__file__).resolve().parent.parent
SERVER_DIR = ROOT_DIR / "server"

# MongoDB connections
BACKUP_HOST = "127.0.0.1"
BACKUP_PORT = 27018
BACKUP_DB_NAME = "tanc_database"

CURRENT_HOST = "127.0.0.1"
CURRENT_PORT = 27017
CURRENT_DB_NAME = "tanc_database"


def connect_to_db(host: str, port: int, db_name: str) -> tuple:
    """Connect to MongoDB and return both client and database."""
    client = MongoClient(f"mongodb://{host}:{port}/")
    db = client[db_name]
    return client, db


def merge_gridfs_files(backup_db, current_db, dry_run: bool = False) -> dict:
    """Copy GridFS files (images) from backup to current database.
    
    Returns statistics about the operation.
    """
    stats = {"files_copied": 0, "files_skipped": 0, "chunks_copied": 0, "errors": []}

    try:
        current_fs_files = current_db["fs.files"]
        current_fs_chunks = current_db["fs.chunks"]
        
        backup_fs_files = backup_db["fs.files"]
        backup_fs_chunks = backup_db["fs.chunks"]
        
        print("\n📁 Copying GridFS files (image data)...")
        
        # Get all file IDs from current to know what exists
        current_file_ids = set(doc["_id"] for doc in current_fs_files.find({}, {"_id": 1}))
        print(f"   Current database has {len(current_file_ids)} files")
        
        # Copy fs.files documents
        print(f"   Backup has {backup_fs_files.count_documents({})} files")
        for file_doc in backup_fs_files.find({}):
            if file_doc["_id"] not in current_file_ids:
                if not dry_run:
                    try:
                        current_fs_files.insert_one(file_doc)
                        stats["files_copied"] += 1
                    except DuplicateKeyError:
                        stats["files_skipped"] += 1
                    except Exception as e:
                        stats["errors"].append(f"Failed to copy file {file_doc.get('_id')}: {e}")
                else:
                    stats["files_copied"] += 1
            else:
                stats["files_skipped"] += 1
        
        # Copy fs.chunks documents (the actual binary data)
        print(f"   Copying associated chunks...")
        current_chunk_ids = set(doc["_id"] for doc in current_fs_chunks.find({}, {"_id": 1}))
        
        backup_chunk_count = 0
        for chunk_doc in backup_fs_chunks.find({}):
            backup_chunk_count += 1
            if chunk_doc["_id"] not in current_chunk_ids:
                if not dry_run:
                    try:
                        current_fs_chunks.insert_one(chunk_doc)
                        stats["chunks_copied"] += 1
                    except DuplicateKeyError:
                        pass
                    except Exception as e:
                        stats["errors"].append(f"Failed to copy chunk {chunk_doc.get('_id')}: {e}")
                else:
                    stats["chunks_copied"] += 1
        
        print(f"   Backup chunks: {backup_chunk_count}")
        
    except Exception as e:
        stats["errors"].append(f"GridFS copy failed: {e}")
        print(f"   ❌ Error: {e}")
    
    return stats


def extract_image_filename(item: dict) -> str:
    """Extract image filename from item's content."""
    for content in item.get("content", []):
        if content.get("content_type") == "image":
            filename = content.get("content_value", {}).get("text", "")
            if filename:
                return filename
    return None


def find_matching_items_by_filename(backup_item: dict, current_db) -> dict:
    """Find matching item in current database based on image filename.
    
    This is more reliable than position-based matching since items may have
    been re-imported with different positions/datasets.
    """
    filename = extract_image_filename(backup_item)
    if not filename:
        return None
    
    # Search for items with this filename in text content
    # The filename might be in various content types or datasets
    matching = current_db["item"].find_one({
        "$or": [
            {"content.content_value.text": filename},
            {"content.content_value.text": {"$regex": filename}},
        ]
    })
    return matching


def merge_item_images(backup_db, current_db, dry_run: bool = False) -> dict:
    """Update current items with image_storage_id from backup items.
    
    Matches items by image filename, which is more reliable across
    database migrations and re-imports.
    """
    stats = {"items_updated": 0, "items_skipped": 0, "errors": [], "items_processed": 0}
    
    print("\n🖼️  Updating items with image references...")
    
    try:
        current_items = current_db["item"]
        backup_items = backup_db["item"]
        
        # Find items in backup with images
        print("   Scanning backup for items with images...")
        image_count = 0
        updated_count = 0
        not_found_count = 0
        
        for backup_item in backup_items.find({"content.content_type": "image"}):
            image_count += 1
            stats["items_processed"] += 1
            
            # Get the image content from backup
            image_content = next(
                (c for c in backup_item.get("content", []) if c.get("content_type") == "image"),
                None
            )
            
            if not image_content:
                continue
            
            filename = image_content.get("content_value", {}).get("text", "")
            
            # Find matching item in current DB by filename
            matching_current = find_matching_items_by_filename(backup_item, current_db)
            
            if matching_current:
                # Check if current item doesn't already have this image
                has_image = any(c.get("content_type") == "image" for c in matching_current.get("content", []))
                
                if not has_image:
                    if not dry_run:
                        try:
                            # Add image content to the item
                            current_items.update_one(
                                {"_id": matching_current["_id"]},
                                {"$push": {"content": image_content}}
                            )
                            updated_count += 1
                            stats["items_updated"] += 1
                        except Exception as e:
                            stats["errors"].append(
                                f"Failed to update item {matching_current['_id']} ({filename}): {e}"
                            )
                    else:
                        updated_count += 1
                        stats["items_updated"] += 1
                else:
                    stats["items_skipped"] += 1
            else:
                not_found_count += 1
        
        print(f"   Backup items with images: {image_count}")
        print(f"   Items updated with images: {updated_count}")
        print(f"   Items skipped (already have images): {stats['items_skipped']}")
        if not_found_count > 0:
            print(f"   Items not found in current DB: {not_found_count}")
        
    except Exception as e:
        stats["errors"].append(f"Item merge failed: {e}")
        print(f"   ❌ Error: {e}")
    
    return stats


def merge_analysis_history(backup_db, current_db, dry_run: bool = False) -> dict:
    """Copy analysis_history collection from backup if current is empty."""
    stats = {"history_copied": 0, "errors": []}
    
    print("\n📊 Checking analysis_history...")
    
    try:
        current_history = current_db["analysis_history"]
        backup_history = backup_db["analysis_history"]
        
        current_count = current_history.count_documents({})
        backup_count = backup_history.count_documents({})
        
        print(f"   Current: {current_count}, Backup: {backup_count}")
        
        if current_count == 0 and backup_count > 0:
            print(f"   Copying {backup_count} analysis history records...")
            
            if not dry_run:
                try:
                    for doc in backup_history.find({}):
                        current_history.insert_one(doc)
                        stats["history_copied"] += 1
                except Exception as e:
                    stats["errors"].append(f"Failed to copy analysis_history: {e}")
            else:
                stats["history_copied"] = backup_count
                print(f"   [DRY RUN] Would copy {backup_count} records")
        
    except Exception as e:
        stats["errors"].append(f"Analysis history merge failed: {e}")
        print(f"   ❌ Error: {e}")
    
    return stats


def print_summary(all_stats: dict):
    """Print summary of merge operation."""
    print("\n" + "=" * 60)
    print("MERGE SUMMARY")
    print("=" * 60)
    
    gridfs_stats = all_stats["gridfs"]
    item_stats = all_stats["items"]
    history_stats = all_stats["history"]
    
    print(f"\n✓ GridFS Files:")
    print(f"  • Copied: {gridfs_stats['files_copied']}")
    print(f"  • Skipped (already exist): {gridfs_stats['files_skipped']}")
    print(f"  • Chunks copied: {gridfs_stats['chunks_copied']}")
    if gridfs_stats["errors"]:
        print(f"  • Errors: {len(gridfs_stats['errors'])}")
    
    print(f"\n✓ Items:")
    print(f"  • Updated with images: {item_stats['items_updated']}")
    print(f"  • Skipped (already have images): {item_stats['items_skipped']}")
    if item_stats["errors"]:
        print(f"  • Errors: {len(item_stats['errors'])}")
    
    print(f"\n✓ Analysis History:")
    print(f"  • Copied: {history_stats['history_copied']}")
    if history_stats["errors"]:
        print(f"  • Errors: {len(history_stats['errors'])}")
    
    all_errors = (gridfs_stats["errors"] + item_stats["errors"] + history_stats["errors"])
    if all_errors:
        print(f"\n⚠️  Errors ({len(all_errors)}):")
        for error in all_errors[:10]:  # Show first 10
            print(f"  • {error}")
        if len(all_errors) > 10:
            print(f"  ... and {len(all_errors) - 10} more")
    
    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Merge backup MongoDB images into current tanc_database"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--backup-port",
        type=int,
        default=27018,
        help="Port where backup MongoDB is running (default: 27018)"
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("MONGODB BACKUP IMAGE MERGE TOOL")
    print("=" * 60)
    
    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made\n")
    
    # Verify backup MongoDB is accessible
    print(f"\nConnecting to databases...")
    print(f"  • Backup:  {BACKUP_HOST}:{args.backup_port}/{BACKUP_DB_NAME}")
    print(f"  • Current: {CURRENT_HOST}:{CURRENT_PORT}/{CURRENT_DB_NAME}")
    
    try:
        backup_client, backup_db = connect_to_db(BACKUP_HOST, args.backup_port, BACKUP_DB_NAME)
        current_client, current_db = connect_to_db(CURRENT_HOST, CURRENT_PORT, CURRENT_DB_NAME)
        
        # Verify connections
        backup_db.command("ping")
        current_db.command("ping")
        print("✓ Connected to both databases")
        
    except Exception as e:
        print(f"\n❌ Failed to connect to databases: {e}")
        print("\nMake sure:")
        print("  1. Current MongoDB is running on port 27017")
        print("  2. Backup MongoDB is running on port 27018")
        print("     Run: mongod --dbpath ~/Desktop/mongodb_backup --port 27018 --quiet &")
        sys.exit(1)
    
    # Perform merge
    all_stats = {}
    all_stats["gridfs"] = merge_gridfs_files(backup_db, current_db, dry_run=args.dry_run)
    all_stats["items"] = merge_item_images(backup_db, current_db, dry_run=args.dry_run)
    all_stats["history"] = merge_analysis_history(backup_db, current_db, dry_run=args.dry_run)
    
    # Print summary
    print_summary(all_stats)
    
    # Cleanup
    backup_client.close()
    current_client.close()
    
    # Check for critical errors
    total_errors = sum(len(stats.get("errors", [])) for stats in all_stats.values())
    if total_errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
