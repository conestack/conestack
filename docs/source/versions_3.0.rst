Conestack 3.0
=============

This is the 3.0 version set.

Packages work from Python 3.10 up to Python 3.14.

``cone.*`` packages use Bootstrap 5 for theming.

``yafowil.*`` packages support themes for Bootstrap 3 and 5.

.. note::

    Conestack 3.0 marks the transition from Bootstrap 3 to Bootstrap 5.
    Packages like ``treibstoff`` have a major version bump (1.x to 2.x)
    to reflect this theming change. The upper version bounds in Conestack 2.0
    packages (e.g., ``treibstoff<2.0.0``) ensure Bootstrap 3 compatibility
    and prevent accidental upgrades to Bootstrap 5.

Specific Packages
-----------------

The following packages are specific to Conestack 3.0, they use Bootstrap 5:

+-----------------+-------+-------+
| Package         | 2.0   | 3.0   |
+=================+=======+=======+
| cone.app        | 1.1.x | 2.1.x |
+-----------------+-------+-------+
| cone.calendar   | 1.1.x | 2.0.x |
+-----------------+-------+-------+
| cone.charts     | 1.1.x | 2.0.x |
+-----------------+-------+-------+
| cone.fileupload | 1.1.x | 2.0.x |
+-----------------+-------+-------+
| cone.ldap       | 1.1.x | 2.0.x |
+-----------------+-------+-------+
| cone.tokens     | 1.1.x | 2.0.x |
+-----------------+-------+-------+
| cone.ugm        | 1.1.x | 2.0.x |
+-----------------+-------+-------+
| treibstoff      | 1.0.x | 2.0.x |
+-----------------+-------+-------+

.. include:: versions_shared.inc
