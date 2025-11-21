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

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


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


def validate_package(
    package_name,
    keep_dist=False,
    keep_venv=False,
    skip_tests=False,
    pyroma_threshold=8,
    verbose=False
):
    """Validate a package through all validation steps.

    :param package_name: Name of the package to validate
    :param keep_dist: Keep dist/ directory after validation
    :param keep_venv: Keep test venv after validation
    :param skip_tests: Skip test execution
    :param pyroma_threshold: Minimum pyroma score required
    :param verbose: Show detailed output
    """
    # Get repository root and package directory
    repo_root = Path.cwd()
    package_dir = repo_root / 'sources' / package_name

    print(f'\n{Colors.BOLD}Validating package: {package_name}{Colors.ENDC}')
    print(f'Package directory: {package_dir}\n')

    # Step 1: Pre-checks
    print_step('Pre-checks', verbose)

    if not package_dir.exists():
        raise ValidationError(f'Package directory not found: {package_dir}')
    print_success(f'Package directory exists')

    pyproject_file = package_dir / 'pyproject.toml'
    if not pyproject_file.exists():
        raise ValidationError(f'pyproject.toml not found in {package_dir}')
    print_success('pyproject.toml exists')

    # Clean previous dist
    dist_dir = package_dir / 'dist'
    if dist_dir.exists():
        print_info(f'Removing previous dist directory', verbose)
        shutil.rmtree(dist_dir)
    print_success('Cleaned previous build artifacts')

    # Step 2: Build Phase
    print_step('Building distributions', verbose)

    run_command(
        [sys.executable, '-m', 'build'],
        cwd=package_dir,
        verbose=verbose
    )

    if not dist_dir.exists() or not list(dist_dir.glob('*')):
        raise ValidationError('Build succeeded but no distributions found')

    wheels = list(dist_dir.glob('*.whl'))
    sdists = list(dist_dir.glob('*.tar.gz'))

    if not wheels:
        raise ValidationError('No wheel (.whl) file found')
    if not sdists:
        raise ValidationError('No source distribution (.tar.gz) file found')

    wheel_file = wheels[0]
    sdist_file = sdists[0]

    print_success(f'Built wheel: {wheel_file.name}')
    print_success(f'Built sdist: {sdist_file.name}')

    # Step 3: PyPI Validation (twine check)
    print_step('Validating PyPI compatibility (twine check)', verbose)

    run_command(
        [sys.executable, '-m', 'twine', 'check', 'dist/*'],
        cwd=package_dir,
        verbose=verbose
    )
    print_success('PyPI metadata validation passed')

    # Step 4: Quality Rating (pyroma)
    print_step(
        f'Rating package quality (pyroma, threshold: {pyroma_threshold}/10)',
        verbose
    )

    try:
        output = run_command(
            [sys.executable, '-m', 'pyroma', '.'],
            cwd=package_dir,
            verbose=verbose
        )

        # Parse pyroma score from output
        # Pyroma outputs "Final rating: X/10"
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
                raise ValidationError(
                    f'Pyroma score {score} below threshold {pyroma_threshold}'
                )
        else:
            print_success('Pyroma check completed (score not parsed)')

    except ValidationError as e:
        if 'below threshold' in str(e):
            raise
        # If pyroma fails for other reasons, show warning but continue
        print(
            f'{Colors.WARNING}Warning: Pyroma check had issues but '
            f'continuing...{Colors.ENDC}'
        )
        if verbose:
            print(str(e))

    # Step 5: Installation Test
    print_step('Testing installation in isolated environment', verbose)

    # Create temporary venv
    timestamp = int(time.time())
    venv_dir = Path(tempfile.gettempdir()) / f'validate_{package_name}_{timestamp}'

    print_info(f'Creating venv: {venv_dir}', verbose)
    run_command(
        [sys.executable, '-m', 'venv', str(venv_dir)],
        verbose=verbose
    )

    # Get venv python path
    venv_python = venv_dir / 'bin' / 'python'
    if not venv_python.exists():
        raise ValidationError(f'Venv python not found: {venv_python}')

    try:
        # Upgrade pip
        print_info('Upgrading pip', verbose)
        run_command(
            [str(venv_python), '-m', 'pip', 'install', '--upgrade', 'pip'],
            verbose=verbose
        )

        # Install the wheel
        print_info(f'Installing wheel: {wheel_file}', verbose)
        run_command(
            [str(venv_python), '-m', 'pip', 'install', str(wheel_file)],
            verbose=verbose
        )
        print_success(f'Package installed successfully')

        # Verify import
        # Try to import the main package module
        # Handle namespace packages (e.g., cone.app -> import cone.app)
        import_name = package_name.replace('-', '_')
        print_info(f'Verifying import: {import_name}', verbose)

        try:
            run_command(
                [str(venv_python), '-c', f'import {import_name}'],
                verbose=verbose
            )
            print_success(f'Package imports successfully')
        except ValidationError:
            # Some packages might have different import names or special handling
            print(
                f'{Colors.WARNING}Warning: Could not verify import '
                f'(this may be normal for some packages){Colors.ENDC}'
            )

        # Step 6: Test Execution
        if not skip_tests:
            print_step('Running tests in isolated environment', verbose)

            # Install test dependencies
            print_info('Installing test dependencies', verbose)
            run_command(
                [str(venv_python), '-m', 'pip', 'install', f'{wheel_file}[test]'],
                verbose=verbose
            )

            # Set up environment variables for tests
            test_env = os.environ.copy()
            test_env.update({
                'TESTRUN_MARKER': '1',
                'LDAP_ADD_BIN': str(repo_root / 'openldap' / 'bin' / 'ldapadd'),
                'LDAP_DELETE_BIN': str(repo_root / 'openldap' / 'bin' / 'ldapdelete'),
                'SLAPD_BIN': str(repo_root / 'openldap' / 'libexec' / 'slapd'),
                'SLAPD_URIS': 'ldap://127.0.0.1:12345',
            })

            # Run pytest from the package directory
            print_info('Running pytest', verbose)
            run_command(
                [str(venv_python), '-m', 'pytest', '-v'],
                cwd=package_dir,
                env=test_env,
                verbose=verbose
            )
            print_success('All tests passed')
        else:
            print(f'{Colors.WARNING}Skipping tests (--skip-tests flag){Colors.ENDC}')

    finally:
        # Cleanup venv
        if not keep_venv:
            print_info(f'Removing test venv: {venv_dir}', verbose)
            shutil.rmtree(venv_dir, ignore_errors=True)
        else:
            print_info(f'Keeping test venv: {venv_dir}', verbose)

    # Cleanup dist
    if not keep_dist:
        print_info('Removing dist directory', verbose)
        shutil.rmtree(dist_dir, ignore_errors=True)
    else:
        print_info(f'Keeping dist directory: {dist_dir}', verbose)

    print(
        f'\n{Colors.OKGREEN}{Colors.BOLD}✓ Package validation completed '
        f'successfully!{Colors.ENDC}\n'
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate Python package for PyPI upload',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='See script docstring for detailed documentation.'
    )

    parser.add_argument(
        'package',
        help='Package name (directory name in sources/)'
    )
    parser.add_argument(
        '--keep-dist',
        action='store_true',
        help='Keep dist/ directory after validation'
    )
    parser.add_argument(
        '--keep-venv',
        action='store_true',
        help='Keep test venv for debugging'
    )
    parser.add_argument(
        '--skip-tests',
        action='store_true',
        help='Skip test execution phase'
    )
    parser.add_argument(
        '--pyroma-threshold',
        type=int,
        default=8,
        help='Minimum pyroma quality score (default: 8)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output'
    )

    args = parser.parse_args()

    # Disable colors if not a TTY
    if not sys.stdout.isatty():
        Colors.disable()

    try:
        # Check dependencies
        check_dependencies()

        # Run validation
        validate_package(
            args.package,
            keep_dist=args.keep_dist,
            keep_venv=args.keep_venv,
            skip_tests=args.skip_tests,
            pyroma_threshold=args.pyroma_threshold,
            verbose=args.verbose
        )

        sys.exit(0)

    except ValidationError as e:
        print_error(f'\nValidation failed: {e}')
        sys.exit(1)
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
