Package Validation
==================

The conestack monorepo includes a package validation system that ensures all packages
are ready for release to PyPI. The validation tests actual built artifacts (wheels and
sdists), not source code, simulating what users will receive when installing from PyPI.


Purpose
-------

The validation system serves several purposes:

1. **Build Verification**: Ensures packages build correctly as wheels and source distributions
2. **Quality Checks**: Validates package metadata and PyPI compliance using pyroma and twine
3. **Artifact Testing**: Tests the actual release artifacts, not source code
4. **Dependency Resolution**: Validates that packages work together using pre-built artifacts
5. **Release Readiness**: Confirms packages are ready for publication to PyPI


Validation Script
-----------------

The validation is performed by ``scripts/validate_package.py``, which supports
modular phase-based validation.

Phases
~~~~~~

The script supports the following phases:

``--env``
    Create a virtual environment and install build/validation tools (build, pyroma, twine).
    The venv is created at ``sources/<package>/venv/``.

``--build``
    Build wheel and sdist using the venv's build tool and copy artifacts to the
    root ``dist/`` directory. This makes packages available for cross-package dependencies.

``--check``
    Run quality validation using twine check and pyroma. Validates PyPI metadata
    compliance and package quality rating.

``--test``
    Install the package from ``dist/`` (not from sources) and run pytest.
    This validates the actual release artifact that users will receive.
    Supports ``--install-from wheel`` (default) or ``--install-from sdist``.

    **Important**: The package code is installed from the built artifact, but
    tests are executed from the source checkout directory. See
    `Test Execution Model`_ for details.

``--clean``
    Remove the package's venv and local dist directory.

``--all``
    Run all phases in sequence: env → build → check → test → clean.


Usage Examples
~~~~~~~~~~~~~~

.. code-block:: bash

    # Full validation workflow for a single package
    python scripts/validate_package.py node --all

    # Manual step-by-step validation
    python scripts/validate_package.py node --env
    python scripts/validate_package.py node --build
    python scripts/validate_package.py node --check
    python scripts/validate_package.py node --test
    python scripts/validate_package.py node --clean

    # Test using sdist instead of wheel
    python scripts/validate_package.py node --test --install-from sdist

    # Full validation with sdist testing
    python scripts/validate_package.py node --all --install-from sdist

    # Verbose output
    python scripts/validate_package.py cone.app --all -v

    # Custom pyroma threshold (default: 8)
    python scripts/validate_package.py plumber --all --pyroma-threshold 9


Configuration Options
~~~~~~~~~~~~~~~~~~~~~

``--pyroma-threshold N``
    Minimum pyroma quality score (default: 8, max: 10)

``--install-from TYPE``
    Install from ``wheel`` or ``sdist`` for testing (default: wheel)

``-v, --verbose``
    Show detailed output including command execution


Exit Codes
~~~~~~~~~~

- **0**: Phase completed successfully
- **1**: Phase failed (build error, test failure, quality below threshold)
- **2**: Setup error (missing venv, missing dist, invalid package)


Make Targets
------------

The following make targets are available for batch validation of all packages:

``make validate-env``
    Create venvs for all packages.

``make validate-build``
    Build all packages and copy artifacts to ``dist/``.
    Also generates ``constraints-validate.txt`` for version pinning.

``make validate-check``
    Run pyroma and twine check on all packages.

``make validate-test-wheel``
    Test all packages by installing from wheels.
    Excludes packages in the test blacklist.

``make validate-test-sdist``
    Test all packages by installing from sdists.
    Excludes packages in the test blacklist.

``make validate-compare``
    Compare wheel and sdist contents for all packages.
    Reports files that are in one artifact but not the other.

``make validate-clean``
    Clean all validation artifacts (venvs, dist directories, logs).

``make validate-all``
    Run the complete validation QA chain in sequence:
    env → build → compare → check → test-wheel → test-sdist → clean.
    Stops on first failure.


Typical Workflow
~~~~~~~~~~~~~~~~

For a complete validation of all packages before release:

.. code-block:: bash

    # Run the complete QA chain (recommended)
    make validate-all

Or run individual steps:

.. code-block:: bash

    # 1. Create venvs for all packages
    make validate-env

    # 2. Build all packages
    make validate-build

    # 3. Compare artifact contents
    make validate-compare

    # 4. Check package quality
    make validate-check

    # 5. Test from wheels
    make validate-test-wheel

    # 6. Test from sdists
    make validate-test-sdist

    # 7. Clean up
    make validate-clean


Test Blacklist
--------------

Some packages are excluded from test validation (defined in ``include.mk``):

- ``cone.three`` - No tests
- ``treibstoff`` - JavaScript package, tests run differently
- ``yafowil-example-helloworld`` - Example package
- ``yafowil.demo`` - Demo application
- ``yafowil.documentation`` - Documentation package
- ``yafowil.webob`` - No test dependencies defined

These packages still go through env, build, and check phases.


Sequential Test Packages
------------------------

The following packages require a local OpenLDAP server for testing and must run
sequentially (not in parallel):

- ``cone.ldap``
- ``node.ext.ldap``

These are defined in ``VALIDATE_SEQUENTIAL_TESTS`` in ``include.mk``.

The ``validate-test-wheel`` and ``validate-test-sdist`` targets automatically handle
this by first running all other packages in parallel, then running sequential packages
one at a time.


Environment Variables
---------------------

The test phase sets the following environment variables (matching ``mx.ini`` configuration):

- ``TESTRUN_MARKER=1``
- ``LDAP_ADD_BIN=openldap/bin/ldapadd``
- ``LDAP_DELETE_BIN=openldap/bin/ldapdelete``
- ``SLAPD_BIN=openldap/libexec/slapd``
- ``SLAPD_URIS=ldap://127.0.0.1:12345``

These are required for packages that have LDAP-related tests.


Test Execution Model
--------------------

The validation system uses a hybrid approach for testing:

- **Package code**: Installed from the built artifact (wheel or sdist) into the venv
- **Test code**: Executed from the source checkout directory (``sources/<package>/``)

This design is intentional:

1. It validates that the actual release artifact works correctly
2. It allows using the latest test code without rebuilding
3. It prepares for a future change where tests will be moved to package root
   folders (outside ``src/``) and excluded from wheel/sdist builds

When pytest runs, it imports the package from the venv (the installed artifact),
but discovers and runs test files from the source checkout. This ensures:

- The installed package API is what gets tested
- Test fixtures and utilities from the source tree are available
- Tests don't need to be included in release artifacts


Artifact Comparison
-------------------

The ``scripts/compare_artifacts.py`` script compares wheel and sdist contents
for all packages in ``dist/``. It helps identify:

- Files in wheel but not in sdist (unexpected)
- Files in sdist but not in wheel (may need exclusion)

Usage
~~~~~

.. code-block:: bash

    # After building packages
    make validate-build

    # Compare all artifacts
    make validate-compare

The script automatically filters expected differences:

- ``.gitignore`` files (expected in sdist only)
- Metadata files (PKG-INFO, pyproject.toml, etc.)
- Documentation files (README, LICENSE, CHANGES, etc.)
- Test files (excluded from comparison)

Common Issues
~~~~~~~~~~~~~

Files that commonly appear as differences:

**cfg/*.xml files**
    Test configuration files in cone.ldap, cone.ugm. Should be excluded
    from sdist via ``[tool.hatch.build]`` excludes in pyproject.toml.

**.travis.yml, Makefile, MANIFEST.in**
    Obsolete files that should be removed from the repository or excluded.

**Nested .gitignore files**
    Sometimes included in wheels when in package subdirectories
    (e.g., static asset directories).


Key Design Points
-----------------

1. **Artifact Testing**: The ``--test`` phase installs from ``dist/`` (the built wheel or
   sdist), NOT from sources. This simulates a real PyPI installation.

2. **Test Separation**: Tests run from source checkout against the installed package.
   This validates the release artifact while keeping tests in the development tree.

3. **Cross-Package Dependencies**: All pip installs use ``--find-links`` pointing to
   ``dist/``, allowing packages to depend on pre-built versions of sibling packages.

4. **Constraints File**: The build phase generates ``constraints-validate.txt`` to ensure
   consistent versions across all package installations.

5. **Parallel Execution**: Make targets run package validations in parallel for efficiency.
   Logs are written to ``/tmp/conestack-dev/validate_<package>.log``.

6. **Development Versions**: Uses pip's ``--pre`` and ``--upgrade`` flags to prefer
   development versions (e.g., ``2.0.0.dev0``) over published versions.
