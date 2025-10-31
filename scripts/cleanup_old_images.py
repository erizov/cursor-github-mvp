#!/usr/bin/env python3
"""
Clean up old Docker images matching alg-teach-* pattern that are older than
30 minutes.

Usage:
    python scripts/cleanup_old_images.py [--age-minutes=30]
"""

import argparse
import subprocess
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional


def get_image_creation_time(image_id: str) -> Optional[datetime]:
    """Get image creation time using docker inspect."""
    try:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.Created}}", image_id],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            created_str = result.stdout.strip()
            # Parse ISO 8601 format
            try:
                return datetime.fromisoformat(created_str.replace("Z", "+00:00").replace(" +0000", ""))
            except ValueError:
                # Try alternative parsing
                return datetime.fromisoformat(created_str.split(".")[0])
    except Exception:
        pass
    return None


def list_alg_teach_images() -> List[Dict[str, str]]:
    """List all Docker images matching alg-teach-* pattern."""
    images = []
    result = subprocess.run(
        ["docker", "images", "--format", "{{.ID}}\t{{.Repository}}\t{{.Tag}}"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    
    if result.returncode != 0:
        print(f"Error listing images: {result.stderr}", file=sys.stderr)
        return images
    
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) >= 3:
            repo = parts[1]
            tag = parts[2]
            if repo and repo.startswith("alg-teach-"):
                images.append({
                    "id": parts[0],
                    "repository": repo,
                    "tag": tag or "<none>",
                })
    
    return images


def cleanup_old_images(age_minutes: int = 30, dry_run: bool = False) -> int:
    """Remove Docker images older than specified age."""
    cutoff_time = datetime.now() - timedelta(minutes=age_minutes)
    images = list_alg_teach_images()
    removed_count = 0
    
    print(f"Found {len(images)} alg-teach-* images")
    print(f"Removing images older than {age_minutes} minutes (before {cutoff_time.isoformat()})")
    
    for img in images:
        created = get_image_creation_time(img["id"])
        if created is None:
            # If we can't determine age, skip (safer)
            print(f"  Skipping {img['repository']}:{img['tag']} (cannot determine age)")
            continue
        
        # Make timezone-naive for comparison
        if created.tzinfo:
            created = created.replace(tzinfo=None)
        
        if created < cutoff_time:
            age_str = str(datetime.now() - created).split(".")[0]
            if dry_run:
                print(f"  [DRY RUN] Would remove {img['repository']}:{img['tag']} (age: {age_str})")
            else:
                print(f"  Removing {img['repository']}:{img['tag']} (age: {age_str})")
                result = subprocess.run(
                    ["docker", "rmi", "-f", img["id"]],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    removed_count += 1
                else:
                    print(f"    Warning: Failed to remove {img['repository']}: {result.stderr}")
        else:
            age_str = str(datetime.now() - created).split(".")[0]
            print(f"  Keeping {img['repository']}:{img['tag']} (age: {age_str})")
    
    return removed_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clean up old alg-teach-* Docker images"
    )
    parser.add_argument(
        "--age-minutes",
        type=int,
        default=30,
        help="Remove images older than this many minutes (default: 30)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without actually removing",
    )
    args = parser.parse_args()
    
    removed = cleanup_old_images(age_minutes=args.age_minutes, dry_run=args.dry_run)
    
    if args.dry_run:
        print(f"\n[DRY RUN] Would remove {removed} images")
    else:
        print(f"\nRemoved {removed} images")


if __name__ == "__main__":
    main()

