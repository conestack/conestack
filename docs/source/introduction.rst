Introduction
============

About Conestack
---------------

Conestack is an organization that develops a collection of interrelated Python
packages for building web applications. The project provides a layered
architecture from low-level data structures up to full-featured web application
components.

All packages are open source and hosted on GitHub at
https://github.com/conestack.

Package Families
----------------

The codebase consists of three main package families, each building on the
previous layer:

**node.*** - Tree Data Structures (Foundation Layer)
    The ``node`` package provides tree/node data structures using ordered
    dictionaries. Extensions provide backends for various storage systems:

    - ``node`` - Core tree data structures
    - ``node.ext.directory`` - Directory/file system trees
    - ``node.ext.fs`` - File system nodes
    - ``node.ext.ldap`` - LDAP directory trees
    - ``node.ext.ugm`` - User/Group management abstractions
    - ``node.ext.yaml`` - YAML file storage
    - ``node.ext.zodb`` - ZODB persistent storage

**yafowil.*** - Form Library (UI Layer)
    YAFOWIL (Yet Another Form Widget Library) provides a powerful form
    generation and processing framework:

    - ``yafowil`` - Core form library
    - ``yafowil.bootstrap`` - Bootstrap CSS framework integration
    - ``yafowil.webob`` - WebOb request/response integration
    - ``yafowil.yaml`` - YAML-based form definitions
    - ``yafowil.widget.*`` - Widget extensions (ace, array, autocomplete,
      chosen, color, cron, datetime, dict, dynatree, image, location,
      multiselect, richtext, select2, slider, tiptap, wysihtml5)

**cone.*** - Web Application Framework (Application Layer)
    The Cone framework builds on Pyramid to provide a complete web application
    stack:

    - ``cone.app`` - Main web application framework
    - ``cone.tile`` - Tile-based UI composition system
    - ``cone.ugm`` - User/Group management UI
    - ``cone.ldap`` - LDAP backend integration
    - ``cone.sql`` - SQL database integration
    - ``cone.zodb`` - ZODB backend integration
    - ``cone.calendar`` - Calendar functionality
    - ``cone.charts`` - Chart visualizations
    - ``cone.fileupload`` - File upload handling
    - ``cone.firebase`` - Firebase integration
    - ``cone.maps`` - Map widgets
    - ``cone.tokens`` - Token management

**Supporting Packages**
    - ``odict`` - Ordered dictionary implementation
    - ``plumber`` - Pipeline/plumbing pattern implementation
    - ``webresource`` - Web resource (JS/CSS) management
    - ``treibstoff`` - JavaScript/TypeScript utilities for cone.app

The Monorepo
------------

This repository is a **monorepo development environment** that manages 50+
packages simultaneously. It uses **mxdev** and **mxmake** for build
orchestration.

Directory Structure
~~~~~~~~~~~~~~~~~~~

::

    conestack/
    ├── sources/          # All package source code (Git checkouts)
    ├── mx.ini            # Package repository configuration
    ├── Makefile          # Generated build targets
    ├── venv/             # Python virtual environment
    ├── openldap/         # Local OpenLDAP server (for tests)
    ├── docs/             # This documentation
    └── scripts/          # Build and validation scripts

Each package in ``sources/`` is checked out from its own Git repository. The
``mx.ini`` file defines which repositories to check out and which branches to
use.

Build System
~~~~~~~~~~~~

The build system consists of two tools:

- **mxdev** - Checks out source repositories from GitHub and generates
  requirements files
- **mxmake** - Generates the Makefile with orchestrated build targets

The virtual environment uses **uv** as the package installer for improved
performance.

Working with the Repository
---------------------------

Initial Setup
~~~~~~~~~~~~~

.. code-block:: bash

    # Install system dependencies (Debian/Ubuntu)
    make system-dependencies

    # Full project install
    make install

    # Or step by step:
    make mxenv        # Create virtual environment
    make sources      # Checkout all source repositories
    make mxfiles      # Generate dependency files
    make packages     # Install all packages

Running Tests
~~~~~~~~~~~~~

.. code-block:: bash

    # Run all tests across all packages
    make test

    # Run coverage
    make coverage

Tests requiring LDAP functionality need the OpenLDAP installation, which can
be built with ``make openldap``.

Working with Individual Packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each package in ``sources/`` is its own Git repository:

1. Changes in ``sources/package-name/`` affect that package's repository
2. Use Git commands inside the specific package directory for commits
3. Packages are installed in development mode (editable install)
4. The root ``mx.ini`` defines which branch each package uses

.. note::

    Packages in ``sources/`` may contain their own nested mxmake setup from
    standalone development. When working from the root conestack directory,
    ignore these nested structures.

Cleanup Commands
~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Clean build artifacts (keeps sources)
    make clean

    # Remove sources directory too
    make purge

    # Clean specific components
    make mxenv-clean      # Remove virtual environment
    make packages-clean   # Uninstall packages
    make sources-purge    # Remove checked out sources

Working with Documentation
--------------------------

Building Documentation
~~~~~~~~~~~~~~~~~~~~~~

The documentation uses Sphinx and is located in the ``docs/`` directory:

.. code-block:: bash

    cd docs
    make html

The built documentation will be in ``docs/build/html/``.

Documentation Structure
~~~~~~~~~~~~~~~~~~~~~~~

- **Introduction** - This overview document
- **Version Overview** - Summary of version sets and their characteristics
- **Conestack 1.0/2.0/3.0** - Detailed package versions for each release
- **Version Mapping** - Complete version history across all releases
- **Package Validation** - QA process for release preparation

Python Version Support
----------------------

- **Conestack 1.0**: Python 2.7, Python 3.7-3.11
- **Conestack 2.0**: Python 3.10-3.14
- **Conestack 3.0**: Python 3.10-3.14

The minimum Python version for current development is **3.10**.

Further Reading
---------------

- Individual package documentation on PyPI and ReadTheDocs
- GitHub repositories at https://github.com/conestack
- Version-specific documentation in this guide
