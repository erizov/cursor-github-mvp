#!/usr/bin/env python3
"""
Clean up unused Docker images matching alg-teach-* pattern that are unused
for more than 15 minutes (not in use by any containers).

Usage:
    python scripts/cleanup_old_images.py [--age-minutes=15]
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
        if result.returncode != 0:
            return None
        
        created_str = result.stdout.strip()
        if not created_str:
            return None
        
        # Try multiple parsing strategies
        # Format 1: ISO 8601 with timezone (e.g., "2024-01-15T12:00:00.123456789Z")
        # Format 2: ISO 8601 without timezone (e.g., "2024-01-15T12:00:00.123456789")
        
        # Remove nanoseconds if present (keep microseconds)
        if "." in created_str:
            parts = created_str.split(".")
            if len(parts) > 1:
                # Keep only up to microseconds
                microseconds = parts[1][:6].rstrip("Z").rstrip("+00:00").rstrip(" ")
                created_str = f"{parts[0]}.{microseconds}"
            else:
                created_str = parts[0]
        
        # Handle timezone indicators
        if created_str.endswith("Z"):
            created_str = created_str[:-1] + "+00:00"
        elif "+" not in created_str and "-" in created_str[-6:]:
            # Might have timezone offset like "-05:00"
            pass
        elif "+" not in created_str and "T" in created_str:
            # No timezone, assume UTC
            if not created_str.endswith("+00:00"):
                created_str += "+00:00"
        
        # Try parsing with timezone first
        try:
            dt = datetime.fromisoformat(created_str)
            # Make timezone-aware if it isn't
            if dt.tzinfo is None:
                from datetime import timezone
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            # Try without timezone
            try:
                dt = datetime.fromisoformat(created_str.replace("+00:00", "").rstrip("Z"))
                from datetime import timezone
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                # Try parsing with dateutil if available
                try:
                    from dateutil import parser as date_parser
                    return date_parser.parse(created_str)
                except ImportError:
                    # Last resort: try parsing common formats
                    for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                        try:
                            return datetime.strptime(created_str.split(".")[0].split("+")[0].split("-")[0], fmt)
                        except ValueError:
                            continue
    except Exception as e:
        print(f"Error parsing creation time for {image_id}: {e}", file=sys.stderr)
    
    return None


def is_image_in_use(image_id: str, image_name: str = "") -> bool:
    """Check if an image is in use by any containers.
    
    Args:
        image_id: Docker image ID
        image_name: Optional image name (repository:tag) for more accurate checking
    """
    # Check by image ID first (ancestor filter)
    result = subprocess.run(
        ["docker", "ps", "-a", "--filter", f"ancestor={image_id}", "--format", "{{.ID}}"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode == 0 and result.stdout.strip():
        return True
    
    # If we have image name, check by name as well
    if image_name and image_name != "<none>:<none>":
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"image={image_name}", "--format", "{{.ID}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return True
    
    return False


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
                image_id = parts[0]
                image_name = f"{repo}:{tag}" if tag else repo
                in_use = is_image_in_use(image_id, image_name)
                images.append({
                    "id": image_id,
                    "repository": repo,
                    "tag": tag or "<none>",
                    "image_name": image_name,
                    "in_use": in_use,
                })
    
    return images


def cleanup_old_images(age_minutes: int = 15, dry_run: bool = False) -> int:
    """Remove unused Docker images older than specified age."""
    from datetime import timezone
    now = datetime.now(timezone.utc)
    cutoff_time = now - timedelta(minutes=age_minutes)
    images = list_alg_teach_images()
    removed_count = 0
    
    print(f"Found {len(images)} alg-teach-* images")
    print(f"Removing unused images unused for more than {age_minutes} minutes (before {cutoff_time.isoformat()})")
    
    for img in images:
        # Skip images that are currently in use
        if img.get("in_use", False):
            print(f"  Keeping {img['repository']}:{img['tag']} (in use by containers)")
            continue
        
        created = get_image_creation_time(img["id"])
        if created is None:
            # If we can't determine age, skip (safer)
            print(f"  Skipping {img['repository']}:{img['tag']} (cannot determine age)")
            continue
        
        # Ensure both datetimes are timezone-aware for comparison
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        if cutoff_time.tzinfo is None:
            cutoff_time = cutoff_time.replace(tzinfo=timezone.utc)
        
        if created < cutoff_time:
            age_delta = now - created
            age_str = str(age_delta).split(".")[0]
            if dry_run:
                print(f"  [DRY RUN] Would remove {img['repository']}:{img['tag']} (unused, age: {age_str})")
                removed_count += 1
            else:
                print(f"  Removing {img['repository']}:{img['tag']} (unused, age: {age_str})")
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
            age_delta = now - created
            age_str = str(age_delta).split(".")[0]
            print(f"  Keeping {img['repository']}:{img['tag']} (unused but too recent, age: {age_str})")
    
    return removed_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clean up old alg-teach-* Docker images"
    )
    parser.add_argument(
        "--age-minutes",
        type=int,
        default=15,
        help="Remove unused images unused for more than this many minutes (default: 15)",
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

