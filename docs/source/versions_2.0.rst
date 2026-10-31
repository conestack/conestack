Conestack 2.0
=============

This is the 2.0 version set.

Packages work from Python 3.10 up to Python 3.14.

``cone.*`` packages use Bootstrap 3 for theming.

``yafowil.*`` packages support themes for Bootstrap 3 and 5.

.. note::

    Some packages in Conestack 2.0 have upper version bounds (e.g., ``<2.0.0``)
    on their dependencies. These bounds mark the transition point from Bootstrap 3
    (Conestack 2.0) to Bootstrap 5 (Conestack 3.0). For example, ``cone.app``
    requires ``treibstoff<2.0.0`` to ensure Bootstrap 3 compatibility.

New Packages
------------

The following packages are new in Conestack 2.0:

- ``cone.charts``
- ``cone.three``
- ``cone.tokens``
- ``treibstoff``
- ``webresource``
- ``yafowil.widget.color``
- ``yafowil.widget.tiptap``

Removed Packages
----------------

The following packages have been removed or archived:

+--------------------+-------------------------+
| Package            | Note                    |
+====================+=========================+
| bdajax             | replaced by treibstoff  |
+--------------------+-------------------------+
| yafowil.werkzeug   | ARCHIVED                |
+--------------------+-------------------------+

Specific Packages
-----------------

The following packages are specific to Conestack 2.0, they use Bootstrap 3:

+-----------------+-------+-------+
| Package         | 1.0   | 2.0   |
+=================+=======+=======+
| cone.app        | 1.0.8 | 1.1.x |
+-----------------+-------+-------+
| cone.calendar   | 0.4   | 1.1.x |
+-----------------+-------+-------+
| cone.charts     | --    | 1.1.x |
+-----------------+-------+-------+
| cone.fileupload | 0.8   | 1.1.x |
+-----------------+-------+-------+
| cone.ldap       | 0.3   | 1.1.x |
+-----------------+-------+-------+
| cone.tokens     | --    | 1.1.x |
+-----------------+-------+-------+
| cone.ugm        | 1.0   | 1.1.x |
+-----------------+-------+-------+
| treibstoff      | --    | 1.0.x |
+-----------------+-------+-------+

.. include:: versions_shared.inc
