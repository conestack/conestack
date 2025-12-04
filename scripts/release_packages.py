#!/usr/bin/env python
"""Release Script for Conestack Monorepo

This script automates releasing all packages with unreleased changes
using zest.releaser.

USAGE
=====

    # Preview releases (dry-run)
    python scripts/release_packages.py --dry-run

    # List packages needing release
    python scripts/release_packages.py --list

    # Release all packages with changes
    python scripts/release_packages.py

    # Release specific packages
    python scripts/release_packages.py --package node --package odict

DETECTION
=========

A package needs release when CHANGES.rst contains an "(unreleased)" section
with actual change entries (not "No changes yet").
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

from zest.releaser.baserelease import NOTHING_CHANGED_YET

# Package groups in dependency order
PACKAGE_GROUPS = [
    # Group 1: Base packages
    (
        "Base packages",
        [
            "odict",
            "plumber",
            "webresource",
            "treibstoff",
        ],
    ),
    # Group 2: Node packages
    (
        "Node packages",
        [
            "node",
            "node.ext.directory",
            "node.ext.fs",
            "node.ext.ldap",
            "node.ext.ugm",
            "node.ext.yaml",
            "node.ext.zodb",
        ],
    ),
    # Group 3: YAFOWIL packages
    (
        "YAFOWIL packages",
        [
            "yafowil",
            "yafowil.bootstrap",
            "yafowil.lingua",
            "yafowil.webob",
            "yafowil.yaml",
            "yafowil.widget.ace",
            "yafowil.widget.array",
            "yafowil.widget.autocomplete",
            "yafowil.widget.chosen",
            "yafowil.widget.color",
            "yafowil.widget.cron",
            "yafowil.widget.datetime",
            "yafowil.widget.dict",
            "yafowil.widget.dynatree",
            "yafowil.widget.image",
            "yafowil.widget.location",
            "yafowil.widget.multiselect",
            "yafowil.widget.richtext",
            "yafowil.widget.select2",
            "yafowil.widget.slider",
            "yafowil.widget.tiptap",
            "yafowil.widget.wysihtml5",
        ],
    ),
    # Group 4: Cone packages
    (
        "Cone packages",
        [
            "cone.tile",
            "cone.app",
            "cone.calendar",
            "cone.charts",
            "cone.fileupload",
            "cone.firebase",
            "cone.ldap",
            "cone.maps",
            "cone.sql",
            "cone.three",
            "cone.tokens",
            "cone.ugm",
            "cone.zodb",
        ],
    ),
]

# Flat list of all packages in release order
ALL_PACKAGES = [pkg for _, packages in PACKAGE_GROUPS for pkg in packages]


def get_root_dir():
    """Get the monorepo root directory."""
    return Path(__file__).parent.parent


def get_package_dir(package):
    """Get the source directory for a package."""
    return get_root_dir() / "sources" / package


def parse_changes_rst(package_dir):
    """Parse CHANGES.rst and check for unreleased changes.

    :return: Tuple of (version_string, has_changes, reason)
    """
    changes_file = package_dir / "CHANGES.rst"
    if not changes_file.exists():
        return None, False, "No CHANGES.rst file"

    content = changes_file.read_text()

    # Match version header with (unreleased)
    # Pattern: "X.Y.Z (unreleased)" followed by dashes
    pattern = (
        r"^(\d+\.\d+(?:\.\d+)?)\s+\(unreleased\)\s*\n"
        r"-+\s*\n"
        r"(.*?)(?=\n\d+\.\d+|\Z)"
    )
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)

    if not match:
        return None, False, "No unreleased section in CHANGES.rst"

    version = match.group(1)
    section_content = match.group(2).strip()

    # Check if section contains the "nothing changed yet" marker
    if NOTHING_CHANGED_YET in section_content:
        return version, False, "No changes yet"

    # Check if section has actual content (bullet points)
    if not re.search(r"^-\s+\S", section_content, re.MULTILINE):
        return version, False, "Unreleased section is empty"

    return version, True, "Has unreleased changes"


def needs_release(package):
    """Check if a package needs release.

    :return: Tuple of (needs_release, version, reason)
    """
    package_dir = get_package_dir(package)
    if not package_dir.exists():
        return False, None, "Package directory not found"

    version, has_changes, reason = parse_changes_rst(package_dir)
    return has_changes, version, reason


def release_package(package, dry_run=False, no_upload=False, verbose=False):
    """Release a single package using zest.releaser.

    :return: True if successful, False otherwise
    """
    package_dir = get_package_dir(package)

    if dry_run:
        print(f"  [DRY-RUN] Would run fullrelease in {package_dir}")
        return True

    # Build fullrelease command
    cmd = ["fullrelease", "--no-input"]
    if no_upload:
        # Use prerelease + release without upload
        cmd = ["prerelease", "--no-input"]

    try:
        result = subprocess.run(
            cmd,
            cwd=package_dir,
            capture_output=not verbose,
            text=True,
        )

        if result.returncode != 0:
            if not verbose:
                print(f"  STDERR: {result.stderr}")
            return False

        if no_upload:
            # Run release (tag) but skip upload
            subprocess.run(
                ["release", "--no-input"],
                cwd=package_dir,
                capture_output=not verbose,
                text=True,
            )
            # Run postrelease for version bump
            subprocess.run(
                ["postrelease", "--no-input"],
                cwd=package_dir,
                capture_output=not verbose,
                text=True,
            )

        return True

    except FileNotFoundError:
        print("  ERROR: fullrelease not found. Install zest.releaser:")
        print("         ./venv/bin/pip install zest.releaser[recommended]")
        return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Release Conestack packages with unreleased changes"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be released without doing it",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_only",
        help="List packages needing release and exit",
    )
    parser.add_argument(
        "--package",
        action="append",
        dest="packages",
        metavar="PKG",
        help="Release only specified package (can be repeated)",
    )
    parser.add_argument(
        "--skip",
        action="append",
        dest="skip_packages",
        metavar="PKG",
        help="Skip specified package (can be repeated)",
    )
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Prepare release but don't upload to PyPI",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    # Determine which packages to process
    if args.packages:
        # Keep user-specified order but filter to valid packages
        packages = [p for p in args.packages if p in ALL_PACKAGES]
    else:
        packages = ALL_PACKAGES

    if args.skip_packages:
        packages = [p for p in packages if p not in args.skip_packages]

    # Find packages needing release
    to_release = []
    skipped = []

    print("Checking packages for unreleased changes...")
    print()

    for package in packages:
        needs, version, reason = needs_release(package)
        if needs:
            to_release.append((package, version))
            if args.verbose or args.list_only:
                print(f"  {package} ({version}): {reason}")
        else:
            skipped.append((package, reason))
            if args.verbose:
                print(f"  {package}: SKIP - {reason}")

    print()
    print(f"Packages to release: {len(to_release)}")
    print(f"Packages skipped: {len(skipped)}")

    if args.list_only:
        if to_release:
            print()
            print("Packages needing release:")
            for package, version in to_release:
                print(f"  - {package} ({version})")
        return 0

    if not to_release:
        print()
        print("No packages need release.")
        return 0

    print()
    if args.dry_run:
        print("DRY-RUN MODE - No actual releases will be made")
    print()

    # Release packages
    released = []
    failed = []

    for package, version in to_release:
        print(f"Releasing {package} ({version})...")

        if release_package(package, args.dry_run, args.no_upload, args.verbose):
            released.append(package)
            print("  OK")
        else:
            failed.append(package)
            print("  FAILED")

        print()

    # Summary
    print("=" * 60)
    print("RELEASE SUMMARY")
    print("=" * 60)
    print(f"Released: {len(released)}")
    print(f"Failed: {len(failed)}")
    print(f"Skipped: {len(skipped)}")

    if failed:
        print()
        print("Failed packages:")
        for package in failed:
            print(f"  - {package}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
