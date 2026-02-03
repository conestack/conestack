Conestack Version Sets
======================

Overview
--------

The Conestack project maintains multiple version sets to support different
Python versions and feature sets. Each version set represents a known good
combination of package versions that work together.

Version History
---------------

**Conestack 1.0** (Legacy)
  The original stable version set supporting Python 2.7 and Python 3.7-3.11.
  This version uses older package versions and is maintained for backward
  compatibility.

**Conestack 2.0**
  The current stable version set supporting Python 3.10-3.14. This version
  uses Bootstrap 3 in ``cone.*`` packages. ``yafowil.*`` packages support
  themes for Bootstrap 3 and 5.

**Conestack 3.0**
  The next version set supporting Python 3.10-3.14. This version transitions
  ``cone.*`` packages from Bootstrap 3 to Bootstrap 5. Core packages like
  ``cone.app``, ``cone.ugm``, and ``cone.ldap`` are updated to 2.0.0 versions.

Bootstrap Transition
--------------------

The transition from Bootstrap 3 to Bootstrap 5 is managed through version
bounds:

- **Conestack 2.0**: Uses Bootstrap 3. Packages have upper version bounds
  (e.g., ``treibstoff<2.0.0``) to ensure Bootstrap 3 compatibility.

- **Conestack 3.0**: Uses Bootstrap 5. The ``treibstoff`` package is bumped
  to 2.0.0, and upper version bounds are removed from dependent packages.

Python Version Support
----------------------

- **Conestack 1.0**: Python 2.7, Python 3.7-3.11
- **Conestack 2.0**: Python 3.10-3.14
- **Conestack 3.0**: Python 3.10-3.14

Package Status
--------------

Some packages are no longer maintained:

- **ARCHIVED**: Package is no longer maintained and should not be used
- **UNSUPPORTED**: Package was not part of legacy versions (1.0)

See the individual version pages for complete package listings and the
version mapping table for detailed package evolution across releases.
