#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
Create a new release by consolidating changelog entries from next-release directory
into a version JSON file (x.y.z.json).
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
VERSION_PATTERN = r"^\d+\.\d+\.\d+$"
CHANGE_TYPES_ORDER = {"breaking": 0, "feature": 1, "enhancement": 2, "bugfix": 3, "dependency": 4}
CHANGE_TYPES = tuple(CHANGE_TYPES_ORDER.keys())


def validate_change_entry(change_data: dict[str, Any], entry_file: Path) -> bool:
    if "type" not in change_data or change_data["type"] not in CHANGE_TYPES:
        print(
            f"Error: Missing or invalid 'type' field in {entry_file}\n"
            f"Type must be one of: {CHANGE_TYPES}"
        )
        return False

    if "description" not in change_data or not change_data["description"]:
        print(f"Error: Missing or empty 'description' field in {entry_file}")
        return False

    return True


def collect_next_release_changes(next_release_dir: Path) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []

    if not next_release_dir.exists():
        return changes

    for entry_file in next_release_dir.iterdir():
        if entry_file.is_file() and entry_file.suffix == ".json":
            try:
                with open(entry_file) as f:
                    change_data = json.load(f)

                    # Validate required fields
                    if not validate_change_entry(change_data, entry_file):
                        sys.exit(1)

                    changes.append(change_data)
            except (OSError, json.JSONDecodeError) as e:
                print(f"Error: Could not process {entry_file}: {e}", file=sys.stderr)
                sys.exit(1)

    # Sort changes by type for consistent ordering
    changes.sort(key=lambda c: (CHANGE_TYPES_ORDER[c["type"]]))

    return changes


def create_version_file(
    changes_dir: Path,
    version: str,
    changes: list[dict[str, Any]],
) -> Path:
    version_file = changes_dir / f"{version}.json"

    if version_file.exists():
        print(f"Error: Version file {version_file} already exists!")
        sys.exit(1)

    version_data: dict[str, Any] = {"changes": changes}

    with open(version_file, "w") as f:
        json.dump(version_data, f, indent=2)

    return version_file


def cleanup_next_release_dir(next_release_dir: Path) -> int:
    removed_count = 0

    for entry_file in next_release_dir.iterdir():
        if entry_file.is_file() and entry_file.suffix == ".json":
            try:
                entry_file.unlink()
                removed_count += 1
            except OSError as e:
                print(f"Warning: Could not remove {entry_file}: {e}", file=sys.stderr)

    return removed_count


def create_new_release(package_name: str, version: str, dry_run: bool = False) -> int:
    # Get package directories
    changes_dir = PROJECT_ROOT_DIR / "packages" / package_name / ".changes"
    next_release_dir = changes_dir / "next-release"

    if not changes_dir.exists():
        print(f"Error: No .changes directory found for package: {package_name}")
        return 1

    # Collect changes from next-release
    changes = collect_next_release_changes(next_release_dir)

    if not changes:
        print(
            f"No changelog entries found in {next_release_dir}.\n"
            "Use 'python scripts/changelog/new-entry.py' to create entries first"
        )
        return 1

    print(f"Found {len(changes)} changelog entries for {package_name} v{version}:")
    for change in changes:
        change_type = change.get("type", "unknown").upper()
        description = change.get("description", "No description")
        print(f"  {change_type}: {description}")

    if dry_run:
        print("\n[DRY RUN] Would create version file and remove next-release entries")
        return 0

    # Create version file
    try:
        version_file = create_version_file(changes_dir, version, changes)
        print(f"\nCreated version file: {version_file}")
    except Exception as e:
        print(f"Error creating version file: {e}")
        return 1

    # Clean up next-release directory
    removed_count = cleanup_next_release_dir(next_release_dir)
    print(f"Removed {removed_count} changelog entries from next-release")
    print(f"✅ Successfully created release {version} for {package_name}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a new release by consolidating changelog entries"
    )
    parser.add_argument("-p", "--package", required=True, help="Package name")
    parser.add_argument(
        "-v", "--version", required=True, help="Release version (e.g., 1.0.0)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    # Basic version format validation
    if not bool(re.match(VERSION_PATTERN, args.version)):
        print("Error: Version must be in format x.y.z (e.g., 1.2.3)")
        return 1

    return create_new_release(
        package_name=args.package,
        version=args.version,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    exit(main())
