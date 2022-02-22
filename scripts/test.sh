#!/bin/bash
#
# Run tests.

# --test-path=sources/node.ext.ldap/src \
# --test-path=sources/yafowil.widget.recaptcha/src \
# --test-path=sources/cone.ldap/src \

export TESTRUN_MARKER=1

./bin/zope-testrunner --auto-color --auto-progress \
    --test-path=sources/node/src \
    --test-path=sources/node.ext.directory/src \
    --test-path=sources/node.ext.ugm/src \
    --test-path=sources/node.ext.yaml/src \
    --test-path=sources/node.ext.zodb/src \
    --test-path=sources/odict/src \
    --test-path=sources/plumber/src \
    --test-path=sources/yafowil/src \
    --test-path=sources/yafowil.bootstrap/src \
    --test-path=sources/yafowil.lingua/src \
    --test-path=sources/yafowil.webob/src \
    --test-path=sources/yafowil.widget.ace/src \
    --test-path=sources/yafowil.widget.array/src \
    --test-path=sources/yafowil.widget.autocomplete/src \
    --test-path=sources/yafowil.widget.chosen/src \
    --test-path=sources/yafowil.widget.cron/src \
    --test-path=sources/yafowil.widget.datetime/src \
    --test-path=sources/yafowil.widget.directory/src \
    --test-path=sources/yafowil.widget.dynatree/src \
    --test-path=sources/yafowil.widget.image/src \
    --test-path=sources/yafowil.widget.location/src \
    --test-path=sources/yafowil.widget.multiselect/src \
    --test-path=sources/yafowil.widget.richtext/src \
    --test-path=sources/yafowil.widget.select2/src \
    --test-path=sources/yafowil.widget.slider/src \
    --test-path=sources/yafowil.widget.wysihtml5/src \
    --test-path=sources/yafowil.yaml/src \
    --test-path=sources/cone.app/src \
    --test-path=sources/cone.calendar/src \
    --test-path=sources/cone.fileupload/src \
    --test-path=sources/cone.firebase/src \
    --test-path=sources/cone.maps/src \
    --test-path=sources/cone.sql/src \
    --test-path=sources/cone.tile/src \
    --test-path=sources/cone.ugm/src \
    --test-path=sources/cone.zodb/src \
    --test-path=sources/webresource/src \
    --module=$1

unset TESTRUN_MARKER
