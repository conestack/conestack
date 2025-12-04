#!/usr/bin/env python
"""Package Validation Script for Conestack Monorepo

This script validates Python packages through multiple phases to ensure they are
ready for release to PyPI. It tests the actual built artifacts, not source code,
simulating what users will receive when installing from PyPI.

REQUIREMENTS
============

This script requires `pip` and `venv` to be installed in used python interpreter.

Each validation creates its own isolated venv with `build`, `pyrmoma` and `pytest`
installed plus the package being validated.

USAGE
=====

The script supports modular phase-based validation. You can run individual phases
or execute all phases in sequence.

Phase Commands:

    # Create venv and install build/validation tools
    python scripts/validate_package.py <package> --env

    # Build wheel/sdist and copy to root dist/
    python scripts/validate_package.py <package> --build

    # Run pyroma and twine check
    python scripts/validate_package.py <package> --check

    # Install from root/dist and run pytest
    python scripts/validate_package.py <package> --test

    # Remove venv and dist/
    python scripts/validate_package.py <package> --clean

    # Run all phases in sequence
    python scripts/validate_package.py <package> --all

Examples:

    # Full validation workflow
    python scripts/validate_package.py node --all

    # Manual step-by-step validation
    python scripts/validate_package.py node --env
    python scripts/validate_package.py node --build
    python scripts/validate_package.py node --check
    python scripts/validate_package.py node --test
    python scripts/validate_package.py node --clean

    # Build all packages, then test one
    make validate-build
    python scripts/validate_package.py node --env
    python scripts/validate_package.py node --test

    # Verbose output
    python scripts/validate_package.py cone.app --all -v

    # Custom pyroma threshold
    python scripts/validate_package.py plumber --all --pyroma-threshold 9

OPTIONS
=======

Positional Arguments:
  package              Package name (directory name in sources/)

Phase Selection (required, mutually exclusive):
  --env                Create venv and install build/validation tools
  --build              Build wheel/sdist using venv and copy to root dist/
  --check              Run pyroma and twine check
  --test               Install package from root/dist and run pytest
  --clean              Remove venv and dist/
  --all                Run all phases: env → build → check → test → clean

Configuration Options:
  --pyroma-threshold N Minimum pyroma quality score (default: 8)
  --install-from TYPE  Install from 'wheel' or 'sdist' for testing (default: wheel)
  -v, --verbose        Show detailed output
  -h, --help           Show this help message

VALIDATION PHASES
=================

1. --env: Environment Setup
   - Creates venv at sources/<package>/venv/
   - Upgrades pip
   - Installs build, pyroma, twine
   - Venv persists for use by other phases

2. --build: Build Distributions
   - Uses venv's build tool to create wheel and sdist
   - Copies artifacts to root dist/ directory
   - Makes packages available for cross-package dependencies
   - Requires: --env

3. --check: Quality Validation
   - Runs twine check on built distributions
   - Runs pyroma quality rating (must meet threshold)
   - Requires: --env and --build

4. --test: Installation and Testing
   - Installs package FROM root/dist (wheel or sdist, NOT from sources)
   - Uses --find-links to resolve dependencies from root/dist
   - Installs test dependencies via package[test]
   - Runs pytest from the source checkout directory
   - Validates the actual release artifact
   - Requires: --env and --build

   IMPORTANT: The package code is installed from the built artifact (wheel/sdist),
   but tests are executed from the source checkout (sources/<package>/). This is
   intentional - tests are planned to be moved to the package root folder and
   excluded from releases in future versions. This approach validates that the
   installed package works correctly while using the latest test code.

5. --clean: Cleanup
   - Removes sources/<package>/venv/
   - Removes sources/<package>/dist/
   - Does NOT remove root dist/ (managed by make targets)

6. --all: Complete Workflow
   - Runs env → build → check → test → clean in sequence
   - Stops on first failure
   - Cleans up automatically at the end

EXIT CODES
==========

0  - Phase completed successfully
1  - Phase failed (build error, test failure, quality below threshold, etc.)
2  - Setup error (missing venv, missing dist/, invalid package, etc.)

ENVIRONMENT
===========

The script sets the following environment variables during test execution
(matching the configuration in mx.ini):

- TESTRUN_MARKER=1
- LDAP_ADD_BIN=openldap/bin/ldapadd
- LDAP_DELETE_BIN=openldap/bin/ldapdelete
- SLAPD_BIN=openldap/libexec/slapd
- SLAPD_URIS=ldap://127.0.0.1:12345

KEY DESIGN POINTS
=================

1. The --test phase installs the package FROM root/dist (the built wheel or
   sdist), NOT from sources. This simulates a real PyPI installation and
   validates the actual release artifact that users will receive.

2. Tests are executed from the source checkout directory (sources/<package>/),
   not from the installed package. This is by design:
   - Package code under test comes from the installed artifact
   - Test code comes from the source checkout
   - This allows tests to be excluded from releases in the future
   - Tests will be moved to package root folders (outside src/) and excluded
     from wheel/sdist builds

3. All pip installs use --find-links pointing to root/dist, allowing packages
   to depend on pre-built versions of sibling packages. This enables validation
   of the entire dependency tree before publishing to PyPI.

4. Venv and dist/ persist between phases until --clean is run. This allows
   incremental validation and debugging of specific phases.

5. Development versions (e.g., 2.0.0.dev0) are preferred over published versions
   using pip's --pre and --upgrade flags.

NOTES
=====

- Each phase can be run independently or combined with --all
- Venv location: sources/<package>/venv/ (persists between phases)
- Build artifacts: sources/<package>/dist/ (copied to root dist/)
- Phases must be run in dependency order: env before build/test, build before check/test
- Package must exist in sources/{package-name}/
- Package must have [project.optional-dependencies] test defined in pyproject.toml

AUTHOR
======

Generated for the Conestack monorepo package validation workflow.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Constant for venv directory name
VALIDATE_VENV_DIR = "venv"


class ValidationError(Exception):
    """Raised when a validation step fails."""

    pass


class Colors:
    """ANSI color codes for terminal output."""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    @classmethod
    def disable(cls):
        """Disable colors (for non-TTY output)."""
        cls.HEADER = ""
        cls.OKBLUE = ""
        cls.OKCYAN = ""
        cls.OKGREEN = ""
        cls.WARNING = ""
        cls.FAIL = ""
        cls.ENDC = ""
        cls.BOLD = ""
        cls.UNDERLINE = ""


def print_step(message, verbose=False):
    """Print a validation step header."""
    if verbose or True:  # Always show steps
        print(f"\n{Colors.HEADER}{Colors.BOLD}=== {message} ==={Colors.ENDC}")


def print_success(message):
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message):
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}", file=sys.stderr)


def print_info(message, verbose=False):
    """Print an info message (only in verbose mode)."""
    if verbose:
        print(f"{Colors.OKCYAN}{message}{Colors.ENDC}")


def run_command(cmd, cwd=None, env=None, verbose=False):
    """Run a shell command and return output.

    Raises ValidationError if command fails.
    """
    if verbose:
        print_info(f"Running: {' '.join(cmd)}", verbose=True)

    try:
        result = subprocess.run(
            cmd, cwd=cwd, env=env, capture_output=True, text=True, check=True
        )
        if verbose and result.stdout:
            print(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {' '.join(cmd)}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        raise ValidationError(f"Command failed with exit code {e.returncode}")


def phase_env(package, repo_root, verbose=False):
    """Create venv and install build and validation tools.

    Creates venv at sources/<package>/venv/ and installs:
    - build (for building wheels/sdists)
    - pyroma (for quality checks)
    - twine (for PyPI validation)

    Does NOT install the package itself - that happens in phase_test.

    :param package: Package name
    :param repo_root: Path to repository root
    :param verbose: Show detailed output
    :return: 0 on success, 1 on failure
    """
    print_step(f"Phase: env - Creating venv for {package}", verbose)

    package_dir = repo_root / "sources" / package
    venv_path = package_dir / VALIDATE_VENV_DIR

    # Remove existing venv if it exists (ensure clean state)
    if venv_path.exists():
        print_info(f"Removing existing venv: {venv_path}", verbose)
        shutil.rmtree(venv_path)

    # Create venv
    print_info(f"Creating venv: {venv_path}", verbose)
    try:
        run_command([sys.executable, "-m", "venv", str(venv_path)], verbose=verbose)
    except ValidationError as e:
        print_error(f"Failed to create venv: {e}")
        return 1

    venv_python = venv_path / "bin" / "python"
    if not venv_python.exists():
        print_error(f"Venv python not found: {venv_python}")
        return 1

    # Upgrade pip
    print_info("Upgrading pip in venv", verbose)
    try:
        run_command(
            [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
            verbose=verbose,
        )
    except ValidationError as e:
        print_error(f"Failed to upgrade pip: {e}")
        return 1

    # Install build, pyroma, and twine
    print_info("Installing build, pyroma, and twine", verbose)
    try:
        run_command(
            [str(venv_python), "-m", "pip", "install", "build", "pyroma", "twine"],
            verbose=verbose,
        )
    except ValidationError as e:
        print_error(f"Failed to install tools: {e}")
        return 1

    print_success(f"Venv created successfully at {venv_path}")
    return 0


def phase_build(package, repo_root, verbose=False):
    """Build wheel and sdist using venv, copy to root dist/.

    Builds distribution artifacts using the build tool from venv and copies
    them to the root dist/ directory where they can be used as dependencies
    by other packages. Requires that --env has been run first.

    :param package: Package name
    :param repo_root: Path to repository root
    :param verbose: Show detailed output
    :return: 0 on success, 1 on failure, 2 on setup error
    """
    print_step(f"Phase: build - Building {package}", verbose)

    package_dir = repo_root / "sources" / package
    venv_path = package_dir / VALIDATE_VENV_DIR
    dist_dir = package_dir / "dist"

    # Check venv exists
    if not venv_path.exists():
        print_error(f"Venv not found: {venv_path}")
        print_error("Please run --env phase first")
        return 2

    venv_python = venv_path / "bin" / "python"
    if not venv_python.exists():
        print_error(f"Venv python not found: {venv_python}")
        return 2

    # Clean existing dist
    if dist_dir.exists():
        print_info("Removing previous dist directory", verbose)
        shutil.rmtree(dist_dir)

    # Build using venv
    print_info(f"Building with: {venv_python} -m build", verbose)
    try:
        run_command(
            [str(venv_python), "-m", "build", str(package_dir)], verbose=verbose
        )
    except ValidationError as e:
        print_error(f"Build failed: {e}")
        return 1

    # Verify artifacts exist
    if not dist_dir.exists() or not list(dist_dir.glob("*")):
        print_error("Build succeeded but no distributions found")
        return 1

    wheels = list(dist_dir.glob("*.whl"))
    sdists = list(dist_dir.glob("*.tar.gz"))

    if not wheels:
        print_error("No wheel (.whl) file found")
        return 1
    if not sdists:
        print_error("No source distribution (.tar.gz) file found")
        return 1

    wheel_file = wheels[0]
    sdist_file = sdists[0]

    print_success(f"Built wheel: {wheel_file.name}")
    print_success(f"Built sdist: {sdist_file.name}")

    # Copy to root dist/
    root_dist = repo_root / "dist"
    root_dist.mkdir(exist_ok=True)

    print_info(f"Copying artifacts to {root_dist}", verbose)
    try:
        shutil.copy2(wheel_file, root_dist)
        shutil.copy2(sdist_file, root_dist)
    except Exception as e:
        print_error(f"Failed to copy artifacts: {e}")
        return 1

    print_success(f"Copied {wheel_file.name} and {sdist_file.name} to dist/")

    # generate constraints
    print_info("Generating constraints", verbose)
    constraints_path = repo_root / "constraints-validate.txt"
    with open(constraints_path, "w") as f:
        for whl in root_dist.glob("*.whl"):
            parts = whl.name.split("-")
            pkg = parts[0].replace("_", "-")
            version = parts[1]
            f.write(f"{pkg}=={version}\n")
    print_success("Generated constraints to constraints-validate.txt")

    return 0


def phase_check(package, repo_root, pyroma_threshold=8, verbose=False):
    """Run pyroma and twine check on built packages.

    Validates package quality and PyPI compliance using tools from venv.
    Requires that --env and --build have been run first.

    :param package: Package name
    :param repo_root: Path to repository root
    :param pyroma_threshold: Minimum pyroma score (default: 8)
    :param verbose: Show detailed output
    :return: 0 on success, 1 on failure, 2 on setup error
    """
    print_step(f"Phase: check - Validating {package}", verbose)

    package_dir = repo_root / "sources" / package
    venv_path = package_dir / VALIDATE_VENV_DIR
    dist_dir = package_dir / "dist"

    # Check venv exists
    if not venv_path.exists():
        print_error(f"Venv not found: {venv_path}")
        print_error("Please run --env phase first")
        return 2

    # Check dist exists
    if not dist_dir.exists():
        print_error(f"Dist directory not found: {dist_dir}")
        print_error("Please run --build phase first")
        return 2

    venv_python = venv_path / "bin" / "python"

    # Run twine check
    print_info("Running twine check", verbose)
    try:
        run_command(
            [str(venv_python), "-m", "twine", "check", "dist/*"],
            cwd=package_dir,
            verbose=verbose,
        )
    except ValidationError as e:
        print_error(f"Twine check failed: {e}")
        return 1

    print_success("PyPI metadata validation passed (twine)")

    # Run pyroma
    print_info(f"Running pyroma (threshold: {pyroma_threshold}/10)", verbose)
    try:
        output = run_command(
            [str(venv_python), "-m", "pyroma", "."], cwd=package_dir, verbose=verbose
        )

        # Parse pyroma score from output
        score = None
        for line in output.split("\n"):
            if "rating:" in line.lower() and "/10" in line:
                try:
                    score = int(line.split(":")[1].split("/10")[0].strip())
                except (ValueError, IndexError):
                    pass

        if score is not None:
            print_success(f"Pyroma score: {score}/10")
            if score < pyroma_threshold:
                print_error(f"Pyroma score {score} below threshold {pyroma_threshold}")
                return 1
        else:
            print_success("Pyroma check completed (score not parsed)")

    except ValidationError as e:
        # If pyroma fails, show warning but continue
        print(
            f"{Colors.WARNING}Warning: Pyroma check had issues but continuing...{Colors.ENDC}"
        )
        if verbose:
            print(str(e))

    print_success("Quality checks passed")
    return 0


def phase_test(package, repo_root, env_vars, install_from="wheel", verbose=False):
    """Install package from root/dist and run pytest.

    Installs the package from root/dist (NOT from sources) to simulate
    a real PyPI installation, then runs tests. This validates the actual
    release artifact. Requires that --env and --build have been run first.

    :param package: Package name
    :param repo_root: Path to repository root
    :param env_vars: Environment variables to set (from mx.ini)
    :param install_from: Install from 'wheel' or 'sdist' (default: 'wheel')
    :param verbose: Show detailed output
    :return: 0 on success, 1 on failure, 2 on setup error
    """
    print_step(f"Phase: test - Testing {package} (from {install_from})", verbose)

    package_dir = repo_root / "sources" / package
    venv_path = package_dir / VALIDATE_VENV_DIR
    root_dist = repo_root / "dist"

    # Check venv exists
    if not venv_path.exists():
        print_error(f"Venv not found: {venv_path}")
        print_error("Please run --env phase first")
        return 2

    venv_python = venv_path / "bin" / "python"

    # Normalize package name for file matching
    package_normalized = package.replace(".", "_")

    # Find the artifact to install
    def find_artifact(artifact_type):
        if artifact_type == "wheel":
            pattern = f"{package_normalized}-*.whl"
        else:  # sdist
            pattern = f"{package_normalized}-*.tar.gz"
        artifacts = list(root_dist.glob(pattern))
        if not artifacts:
            raise FileNotFoundError(f"No {artifact_type} found for {package}")
        return artifacts[0]

    try:
        artifact_path = find_artifact(install_from)
    except FileNotFoundError as e:
        print_error(str(e))
        print_error("Please run --build phase first")
        return 2

    # Install package from root/dist with --find-links
    # Use --pre to prefer development versions and --upgrade to force reinstall
    print_info(f"Installing {package} from {artifact_path.name}", verbose)

    try:
        run_command(
            [
                str(venv_python),
                "-m",
                "pip",
                "install",
                "--find-links",
                str(root_dist),
                "--pre",  # Allow pre-release/development versions
                "--upgrade",  # Force upgrade to local version if exists
                "-c",
                f"{repo_root}/constraints-validate.txt",
                f"{artifact_path}[test]",
            ],
            verbose=verbose,
        )
    except ValidationError as e:
        print_error(f"Failed to install package: {e}")
        return 1

    print_success(f"Package installed from {install_from}")

    # Set up environment variables for tests
    test_env = os.environ.copy()
    test_env.update(env_vars)

    # Run pytest from the package directory
    print_info("Running pytest", verbose)
    try:
        run_command(
            [str(venv_python), "-m", "pytest", "-v"],
            cwd=package_dir,
            env=test_env,
            verbose=verbose,
        )
    except ValidationError as e:
        print_error(f"Tests failed: {e}")
        return 1

    print_success("All tests passed")
    return 0


def phase_clean(package, repo_root, verbose=False):
    """Remove venv and dist directories.

    Cleans up validation artifacts for the package. Does NOT remove
    artifacts from root dist/ directory.

    :param package: Package name
    :param repo_root: Path to repository root
    :param verbose: Show detailed output
    :return: 0 (always succeeds)
    """
    print_step(f"Phase: clean - Cleaning {package}", verbose)

    package_dir = repo_root / "sources" / package
    venv_path = package_dir / VALIDATE_VENV_DIR
    dist_path = package_dir / "dist"

    cleaned = []

    # Remove venv
    if venv_path.exists():
        print_info(f"Removing venv: {venv_path}", verbose)
        try:
            shutil.rmtree(venv_path)
            cleaned.append("venv")
        except Exception as e:
            print(f"{Colors.WARNING}Warning: Failed to remove venv: {e}{Colors.ENDC}")

    # Remove dist
    if dist_path.exists():
        print_info(f"Removing dist: {dist_path}", verbose)
        try:
            shutil.rmtree(dist_path)
            cleaned.append("dist")
        except Exception as e:
            print(f"{Colors.WARNING}Warning: Failed to remove dist: {e}{Colors.ENDC}")

    if cleaned:
        print_success(f"Cleaned: {', '.join(cleaned)}")
    else:
        print_info("Nothing to clean", verbose)

    return 0


def load_env_vars(repo_root):
    """Load environment variables for test execution."""
    return {
        "TESTRUN_MARKER": "1",
        "LDAP_ADD_BIN": str(repo_root / "openldap" / "bin" / "ldapadd"),
        "LDAP_DELETE_BIN": str(repo_root / "openldap" / "bin" / "ldapdelete"),
        "SLAPD_BIN": str(repo_root / "openldap" / "libexec" / "slapd"),
        "SLAPD_URIS": "ldap://127.0.0.1:12345",
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate a Python package through build, check, and test phases.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="See script docstring for detailed documentation.",
    )

    parser.add_argument("package", help="Package name (must exist in sources/)")

    # Phase selection (mutually exclusive)
    phase_group = parser.add_mutually_exclusive_group(required=True)
    phase_group.add_argument(
        "--env",
        action="store_true",
        help="Create venv and install validation tools (build, pyroma, twine)",
    )
    phase_group.add_argument(
        "--build",
        action="store_true",
        help="Build wheel/sdist using venv and copy to root dist/ (requires --env)",
    )
    phase_group.add_argument(
        "--check",
        action="store_true",
        help="Run pyroma and twine check (requires --env and --build)",
    )
    phase_group.add_argument(
        "--test",
        action="store_true",
        help="Install package from root/dist and run pytest (requires --env and --build)",
    )
    phase_group.add_argument(
        "--clean", action="store_true", help="Remove venv and dist/"
    )
    phase_group.add_argument(
        "--all",
        action="store_true",
        help="Run all phases: env, build, check, test, clean",
    )

    # Configuration options
    parser.add_argument(
        "--pyroma-threshold",
        type=int,
        default=8,
        help="Minimum pyroma score (default: 8)",
    )
    parser.add_argument(
        "--install-from",
        choices=["wheel", "sdist"],
        default="wheel",
        help="Install from wheel or sdist for testing (default: wheel)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed output"
    )

    args = parser.parse_args()

    # Disable colors if not a TTY
    if not sys.stdout.isatty():
        Colors.disable()

    # Get repository root
    repo_root = Path.cwd()

    # Verify package exists
    package_dir = repo_root / "sources" / args.package
    if not package_dir.exists():
        print_error(f"Package directory not found: {package_dir}")
        sys.exit(2)

    # Load environment variables
    env_vars = load_env_vars(repo_root)

    print(f"\n{Colors.BOLD}Validating package: {args.package}{Colors.ENDC}")
    print(f"Package directory: {package_dir}\n")

    # Execute requested phase(s)
    try:
        if args.all:
            # Run all phases in sequence
            phases = [
                ("env", lambda: phase_env(args.package, repo_root, args.verbose)),
                ("build", lambda: phase_build(args.package, repo_root, args.verbose)),
                (
                    "check",
                    lambda: phase_check(
                        args.package, repo_root, args.pyroma_threshold, args.verbose
                    ),
                ),
                (
                    "test",
                    lambda: phase_test(
                        args.package,
                        repo_root,
                        env_vars,
                        args.install_from,
                        args.verbose,
                    ),
                ),
                ("clean", lambda: phase_clean(args.package, repo_root, args.verbose)),
            ]

            for phase_name, phase_func in phases:
                result = phase_func()
                if result != 0:
                    print_error(f'\nPhase "{phase_name}" failed')
                    sys.exit(result if result != 2 else 1)

            print(
                f"\n{Colors.OKGREEN}{Colors.BOLD}✓ All phases completed successfully!{Colors.ENDC}\n"
            )
            sys.exit(0)

        elif args.env:
            result = phase_env(args.package, repo_root, args.verbose)
            sys.exit(result)

        elif args.build:
            result = phase_build(args.package, repo_root, args.verbose)
            sys.exit(result)

        elif args.check:
            result = phase_check(
                args.package, repo_root, args.pyroma_threshold, args.verbose
            )
            sys.exit(result)

        elif args.test:
            result = phase_test(
                args.package, repo_root, env_vars, args.install_from, args.verbose
            )
            sys.exit(result)

        elif args.clean:
            result = phase_clean(args.package, repo_root, args.verbose)
            sys.exit(result)

        else:
            print_error("No phase selected")
            sys.exit(2)

    except KeyboardInterrupt:
        print_error("\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
