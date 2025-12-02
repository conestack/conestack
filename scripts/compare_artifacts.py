#!/usr/bin/env python
"""Artifact Comparison Script for Conestack Monorepo

This script compares the contents of wheel and sdist artifacts for all packages
in the dist/ directory. It identifies files that are present in one artifact
but missing from the other, helping to ensure consistent package contents.

REQUIREMENTS
============

This script requires only Python standard library modules (zipfile, tarfile).
It should be run after `make validate-build` to analyze the built artifacts.

USAGE
=====

    # Compare all artifacts in dist/
    ./venv/bin/python scripts/compare_artifacts.py

The script automatically finds all wheel files in dist/, locates their
corresponding sdist files, and compares the contents.

OUTPUT
======

The script reports:

1. Packages with no issues (wheel and sdist contents match)
2. For each package with differences:
   - Files in wheel but not in sdist (marked with +)
   - Files in sdist but not in wheel (marked with -)

FILTERING
=========

The following files are automatically filtered and not reported:

From sdist (expected differences):
- .gitignore files (not included in wheels)
- PKG-INFO, setup.cfg, setup.py, pyproject.toml (metadata files)
- LICENSE*, README*, CHANGES*, HISTORY* (documentation files)
- Test files (paths containing /tests/ or starting with tests/)
- Non-Python files (.rst, .md, .txt, .ini, .cfg, .toml)

From wheel:
- .dist-info/ directory contents (wheel metadata)

COMMON ISSUES
=============

Files that commonly appear as differences and may need attention:

1. **cfg/*.xml files**: Test configuration files that should be excluded
   from sdist via pyproject.toml [tool.hatch.build] excludes

2. **.travis.yml, Makefile, MANIFEST.in**: Obsolete files that should be
   removed from the repository or excluded from sdist

3. **Nested .gitignore files**: Sometimes included in wheels when they
   exist in package subdirectories (e.g., static asset directories)

EXAMPLES
========

Typical workflow:

    # Build all packages
    make validate-build

    # Compare artifacts
    ./venv/bin/python scripts/compare_artifacts.py

    # Fix issues in pyproject.toml and rebuild
    make validate-clean
    make validate-build
    ./venv/bin/python scripts/compare_artifacts.py

EXIT CODES
==========

The script always exits with code 0. It is designed for informational
purposes and does not fail on differences (some differences are expected).

NOTES
=====

- The script uses the dist/ directory in the repository root
- Both wheel (.whl) and sdist (.tar.gz) must exist for comparison
- Packages are identified by wheel filename pattern: {name}-{version}-*.whl
- The src/ prefix is normalized for src-layout packages

AUTHOR
======

Generated for the Conestack monorepo artifact validation workflow.
"""

import tarfile
import tempfile
import zipfile
from pathlib import Path


def get_wheel_files(wheel_path):
    """Extract file list from wheel (zip format)."""
    files = set()
    with zipfile.ZipFile(wheel_path, 'r') as zf:
        for name in zf.namelist():
            # Skip .dist-info directory
            if '.dist-info/' in name:
                continue
            # Normalize path
            files.add(name)
    return files


def get_sdist_files(sdist_path):
    """Extract file list from sdist (tar.gz format)."""
    files = set()
    with tarfile.open(sdist_path, 'r:gz') as tf:
        for member in tf.getmembers():
            if member.isfile():
                # Remove the top-level directory (package-version/)
                parts = member.name.split('/', 1)
                if len(parts) > 1:
                    path = parts[1]
                    # Skip metadata files
                    if path in ('PKG-INFO', 'setup.cfg', 'setup.py', 'pyproject.toml'):
                        continue
                    if path.startswith(('LICENSE', 'README', 'CHANGES', 'HISTORY')):
                        continue
                    # Skip .gitignore (expected in sdist but not wheel)
                    if path == '.gitignore' or path.endswith('/.gitignore'):
                        continue
                    files.add(path)
    return files


def normalize_wheel_path(path):
    """Normalize wheel path to match sdist structure."""
    # Wheel stores files directly, sdist has src/ prefix for src-layout packages
    return path


def normalize_sdist_path(path):
    """Normalize sdist path for comparison."""
    # Remove src/ prefix if present (src-layout packages)
    if path.startswith('src/'):
        return path[4:]
    return path


def compare_package(wheel_path, sdist_path):
    """Compare wheel and sdist contents."""
    wheel_files = get_wheel_files(wheel_path)
    sdist_files = get_sdist_files(sdist_path)

    # Normalize sdist paths (remove src/ prefix)
    sdist_normalized = {normalize_sdist_path(f) for f in sdist_files}

    # Filter sdist to only include Python package files (not tests, docs, etc.)
    # Wheel should only contain the installable package
    sdist_package_files = set()
    for f in sdist_normalized:
        # Skip test files
        if '/tests/' in f or f.startswith('tests/'):
            continue
        # Skip non-Python files that aren't typically in wheels
        if f.endswith(('.rst', '.md', '.txt', '.ini', '.cfg', '.toml')):
            continue
        sdist_package_files.add(f)

    # Files in wheel but not in sdist (shouldn't happen normally)
    wheel_only = wheel_files - sdist_normalized

    # Files in sdist package but not in wheel (potentially missing from wheel)
    sdist_only = sdist_package_files - wheel_files

    return {
        'wheel_files': wheel_files,
        'sdist_files': sdist_files,
        'sdist_package_files': sdist_package_files,
        'wheel_only': wheel_only,
        'sdist_only': sdist_only,
    }


def main():
    dist_dir = Path('/home/rnix/workspace/conestack/dist')

    # Find all wheel files
    wheels = sorted(dist_dir.glob('*.whl'))

    issues_found = False

    for wheel_path in wheels:
        # Extract package name and version from wheel filename
        # Format: {package}-{version}-{python}-{abi}-{platform}.whl
        parts = wheel_path.stem.split('-')
        pkg_name = parts[0]
        pkg_version = parts[1]

        # Find corresponding sdist
        sdist_path = dist_dir / f"{pkg_name}-{pkg_version}.tar.gz"

        if not sdist_path.exists():
            print(f"\n{'='*60}")
            print(f"PACKAGE: {pkg_name}")
            print(f"{'='*60}")
            print(f"  ERROR: No sdist found for {wheel_path.name}")
            issues_found = True
            continue

        result = compare_package(wheel_path, sdist_path)

        has_issues = result['wheel_only'] or result['sdist_only']

        if has_issues:
            issues_found = True
            print(f"\n{'='*60}")
            print(f"PACKAGE: {pkg_name}")
            print(f"{'='*60}")
            print(f"  Wheel: {wheel_path.name}")
            print(f"  Sdist: {sdist_path.name}")
            print(f"  Wheel file count: {len(result['wheel_files'])}")
            print(f"  Sdist file count: {len(result['sdist_files'])}")

            if result['wheel_only']:
                print(f"\n  FILES IN WHEEL BUT NOT IN SDIST ({len(result['wheel_only'])}):")
                for f in sorted(result['wheel_only']):
                    print(f"    + {f}")

            if result['sdist_only']:
                print(f"\n  FILES IN SDIST BUT NOT IN WHEEL ({len(result['sdist_only'])}):")
                for f in sorted(result['sdist_only']):
                    print(f"    - {f}")

    if not issues_found:
        print("All packages: wheel and sdist contents match (no issues found)")
    else:
        print(f"\n{'='*60}")
        print("NOTE: Some differences are expected:")
        print("  - Tests are typically excluded from wheels")
        print("  - Documentation files are excluded from wheels")
        print("  - Only package source files should be in both")


if __name__ == '__main__':
    main()
