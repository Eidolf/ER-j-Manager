#!/usr/bin/env python3
import sys
import os
import argparse
import datetime
import re

VERSION_FILE = "VERSION"

def read_version():
    if not os.path.exists(VERSION_FILE):
        return "0.0.0"
    with open(VERSION_FILE, "r") as f:
        return f.read().strip()

def write_version(version):
    with open(VERSION_FILE, "w") as f:
        f.write(version)
    print(f"Updated VERSION to {version}")

def get_date_parts():
    now = datetime.datetime.utcnow()
    return now.year, now.month, now.strftime("%Y%m%d.%H%M")

def bump_version(release_type, current_version):
    year, month, timestamp = get_date_parts()
    
    # Parse current version
    # Expected format: YYYY.MM.PATCH or YYYY.MM.PATCH-suffix
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-(.+))?$", current_version)
    
    if match:
        curr_year = int(match.group(1))
        curr_month = int(match.group(2))
        curr_patch = int(match.group(3))
    else:
        # Fallback if invalid
        curr_year, curr_month, curr_patch = 0, 0, 0

    # Logic: Reset patch if Year or Month changes
    if year != curr_year or month != curr_month:
        new_patch = 1
    else:
        new_patch = curr_patch

    # For 'dev' bumps or stable releases, we increment patch if it's the SAME month/year
    # However, if we just switched month, we effectively already 'bumped' to 1.
    
    base_version = f"{year}.{month}.{new_patch}"

    if release_type == "stable":
        # Ensure we are strictly bumping from a previous state.
        # If we are already on YYYY.MM.N, stable just keeps it?
        # Usually release implies we finalize this version.
        # But if we were on YYYY.MM.1-beta, stable becomes YYYY.MM.1
        # If we were on YYYY.MM.1 (stable), requesting stable again implies a hotfix?
        # Let's keep it simple: Release uses the projected base version.
        if year == curr_year and month == curr_month:
             # Same month release, increment patch from previous STABLE or just use current if coming from dev?
             # User spec: "Reset patch to 1 when month or year changes."
             pass
        return base_version

    elif release_type == "beta":
        return f"{base_version}-beta"

    elif release_type == "nightly":
        return f"{base_version}-nightly.{timestamp}"

    elif release_type == "dev":
        # Post-release bump. If we just released 2024.1.5, dev becomes 2024.1.6-dev
        if year == curr_year and month == curr_month:
             new_patch = curr_patch + 1
        base_version = f"{year}.{month}.{new_patch}"
        return f"{base_version}-dev"
    
    return current_version

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=["read", "bump"], required=True)
    parser.add_argument("--type", choices=["nightly", "beta", "stable", "dev"], default="dev")
    args = parser.parse_args()

    current_version = read_version()

    if args.action == "read":
        print(current_version)
    elif args.action == "bump":
        new_version = bump_version(args.type, current_version)
        write_version(new_version)
        print(new_version)

if __name__ == "__main__":
    main()
