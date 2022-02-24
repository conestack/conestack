#!/bin/bash

export TESTRUN_MARKER=1
export LDAP_ADD_BIN="openldap/bin/ldapadd"
export LDAP_DELETE_BIN="openldap/bin/ldapdelete"
export SLAPD_BIN="openldap/libexec/slapd"
export SLAPD_URIS="ldap://127.0.0.1:12345"
export ADDITIONAL_LDIF_LAYERS=""

sources=(
    sources/node/src/node
    sources/node.ext.directory/src/node/ext/directory
    sources/node.ext.ldap/src/node/ext/ldap
    sources/node.ext.ugm/src/node/ext/ugm
    sources/node.ext.yaml/src/node/ext/yaml
    sources/node.ext.zodb/src/node/ext/zodb
    sources/odict/src/odict
    sources/plumber/src/plumber
    sources/yafowil/src/yafowil
    sources/yafowil.bootstrap/src/yafowil/bootstrap
    sources/yafowil.lingua/src/yafowil/lingua
    sources/yafowil.webob/src/yafowil/webob
    sources/yafowil.widget.ace/src/yafowil/widget/ace
    sources/yafowil.widget.array/src/yafowil/widget/array
    sources/yafowil.widget.autocomplete/src/yafowil/widget/autocomplete
    sources/yafowil.widget.chosen/src/yafowil/widget/chosen
    sources/yafowil.widget.cron/src/yafowil/widget/cron
    sources/yafowil.widget.datetime/src/yafowil/widget/datetime
    sources/yafowil.widget.dict/src/yafowil/widget/dict
    sources/yafowil.widget.dynatree/src/yafowil/widget/dynatree
    sources/yafowil.widget.image/src/yafowil/widget/image
    sources/yafowil.widget.location/src/yafowil/widget/location
    sources/yafowil.widget.multiselect/src/yafowil/widget/multiselect
    sources/yafowil.widget.richtext/src/yafowil/widget/richtext
    sources/yafowil.widget.select2/src/yafowil/widget/select2
    sources/yafowil.widget.slider/src/yafowil/widget/slider
    sources/yafowil.widget.wysihtml5/src/yafowil/widget/wysihtml5
    sources/yafowil.yaml/src/yafowil/yaml
    sources/cone.app/src/cone/app
    sources/cone.calendar/src/cone/calendar
    sources/cone.fileupload/src/cone/fileupload
    sources/cone.firebase/src/cone/firebase
    sources/cone.ldap/src/cone/ldap
    sources/cone.maps/src/cone/maps
    sources/cone.sql/src/cone/sql
    sources/cone.tile/src/cone/tile
    sources/cone.ugm/src/cone/ugm
    sources/cone.zodb/src/cone/zodb
    sources/webresource/webresource
)

sources=$(printf ",%s" "${sources[@]}")
sources=${sources:1}

./bin/coverage run \
    --source=$sources \
    -m zope.testrunner --auto-color --auto-progress \
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
    --test-path=sources/yafowil.widget.dict/src \
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
    --test-path=sources/webresource

unset TESTRUN_MARKER
unset LDAP_ADD_BIN
unset LDAP_DELETE_BIN
unset SLAPD_BIN
unset SLAPD_URIS
unset ADDITIONAL_LDIF_LAYERS
