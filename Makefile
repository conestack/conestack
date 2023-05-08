##############################################################################
# THIS FILE IS GENERATED BY MXMAKE
#
# DOMAINS:
#: core.base
#: core.mxenv
#: core.mxfiles
#: core.packages
#: core.sources
#: ldap.openldap
#: ldap.python-ldap
#: qa.coverage
#: qa.test
#: system.dependencies
#
# SETTINGS (ALL CHANGES MADE BELOW SETTINGS WILL BE LOST)
##############################################################################

## core.base

# `deploy` target dependencies.
# No default value.
DEPLOY_TARGETS?=

# target to be executed when calling `make run`
# No default value.
RUN_TARGET?=

# Additional files and folders to remove when running clean target
# No default value.
CLEAN_FS?=

# Optional makefile to include before default targets. This can
# be used to provide custom targets or hook up to existing targets.
# Default: include.mk
INCLUDE_MAKEFILE?=include.mk

## system.dependencies

# Space separated system package names.
# No default value.
SYSTEM_DEPENDENCIES?=

## ldap.openldap

# OpenLDAP version to download
# Default: 2.4.59
OPENLDAP_VERSION?=2.4.59

# OpenLDAP base download URL
# Default: https://www.openldap.org/software/download/OpenLDAP/openldap-release/
OPENLDAP_URL?=https://www.openldap.org/software/download/OpenLDAP/openldap-release/

# Build directory for OpenLDAP
# Default: $(shell echo $(realpath .))/openldap
OPENLDAP_DIR?=$(shell echo $(realpath .))/openldap

# Build environment for OpenLDAP
# Default: PATH=/usr/local/bin:/usr/bin:/bin
OPENLDAP_ENV?=PATH=/usr/local/bin:/usr/bin:/bin

## core.mxenv

# Python interpreter to use.
# Default: python3
PYTHON_BIN?=python3

# Minimum required Python version.
# Default: 3.7
PYTHON_MIN_VERSION?=3.7

# Flag whether to use virtual environment. If `false`, the
# interpreter according to `PYTHON_BIN` found in `PATH` is used.
# Default: true
VENV_ENABLED?=true

# Flag whether to create a virtual environment. If set to `false`
# and `VENV_ENABLED` is `true`, `VENV_FOLDER` is expected to point to an
# existing virtual environment.
# Default: true
VENV_CREATE?=true

# The folder of the virtual environment.
# If `VENV_ENABLED` is `true` and `VENV_CREATE` is true it is used as the
# target folder for the virtual environment. If `VENV_ENABLED` is `true` and
# `VENV_CREATE` is false it is expected to point to an existing virtual
# environment. If `VENV_ENABLED` is `false` it is ignored.
# Default: venv
VENV_FOLDER?=venv

# mxdev to install in virtual environment.
# Default: mxdev
MXDEV?=mxdev

# mxmake to install in virtual environment.
# Default: mxmake
MXMAKE?=mxmake

## core.mxfiles

# The config file to use.
# Default: mx.ini
PROJECT_CONFIG?=mx.ini

## qa.test

# The command which gets executed. Defaults to the location the
# :ref:`run-tests` template gets rendered to if configured.
# Default: .mxmake/files/run-tests.sh
TEST_COMMAND?=.mxmake/files/run-tests.sh

# Additional Python requirements for running tests to be
# installed (via pip).
# Default: pytest
TEST_REQUIREMENTS?=zope.testrunner

# Additional make targets the test target depends on.
# No default value.
TEST_DEPENDENCY_TARGETS?=python-ldap

## qa.coverage

# The command which gets executed. Defaults to the location the
# :ref:`run-coverage` template gets rendered to if configured.
# Default: .mxmake/files/run-coverage.sh
COVERAGE_COMMAND?=.mxmake/files/run-coverage.sh

##############################################################################
# END SETTINGS - DO NOT EDIT BELOW THIS LINE
##############################################################################

INSTALL_TARGETS?=
DIRTY_TARGETS?=
CLEAN_TARGETS?=
PURGE_TARGETS?=
CHECK_TARGETS?=
FORMAT_TARGETS?=

# Defensive settings for make: https://tech.davis-hansson.com/p/make/
SHELL:=bash
.ONESHELL:
# for Makefile debugging purposes add -x to the .SHELLFLAGS
.SHELLFLAGS:=-eu -o pipefail -O inherit_errexit -c
.SILENT:
.DELETE_ON_ERROR:
MAKEFLAGS+=--warn-undefined-variables
MAKEFLAGS+=--no-builtin-rules

# mxmake folder
MXMAKE_FOLDER?=.mxmake

# Sentinel files
SENTINEL_FOLDER?=$(MXMAKE_FOLDER)/sentinels
SENTINEL?=$(SENTINEL_FOLDER)/about.txt
$(SENTINEL):
	@mkdir -p $(SENTINEL_FOLDER)
	@echo "Sentinels for the Makefile process." > $(SENTINEL)

##############################################################################
# system dependencies
##############################################################################

.PHONY: system-dependencies
system-dependencies:
	@echo "Install system dependencies"
	@test -z "$(SYSTEM_DEPENDENCIES)" && echo "No System dependencies defined"
	@test -z "$(SYSTEM_DEPENDENCIES)" \
		|| sudo apt-get install -y $(SYSTEM_DEPENDENCIES)

##############################################################################
# openldap
##############################################################################

# case `system.dependencies` domain is included
SYSTEM_DEPENDENCIES+=libdb-dev libsasl2-dev

OPENLDAP_TARGET:=$(SENTINEL_FOLDER)/openldap.sentinel
$(OPENLDAP_TARGET): $(SENTINEL)
	@echo "Building openldap server in '$(OPENLDAP_DIR)'"
	@test -d $(OPENLDAP_DIR) || curl -o openldap-$(OPENLDAP_VERSION).tgz \
		$(OPENLDAP_URL)/openldap-$(OPENLDAP_VERSION).tgz
	@test -d $(OPENLDAP_DIR) || tar xf openldap-$(OPENLDAP_VERSION).tgz
	@test -d $(OPENLDAP_DIR) || rm openldap-$(OPENLDAP_VERSION).tgz
	@test -d $(OPENLDAP_DIR) || mv openldap-$(OPENLDAP_VERSION) $(OPENLDAP_DIR)
	@env -i -C $(OPENLDAP_DIR) $(OPENLDAP_ENV) bash -c \
		'./configure \
			--with-tls \
			--enable-slapd=yes \
			--enable-overlays \
			--prefix=$(OPENLDAP_DIR) \
		&& make depend \
		&& make -j4 \
		&& make install'
	@touch $(OPENLDAP_TARGET)

.PHONY: openldap
openldap: $(OPENLDAP_TARGET)

.PHONY: openldap-dirty
openldap-dirty:
	@test -d $(OPENLDAP_DIR) \
		&& env -i -C $(OPENLDAP_DIR) $(OPENLDAP_ENV) bash -c 'make clean'
	@rm -f $(OPENLDAP_TARGET)

.PHONY: openldap-clean
openldap-clean:
	@rm -f $(OPENLDAP_TARGET)
	@rm -rf $(OPENLDAP_DIR)

INSTALL_TARGETS+=openldap
DIRTY_TARGETS+=openldap-dirty
CLEAN_TARGETS+=openldap-clean

##############################################################################
# mxenv
##############################################################################

# Check if given Python is installed
ifeq (,$(shell which $(PYTHON_BIN)))
$(error "PYTHON=$(PYTHON_BIN) not found in $(PATH)")
endif

# Check if given Python version is ok
PYTHON_VERSION_OK=$(shell $(PYTHON_BIN) -c "import sys; print((int(sys.version_info[0]), int(sys.version_info[1])) >= tuple(map(int, '$(PYTHON_MIN_VERSION)'.split('.'))))")
ifeq ($(PYTHON_VERSION_OK),0)
$(error "Need Python >= $(PYTHON_MIN_VERSION)")
endif

# Check if venv folder is configured if venv is enabled
ifeq ($(shell [[ "$(VENV_ENABLED)" == "true" && "$(VENV_FOLDER)" == "" ]] && echo "true"),"true")
$(error "VENV_FOLDER must be configured if VENV_ENABLED is true")
endif

# determine the executable path
ifeq ("$(VENV_ENABLED)", "true")
MXENV_PATH=$(VENV_FOLDER)/bin/
else
MXENV_PATH=
endif

MXENV_TARGET:=$(SENTINEL_FOLDER)/mxenv.sentinel
$(MXENV_TARGET): $(SENTINEL)
ifeq ("$(VENV_ENABLED)", "true")
	@echo "Setup Python Virtual Environment under '$(VENV_FOLDER)'"
	@$(PYTHON_BIN) -m venv $(VENV_FOLDER)
endif
	@$(MXENV_PATH)pip install -U pip setuptools wheel
	@$(MXENV_PATH)pip install -U $(MXDEV)
	@$(MXENV_PATH)pip install -U $(MXMAKE)
	@touch $(MXENV_TARGET)

.PHONY: mxenv
mxenv: $(MXENV_TARGET)

.PHONY: mxenv-dirty
mxenv-dirty:
	@rm -f $(MXENV_TARGET)

.PHONY: mxenv-clean
mxenv-clean: mxenv-dirty
ifeq ("$(VENV_ENABLED)", "true")
	@rm -rf $(VENV_FOLDER)
else
	@$(MXENV_PATH)pip uninstall -y $(MXDEV)
	@$(MXENV_PATH)pip uninstall -y $(MXMAKE)
endif

INSTALL_TARGETS+=mxenv
DIRTY_TARGETS+=mxenv-dirty
CLEAN_TARGETS+=mxenv-clean

##############################################################################
# python-ldap
##############################################################################

PYTHON_LDAP_TARGET:=$(SENTINEL_FOLDER)/python-ldap.sentinel
$(PYTHON_LDAP_TARGET): $(MXENV_TARGET) $(OPENLDAP_TARGET)
	@$(MXENV_PATH)pip install \
		--force-reinstall \
		--no-binary=:all: \
		--config-settings="CFLAGS=-I$(OPENLDAP_DIR)/include" \
		--config-settings="CFLAGS=-L$(OPENLDAP_DIR)/lib" \
		--config-settings="CFLAGS=-R$(OPENLDAP_DIR)/lib" \
		python-ldap
	@touch $(PYTHON_LDAP_TARGET)

.PHONY: python-ldap
python-ldap: $(PYTHON_LDAP_TARGET)

.PHONY: python-ldap-dirty
python-ldap-dirty:
	@rm -f $(PYTHON_LDAP_TARGET)

.PHONY: python-ldap-clean
python-ldap-clean: python-ldap-dirty
	@test -e $(MXENV_PATH)pip && $(MXENV_PATH)pip uninstall -y python-ldap || :

INSTALL_TARGETS+=python-ldap
DIRTY_TARGETS+=python-ldap-dirty
CLEAN_TARGETS+=python-ldap-clean

##############################################################################
# sources
##############################################################################

SOURCES_TARGET:=$(SENTINEL_FOLDER)/sources.sentinel
$(SOURCES_TARGET): $(MXENV_TARGET)
	@echo "Checkout project sources"
	@$(MXENV_PATH)mxdev -o -c $(PROJECT_CONFIG)
	@touch $(SOURCES_TARGET)

.PHONY: sources
sources: $(SOURCES_TARGET)

.PHONY: sources-dirty
sources-dirty:
	@rm -f $(SOURCES_TARGET)

.PHONY: sources-purge
sources-purge: sources-dirty
	@rm -rf sources

INSTALL_TARGETS+=sources
DIRTY_TARGETS+=sources-dirty
PURGE_TARGETS+=sources-purge

##############################################################################
# mxfiles
##############################################################################

# case `core.sources` domain not included
SOURCES_TARGET?=

# File generation target
MXMAKE_FILES?=$(MXMAKE_FOLDER)/files

# set environment variables for mxmake
define set_mxfiles_env
	@export MXMAKE_MXENV_PATH=$(1)
	@export MXMAKE_FILES=$(2)
endef

# unset environment variables for mxmake
define unset_mxfiles_env
	@unset MXMAKE_MXENV_PATH
	@unset MXMAKE_FILES
endef

$(PROJECT_CONFIG):
ifneq ("$(wildcard $(PROJECT_CONFIG))","")
	@touch $(PROJECT_CONFIG)
else
	@echo "[settings]" > $(PROJECT_CONFIG)
endif

LOCAL_PACKAGE_FILES:=$(wildcard pyproject.toml setup.cfg setup.py requirements.txt constraints.txt)

FILES_TARGET:=requirements-mxdev.txt
$(FILES_TARGET): $(PROJECT_CONFIG) $(MXENV_TARGET) $(SOURCES_TARGET) $(LOCAL_PACKAGE_FILES)
	@echo "Create project files"
	@mkdir -p $(MXMAKE_FILES)
	$(call set_mxfiles_env,$(MXENV_PATH),$(MXMAKE_FILES))
	@$(MXENV_PATH)mxdev -n -c $(PROJECT_CONFIG)
	$(call unset_mxfiles_env,$(MXENV_PATH),$(MXMAKE_FILES))
	@touch $(FILES_TARGET)

.PHONY: mxfiles
mxfiles: $(FILES_TARGET)

.PHONY: mxfiles-dirty
mxfiles-dirty:
	@touch $(PROJECT_CONFIG)

.PHONY: mxfiles-clean
mxfiles-clean: mxfiles-dirty
	@rm -rf constraints-mxdev.txt requirements-mxdev.txt $(MXMAKE_FILES)

INSTALL_TARGETS+=mxfiles
DIRTY_TARGETS+=mxfiles-dirty
CLEAN_TARGETS+=mxfiles-clean

##############################################################################
# packages
##############################################################################

# additional sources targets which requires package re-install on change
-include $(MXMAKE_FILES)/additional_sources_targets.mk
ADDITIONAL_SOURCES_TARGETS?=

INSTALLED_PACKAGES=$(MXMAKE_FILES)/installed.txt

PACKAGES_TARGET:=$(INSTALLED_PACKAGES)
$(PACKAGES_TARGET): $(FILES_TARGET) $(ADDITIONAL_SOURCES_TARGETS)
	@echo "Install python packages"
	@$(MXENV_PATH)pip install -r $(FILES_TARGET)
	@$(MXENV_PATH)pip freeze > $(INSTALLED_PACKAGES)
	@touch $(PACKAGES_TARGET)

.PHONY: packages
packages: $(PACKAGES_TARGET)

.PHONY: packages-dirty
packages-dirty:
	@rm -f $(PACKAGES_TARGET)

.PHONY: packages-clean
packages-clean:
	@test -e $(FILES_TARGET) \
		&& test -e $(MXENV_PATH)pip \
		&& $(MXENV_PATH)pip uninstall -y -r $(FILES_TARGET) \
		|| :
	@rm -f $(PACKAGES_TARGET)

INSTALL_TARGETS+=packages
DIRTY_TARGETS+=packages-dirty
CLEAN_TARGETS+=packages-clean

##############################################################################
# test
##############################################################################

TEST_TARGET:=$(SENTINEL_FOLDER)/test.sentinel
$(TEST_TARGET): $(MXENV_TARGET)
	@echo "Install $(TEST_REQUIREMENTS)"
	@$(MXENV_PATH)pip install $(TEST_REQUIREMENTS)
	@touch $(TEST_TARGET)

.PHONY: test
test: $(FILES_TARGET) $(SOURCES_TARGET) $(PACKAGES_TARGET) $(TEST_TARGET) $(TEST_DEPENDENCY_TARGETS)
	@echo "Run tests"
	@test -z "$(TEST_COMMAND)" && echo "No test command defined"
	@test -z "$(TEST_COMMAND)" || bash -c "$(TEST_COMMAND)"

.PHONY: test-dirty
test-dirty:
	@rm -f $(TEST_TARGET)

.PHONY: test-clean
test-clean: test-dirty
	@test -e $(MXENV_PATH)pip && $(MXENV_PATH)pip uninstall -y $(TEST_REQUIREMENTS) || :
	@rm -rf .pytest_cache

INSTALL_TARGETS+=$(TEST_TARGET)
CLEAN_TARGETS+=test-clean
DIRTY_TARGETS+=test-dirty

##############################################################################
# coverage
##############################################################################

COVERAGE_TARGET:=$(SENTINEL_FOLDER)/coverage.sentinel
$(COVERAGE_TARGET): $(TEST_TARGET)
	@echo "Install Coverage"
	@$(MXENV_PATH)pip install -U coverage
	@touch $(COVERAGE_TARGET)

.PHONY: coverage
coverage: $(FILES_TARGET) $(SOURCES_TARGET) $(PACKAGES_TARGET) $(COVERAGE_TARGET)
	@echo "Run coverage"
	@test -z "$(COVERAGE_COMMAND)" && echo "No coverage command defined"
	@test -z "$(COVERAGE_COMMAND)" || bash -c "$(COVERAGE_COMMAND)"

.PHONY: coverage-dirty
coverage-dirty:
	@rm -f $(COVERAGE_TARGET)

.PHONY: coverage-clean
coverage-clean: coverage-dirty
	@test -e $(MXENV_PATH)pip && $(MXENV_PATH)pip uninstall -y coverage || :
	@rm -rf .coverage htmlcov

INSTALL_TARGETS+=$(COVERAGE_TARGET)
DIRTY_TARGETS+=coverage-dirty
CLEAN_TARGETS+=coverage-clean

-include $(INCLUDE_MAKEFILE)

##############################################################################
# Default targets
##############################################################################

INSTALL_TARGET:=$(SENTINEL_FOLDER)/install.sentinel
$(INSTALL_TARGET): $(INSTALL_TARGETS)
	@touch $(INSTALL_TARGET)

.PHONY: install
install: $(INSTALL_TARGET)
	@touch $(INSTALL_TARGET)

.PHONY: run
run: $(RUN_TARGET)

.PHONY: deploy
deploy: $(DEPLOY_TARGETS)

.PHONY: dirty
dirty: $(DIRTY_TARGETS)
	@rm -f $(INSTALL_TARGET)

.PHONY: clean
clean: dirty $(CLEAN_TARGETS)
	@rm -rf $(CLEAN_TARGETS) $(MXMAKE_FOLDER) $(CLEAN_FS)

.PHONY: purge
purge: clean $(PURGE_TARGETS)

.PHONY: runtime-clean
runtime-clean:
	@echo "Remove runtime artifacts, like byte-code and caches."
	@find . -name '*.py[c|o]' -delete
	@find . -name '*~' -exec rm -f {} +
	@find . -name '__pycache__' -exec rm -fr {} +

.PHONY: check
check: $(CHECK_TARGETS)

.PHONY: format
format: $(FORMAT_TARGETS)
