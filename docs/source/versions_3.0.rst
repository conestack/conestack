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

Version Changes
---------------

Bootstrap 5 transition - treibstoff major version bump:

- treibstoff: 1.0.0 → 2.0.0

Cone framework version bumps:

- cone.app: 1.1.0 → 2.0.0
- cone.calendar: 1.1.0 → 2.0.0
- cone.fileupload: 1.1.0 → 2.0.0
- cone.ldap: 1.1.0 → 2.0.0
- cone.tokens: 1.1.0 → 2.0.0
- cone.ugm: 1.1.0 → 2.0.0

Unchanged Packages
------------------

The following packages remain at their Conestack 2.0 versions:

- cone.charts = 1.1.0
- cone.firebase = 1.1.0
- cone.maps = 1.1.0
- cone.sql = 1.1.0
- cone.three = 1.1.0
- cone.tile = 2.0.0
- cone.zodb = 1.1.0
- node = 2.0.0
- node.ext.directory = 2.0.0
- node.ext.fs = 2.0.0
- node.ext.ldap = 2.0.0
- node.ext.ugm = 2.0.0
- node.ext.yaml = 2.0.0
- node.ext.zodb = 2.0.0
- odict = 2.0.0
- plumber = 2.0.0
- webresource = 2.0.0
- yafowil = 4.0.0
- yafowil.bootstrap = 2.0.0
- yafowil.demo = 4.0.0
- yafowil.documentation = 4.0.0
- yafowil.lingua = 2.0.0
- yafowil.webob = 2.0.0
- yafowil.widget.ace = 2.0.0
- yafowil.widget.array = 2.0.0
- yafowil.widget.autocomplete = 2.0.0
- yafowil.widget.chosen = 2.0.0
- yafowil.widget.color = 2.0.0
- yafowil.widget.cron = 2.0.0
- yafowil.widget.datetime = 2.0.0
- yafowil.widget.dict = 2.0.0
- yafowil.widget.dynatree = 2.0.0
- yafowil.widget.image = 2.0.0
- yafowil.widget.location = 2.0.0
- yafowil.widget.multiselect = 2.0.0
- yafowil.widget.richtext = 2.0.0
- yafowil.widget.select2 = 2.0.0
- yafowil.widget.slider = 2.0.0
- yafowil.widget.tiptap = 2.0.0
- yafowil.widget.wysihtml5 = 2.0.0
- yafowil.yaml = 3.0.0
