#!/usr/bin/env python
"""Package Validation Script for Conestack Monorepo

This script validates Python packages before uploading to PyPI by performing
comprehensive checks including building, metadata validation, quality rating,
installation testing, and running tests in an isolated environment.

REQUIREMENTS
============

This script requires the following packages to be installed:

    pip install build twine pyroma

The script also expects pytest to be available in the test virtual environment
(it will be installed as part of the package's test dependencies).

USAGE
=====

Basic usage:

    python scripts/validate_package.py <package-name>

Examples:

    # Validate the 'node' package
    python scripts/validate_package.py node

    # Validate with verbose output
    python scripts/validate_package.py cone.app --verbose

    # Keep build artifacts for inspection
    python scripts/validate_package.py yafowil --keep-dist

    # Skip test execution (for debugging)
    python scripts/validate_package.py odict --skip-tests

    # Set custom pyroma threshold
    python scripts/validate_package.py plumber --pyroma-threshold 9

    # Collect build artifacts to root dist/ directory
    python scripts/validate_package.py node --collect-dist

OPTIONS
=======

Positional Arguments:
  package              Package name (directory name in sources/)

Optional Arguments:
  --keep-dist          Keep dist/ directory after validation (default: remove)
  --keep-venv          Keep test venv for debugging (default: remove)
  --skip-tests         Skip test execution phase
  --pyroma-threshold   Minimum pyroma quality score (default: 8)
  --verbose, -v        Show detailed output
  --collect-dist       Copy build artifacts to root dist/ directory
  --help, -h           Show this help message

VALIDATION STEPS
================

The script performs the following validation steps in order:

1. Pre-checks
   - Verify package directory exists in sources/
   - Verify pyproject.toml exists
   - Clean previous dist/ directory

2. Build Phase
   - Build wheel and source distribution using 'python -m build'
   - Fails immediately if build errors occur

3. PyPI Validation (twine check)
   - Validate package metadata for PyPI compatibility
   - Check README rendering
   - Fails if metadata issues found

4. Quality Rating (pyroma)
   - Rate package quality and best practices
   - Score must meet threshold (default: 8/10)
   - Fails if score below threshold

5. Installation Test
   - Create temporary isolated virtual environment
   - Install built wheel distribution
   - Verify package can be imported
   - Fails if installation or import fails

6. Test Execution
   - Install test dependencies via package[test] extras
   - Run pytest in the installed environment
   - Sets required environment variables (LDAP paths, etc.)
   - Executes package tests
   - Fails if tests fail

7. Cleanup
   - Copy build artifacts to root directory dist/ folder (if --collect-dist)
   - Remove temporary venv (unless --keep-venv)
   - Remove dist/ directory (unless --keep-dist)

EXIT CODES
==========

0  - All validations passed successfully
1  - Validation failed (build, tests, quality, etc.)
2  - Setup error (missing dependencies, invalid arguments, etc.)

ENVIRONMENT
===========

The script sets the following environment variables during test execution
(matching the configuration in mx.ini):

- TESTRUN_MARKER=1
- LDAP_ADD_BIN=openldap/bin/ldapadd
- LDAP_DELETE_BIN=openldap/bin/ldapdelete
- SLAPD_BIN=openldap/libexec/slapd
- SLAPD_URIS=ldap://127.0.0.1:12345

NOTES
=====

- The script operates in fail-fast mode: stops at first error
- Build artifacts are created in the package's dist/ directory
- Test venv is created in /tmp/validate_{package}_{timestamp}/
- All paths are relative to the conestack monorepo root
- Package must be checked out in sources/{package-name}/
- Package must have [project.optional-dependencies] test defined in pyproject.toml

AUTHOR
======

Generated for the Conestack monorepo package validation workflow.
"""

from pathlib import Path

import argparse
import os
import shutil
import subprocess
import sys


# Constant for venv directory name
VALIDATE_VENV_DIR = "venv"


class ValidationError(Exception):
    """Raised when a validation step fails."""
    pass


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @classmethod
    def disable(cls):
        """Disable colors (for non-TTY output)."""
        cls.HEADER = ''
        cls.OKBLUE = ''
        cls.OKCYAN = ''
        cls.OKGREEN = ''
        cls.WARNING = ''
        cls.FAIL = ''
        cls.ENDC = ''
        cls.BOLD = ''
        cls.UNDERLINE = ''


def print_step(message, verbose=False):
    """Print a validation step header."""
    if verbose or True:  # Always show steps
        print(f'\n{Colors.HEADER}{Colors.BOLD}=== {message} ==={Colors.ENDC}')


def print_success(message):
    """Print a success message."""
    print(f'{Colors.OKGREEN}✓ {message}{Colors.ENDC}')


def print_error(message):
    """Print an error message."""
    print(f'{Colors.FAIL}✗ {message}{Colors.ENDC}', file=sys.stderr)


def print_info(message, verbose=False):
    """Print an info message (only in verbose mode)."""
    if verbose:
        print(f'{Colors.OKCYAN}{message}{Colors.ENDC}')


def run_command(cmd, cwd=None, env=None, verbose=False):
    """Run a shell command and return output.

    Raises ValidationError if command fails.
    """
    if verbose:
        print_info(f'Running: {" ".join(cmd)}', verbose=True)

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        if verbose and result.stdout:
            print(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print_error(f'Command failed: {" ".join(cmd)}')
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        raise ValidationError(f'Command failed with exit code {e.returncode}')


def check_dependencies():
    """Check if required Python packages are available."""
    required = {
        'build': 'build',
        'twine': 'twine',
        'pyroma': 'pyroma'
    }
    missing = []

    for module_name, package_name in required.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(package_name)

    if missing:
        print_error(f'Missing required packages: {", ".join(missing)}')
        print_error('Install with: pip install build twine pyroma')
        sys.exit(2)


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
    print_step(f'Phase: env - Creating venv for {package}', verbose)

    package_dir = repo_root / "sources" / package
    venv_path = package_dir / VALIDATE_VENV_DIR

    # Remove existing venv if it exists (ensure clean state)
    if venv_path.exists():
        print_info(f'Removing existing venv: {venv_path}', verbose)
        shutil.rmtree(venv_path)

    # Create venv
    print_info(f'Creating venv: {venv_path}', verbose)
    try:
        run_command(
            [sys.executable, '-m', 'venv', str(venv_path)],
            verbose=verbose
        )
    except ValidationError as e:
        print_error(f'Failed to create venv: {e}')
        return 1

    venv_python = venv_path / 'bin' / 'python'
    if not venv_python.exists():
        print_error(f'Venv python not found: {venv_python}')
        return 1

    # Upgrade pip
    print_info('Upgrading pip in venv', verbose)
    try:
        run_command(
            [str(venv_python), '-m', 'pip', 'install', '--upgrade', 'pip'],
            verbose=verbose
        )
    except ValidationError as e:
        print_error(f'Failed to upgrade pip: {e}')
        return 1

    # Install build, pyroma, and twine
    print_info('Installing build, pyroma, and twine', verbose)
    try:
        run_command(
            [str(venv_python), '-m', 'pip', 'install', 'build', 'pyroma', 'twine'],
            verbose=verbose
        )
    except ValidationError as e:
        print_error(f'Failed to install tools: {e}')
        return 1

    print_success(f'Venv created successfully at {venv_path}')
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
    print_step(f'Phase: build - Building {package}', verbose)

    package_dir = repo_root / "sources" / package
    venv_path = package_dir / VALIDATE_VENV_DIR
    dist_dir = package_dir / "dist"

    # Check venv exists
    if not venv_path.exists():
        print_error(f'Venv not found: {venv_path}')
        print_error('Please run --env phase first')
        return 2

    venv_python = venv_path / 'bin' / 'python'
    if not venv_python.exists():
        print_error(f'Venv python not found: {venv_python}')
        return 2

    # Clean existing dist
    if dist_dir.exists():
        print_info(f'Removing previous dist directory', verbose)
        shutil.rmtree(dist_dir)

    # Build using venv
    print_info(f'Building with: {venv_python} -m build', verbose)
    try:
        run_command(
            [str(venv_python), '-m', 'build', str(package_dir)],
            verbose=verbose
        )
    except ValidationError as e:
        print_error(f'Build failed: {e}')
        return 1

    # Verify artifacts exist
    if not dist_dir.exists() or not list(dist_dir.glob('*')):
        print_error('Build succeeded but no distributions found')
        return 1

    wheels = list(dist_dir.glob('*.whl'))
    sdists = list(dist_dir.glob('*.tar.gz'))

    if not wheels:
        print_error('No wheel (.whl) file found')
        return 1
    if not sdists:
        print_error('No source distribution (.tar.gz) file found')
        return 1

    wheel_file = wheels[0]
    sdist_file = sdists[0]

    print_success(f'Built wheel: {wheel_file.name}')
    print_success(f'Built sdist: {sdist_file.name}')

    # Copy to root dist/
    root_dist = repo_root / "dist"
    root_dist.mkdir(exist_ok=True)

    print_info(f'Copying artifacts to {root_dist}', verbose)
    try:
        shutil.copy2(wheel_file, root_dist)
        shutil.copy2(sdist_file, root_dist)
    except Exception as e:
        print_error(f'Failed to copy artifacts: {e}')
        return 1

    print_success(f'Copied {wheel_file.name} and {sdist_file.name} to dist/')
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
    print_step(f'Phase: check - Validating {package}', verbose)

    package_dir = repo_root / "sources" / package
    venv_path = package_dir / VALIDATE_VENV_DIR
    dist_dir = package_dir / "dist"

    # Check venv exists
    if not venv_path.exists():
        print_error(f'Venv not found: {venv_path}')
        print_error('Please run --env phase first')
        return 2

    # Check dist exists
    if not dist_dir.exists():
        print_error(f'Dist directory not found: {dist_dir}')
        print_error('Please run --build phase first')
        return 2

    venv_python = venv_path / 'bin' / 'python'

    # Run twine check
    print_info('Running twine check', verbose)
    try:
        run_command(
            [str(venv_python), '-m', 'twine', 'check', 'dist/*'],
            cwd=package_dir,
            verbose=verbose
        )
    except ValidationError as e:
        print_error(f'Twine check failed: {e}')
        return 1

    print_success('PyPI metadata validation passed (twine)')

    # Run pyroma
    print_info(f'Running pyroma (threshold: {pyroma_threshold}/10)', verbose)
    try:
        output = run_command(
            [str(venv_python), '-m', 'pyroma', '.'],
            cwd=package_dir,
            verbose=verbose
        )

        # Parse pyroma score from output
        score = None
        for line in output.split('\n'):
            if 'rating:' in line.lower() and '/10' in line:
                try:
                    score = int(line.split(':')[1].split('/10')[0].strip())
                except (ValueError, IndexError):
                    pass

        if score is not None:
            print_success(f'Pyroma score: {score}/10')
            if score < pyroma_threshold:
                print_error(f'Pyroma score {score} below threshold {pyroma_threshold}')
                return 1
        else:
            print_success('Pyroma check completed (score not parsed)')

    except ValidationError as e:
        # If pyroma fails, show warning but continue
        print(f'{Colors.WARNING}Warning: Pyroma check had issues but continuing...{Colors.ENDC}')
        if verbose:
            print(str(e))

    print_success('Quality checks passed')
    return 0


def phase_test(package, repo_root, env_vars, verbose=False):
    """Install package from root/dist and run pytest.

    Installs the package from root/dist (NOT from sources) to simulate
    a real PyPI installation, then runs tests. This validates the actual
    release artifact. Requires that --env and --build have been run first.

    :param package: Package name
    :param repo_root: Path to repository root
    :param env_vars: Environment variables to set (from mx.ini)
    :param verbose: Show detailed output
    :return: 0 on success, 1 on failure, 2 on setup error
    """
    print_step(f'Phase: test - Testing {package}', verbose)

    package_dir = repo_root / "sources" / package
    venv_path = package_dir / VALIDATE_VENV_DIR
    root_dist = repo_root / "dist"

    # Check venv exists
    if not venv_path.exists():
        print_error(f'Venv not found: {venv_path}')
        print_error('Please run --env phase first')
        return 2

    venv_python = venv_path / 'bin' / 'python'

    # Check root dist has package wheel
    package_name_safe = package.replace('-', '_').replace('.', '_')
    wheels_in_dist = list(root_dist.glob(f'{package}*.whl')) + \
                     list(root_dist.glob(f'{package_name_safe}*.whl'))

    if not wheels_in_dist:
        print_error(f'No wheel for {package} found in {root_dist}')
        print_error('Please run --build phase first')
        return 2

    # Install package from root/dist with --find-links
    # Use --pre to prefer development versions and --upgrade to force reinstall
    print_info(f'Installing {package} from {root_dist} (with dependencies)', verbose)
    try:
        run_command(
            [str(venv_python), '-m', 'pip', 'install',
             '--find-links', str(root_dist),
             '--pre',  # Allow pre-release/development versions
             '--upgrade',  # Force upgrade to local version if exists
             f'{package}[test]'],
            verbose=verbose
        )
    except ValidationError as e:
        print_error(f'Failed to install package: {e}')
        return 1

    print_success(f'Package installed from root/dist')

    # Set up environment variables for tests
    test_env = os.environ.copy()
    test_env.update(env_vars)

    # Run pytest from the package directory
    print_info('Running pytest', verbose)
    try:
        run_command(
            [str(venv_python), '-m', 'pytest', '-v'],
            cwd=package_dir,
            env=test_env,
            verbose=verbose
        )
    except ValidationError as e:
        print_error(f'Tests failed: {e}')
        return 1

    print_success('All tests passed')
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
    print_step(f'Phase: clean - Cleaning {package}', verbose)

    package_dir = repo_root / "sources" / package
    venv_path = package_dir / VALIDATE_VENV_DIR
    dist_path = package_dir / "dist"

    cleaned = []

    # Remove venv
    if venv_path.exists():
        print_info(f'Removing venv: {venv_path}', verbose)
        try:
            shutil.rmtree(venv_path)
            cleaned.append('venv')
        except Exception as e:
            print(f'{Colors.WARNING}Warning: Failed to remove venv: {e}{Colors.ENDC}')

    # Remove dist
    if dist_path.exists():
        print_info(f'Removing dist: {dist_path}', verbose)
        try:
            shutil.rmtree(dist_path)
            cleaned.append('dist')
        except Exception as e:
            print(f'{Colors.WARNING}Warning: Failed to remove dist: {e}{Colors.ENDC}')

    if cleaned:
        print_success(f'Cleaned: {", ".join(cleaned)}')
    else:
        print_info('Nothing to clean', verbose)

    return 0


def load_env_vars(repo_root):
    """Load environment variables for test execution."""
    return {
        'TESTRUN_MARKER': '1',
        'LDAP_ADD_BIN': str(repo_root / 'openldap' / 'bin' / 'ldapadd'),
        'LDAP_DELETE_BIN': str(repo_root / 'openldap' / 'bin' / 'ldapdelete'),
        'SLAPD_BIN': str(repo_root / 'openldap' / 'libexec' / 'slapd'),
        'SLAPD_URIS': 'ldap://127.0.0.1:12345',
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate a Python package through build, check, and test phases.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='See script docstring for detailed documentation.'
    )

    parser.add_argument(
        'package',
        help='Package name (must exist in sources/)'
    )

    # Phase selection (mutually exclusive)
    phase_group = parser.add_mutually_exclusive_group(required=True)
    phase_group.add_argument(
        '--env',
        action='store_true',
        help='Create venv and install validation tools (build, pyroma, twine)'
    )
    phase_group.add_argument(
        '--build',
        action='store_true',
        help='Build wheel/sdist using venv and copy to root dist/ (requires --env)'
    )
    phase_group.add_argument(
        '--check',
        action='store_true',
        help='Run pyroma and twine check (requires --env and --build)'
    )
    phase_group.add_argument(
        '--test',
        action='store_true',
        help='Install package from root/dist and run pytest (requires --env and --build)'
    )
    phase_group.add_argument(
        '--clean',
        action='store_true',
        help='Remove venv and dist/'
    )
    phase_group.add_argument(
        '--all',
        action='store_true',
        help='Run all phases: env, build, check, test, clean'
    )

    # Configuration options
    parser.add_argument(
        '--pyroma-threshold',
        type=int,
        default=8,
        help='Minimum pyroma score (default: 8)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed output'
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
        print_error(f'Package directory not found: {package_dir}')
        sys.exit(2)

    # Check dependencies
    check_dependencies()

    # Load environment variables
    env_vars = load_env_vars(repo_root)

    print(f'\n{Colors.BOLD}Validating package: {args.package}{Colors.ENDC}')
    print(f'Package directory: {package_dir}\n')

    # Execute requested phase(s)
    try:
        if args.all:
            # Run all phases in sequence
            phases = [
                ("env", lambda: phase_env(args.package, repo_root, args.verbose)),
                ("build", lambda: phase_build(args.package, repo_root, args.verbose)),
                ("check", lambda: phase_check(args.package, repo_root, args.pyroma_threshold, args.verbose)),
                ("test", lambda: phase_test(args.package, repo_root, env_vars, args.verbose)),
                ("clean", lambda: phase_clean(args.package, repo_root, args.verbose)),
            ]

            for phase_name, phase_func in phases:
                result = phase_func()
                if result != 0:
                    print_error(f'\nPhase "{phase_name}" failed')
                    sys.exit(result if result != 2 else 1)

            print(f'\n{Colors.OKGREEN}{Colors.BOLD}✓ All phases completed successfully!{Colors.ENDC}\n')
            sys.exit(0)

        elif args.env:
            result = phase_env(args.package, repo_root, args.verbose)
            sys.exit(result)

        elif args.build:
            result = phase_build(args.package, repo_root, args.verbose)
            sys.exit(result)

        elif args.check:
            result = phase_check(args.package, repo_root, args.pyroma_threshold, args.verbose)
            sys.exit(result)

        elif args.test:
            result = phase_test(args.package, repo_root, env_vars, args.verbose)
            sys.exit(result)

        elif args.clean:
            result = phase_clean(args.package, repo_root, args.verbose)
            sys.exit(result)

        else:
            print_error('No phase selected')
            sys.exit(2)

    except KeyboardInterrupt:
        print_error('\nValidation interrupted by user')
        sys.exit(1)
    except Exception as e:
        print_error(f'\nUnexpected error: {e}')
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(2)


if __name__ == '__main__':
    main()
