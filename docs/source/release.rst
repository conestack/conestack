Release Process
===============

Overview
--------

This document describes the release process for Conestack packages using
zest.releaser for automated version management and PyPI uploads.

Prerequisites
-------------

Required Tools
~~~~~~~~~~~~~~

**zest.releaser**: Install in the monorepo venv:

.. code-block:: bash

    ./venv/bin/pip install zest.releaser[recommended]

PyPI Configuration
~~~~~~~~~~~~~~~~~~

Configure ``~/.pypirc`` with your PyPI credentials:

.. code-block:: ini

    [distutils]
    index-servers =
        pypi

    [pypi]
    username = __token__
    password = pypi-YOUR-API-TOKEN

Pre-Release Validation
~~~~~~~~~~~~~~~~~~~~~~

Before releasing, ensure all packages pass validation:

.. code-block:: bash

    make validate-all

Automated Release
-----------------

Using the Release Script
~~~~~~~~~~~~~~~~~~~~~~~~

Release all packages with unreleased changes:

.. code-block:: bash

    ./venv/bin/python scripts/release_packages.py

Script Options
~~~~~~~~~~~~~~

::

    usage: release_packages.py [options]

    options:
      --dry-run         Show what would be released without doing it
      --list            List packages needing release and exit
      --package PKG     Release only specified package (can be repeated)
      --skip PKG        Skip specified package (can be repeated)
      --no-upload       Prepare release but don't upload to PyPI
      -v, --verbose     Verbose output

Examples
~~~~~~~~

.. code-block:: bash

    # Preview what will be released
    ./venv/bin/python scripts/release_packages.py --dry-run

    # List packages needing release
    ./venv/bin/python scripts/release_packages.py --list

    # Release specific packages only
    ./venv/bin/python scripts/release_packages.py --package node --package odict

    # Release all except specific packages
    ./venv/bin/python scripts/release_packages.py --skip cone.ldap

    # Prepare releases without uploading
    ./venv/bin/python scripts/release_packages.py --no-upload

Manual Release (Single Package)
-------------------------------

For releasing a single package manually:

.. code-block:: bash

    cd sources/<package>
    fullrelease

This will interactively:

1. Update version in pyproject.toml
2. Update CHANGES.rst (remove "(unreleased)", add date)
3. Commit changes
4. Create git tag
5. Build wheel and sdist
6. Upload to PyPI
7. Bump to next development version

Release Order
-------------

Packages are released in dependency order by group:

.. list-table::
   :header-rows: 1
   :widths: 10 30 60

   * - Order
     - Group
     - Packages
   * - 1
     - Base packages
     - odict, plumber, webresource, treibstoff
   * - 2
     - Node packages
     - node, node.ext.*
   * - 3
     - YAFOWIL packages
     - yafowil, yafowil.*, yafowil.widget.*
   * - 4
     - Cone tile
     - cone.tile
   * - 5
     - Cone app
     - cone.app
   * - 6
     - Cone packages
     - cone.*

Detection Logic
---------------

A package needs release when its CHANGES.rst contains:

- A version section marked ``(unreleased)``
- Actual change entries under that section

Packages are skipped if:

- No CHANGES.rst file exists
- The unreleased section contains "No changes yet"

Post-Release Verification
-------------------------

After release, verify packages on PyPI:

.. code-block:: bash

    # Check package is available
    pip index versions <package>

    # Test installation
    pip install <package>==<version>

Troubleshooting
---------------

Release Failed Mid-Way
~~~~~~~~~~~~~~~~~~~~~~

If a release fails after committing but before upload:

1. Check git status in the package directory
2. Manually upload: ``twine upload dist/*``
3. Or reset and retry: ``git reset --hard HEAD~2``

PyPI Upload Errors
~~~~~~~~~~~~~~~~~~

- **403 Forbidden**: Check ~/.pypirc credentials
- **400 Bad Request**: Version may already exist on PyPI
- **Network Error**: Retry with ``twine upload dist/*``
