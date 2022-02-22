#!/bin/bash
#
# Run tests.

export TESTRUN_MARKER=1
export LDAP_ADD_BIN="openldap/bin/ldapadd"
export LDAP_DELETE_BIN="openldap/bin/ldapdelete"
export SLAPD_BIN="openldap/libexec/slapd"
export SLAPD_URIS="ldap://127.0.0.1:12345"
export ADDITIONAL_LDIF_LAYERS=""

./bin/zope-testrunner --auto-color --auto-progress \
    --test-path=sources/node/src \
    --test-path=sources/node.ext.directory/src \
    --test-path=sources/node.ext.ldap/src \
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
    --test-path=sources/cone.ldap/src \
    --test-path=sources/cone.maps/src \
    --test-path=sources/cone.sql/src \
    --test-path=sources/cone.tile/src \
    --test-path=sources/cone.ugm/src \
    --test-path=sources/cone.zodb/src \
    --test-path=sources/webresource/src \
    --module=$1

unset TESTRUN_MARKER
unset LDAP_ADD_BIN
unset LDAP_DELETE_BIN
unset SLAPD_BIN
unset SLAPD_URIS
unset ADDITIONAL_LDIF_LAYERS

exit 0
