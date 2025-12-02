##############################################################################
# Package Validation Targets
##############################################################################

# All packages from mx.ini (alphabetically sorted, one per line)
VALIDATE_ALL_PACKAGES = \
    cone.app \
    cone.calendar \
    cone.charts \
    cone.fileupload \
    cone.firebase \
    cone.ldap \
    cone.maps \
    cone.sql \
    cone.three \
    cone.tile \
    cone.tokens \
    cone.ugm \
    cone.zodb \
    node \
    node.ext.directory \
    node.ext.fs \
    node.ext.ldap \
    node.ext.ugm \
    node.ext.yaml \
    node.ext.zodb \
    odict \
    plumber \
    treibstoff \
    webresource \
    yafowil \
    yafowil.bootstrap \
    yafowil.demo \
    yafowil.documentation \
    yafowil.lingua \
    yafowil.webob \
    yafowil.widget.ace \
    yafowil.widget.array \
    yafowil.widget.autocomplete \
    yafowil.widget.chosen \
    yafowil.widget.color \
    yafowil.widget.cron \
    yafowil.widget.datetime \
    yafowil.widget.dict \
    yafowil.widget.dynatree \
    yafowil.widget.image \
    yafowil.widget.location \
    yafowil.widget.multiselect \
    yafowil.widget.richtext \
    yafowil.widget.select2 \
    yafowil.widget.slider \
    yafowil.widget.tiptap \
    yafowil.widget.wysihtml5 \
    yafowil.yaml \
    yafowil-example-helloworld

# Test blacklist from TODO.rst (alphabetically sorted, one per line)
VALIDATE_TEST_BLACKLIST = \
    cone.three \
    treibstoff \
    yafowil-example-helloworld \
    yafowil.demo \
    yafowil.documentation \
    yafowil.webob

# Packages requiring local OpenLDAP server (must run sequentially)
VALIDATE_SEQUENTIAL_TESTS = \
    cone.ldap \
    node.ext.ldap

# Packages that run tests (excluding blacklist)
VALIDATE_WITH_TESTS = $(filter-out $(VALIDATE_TEST_BLACKLIST), \
    $(VALIDATE_ALL_PACKAGES))

# Packages that run tests in parallel (excluding LDAP packages)
VALIDATE_PARALLEL_TESTS = $(filter-out $(VALIDATE_SEQUENTIAL_TESTS), \
    $(VALIDATE_WITH_TESTS))

# Packages that skip tests
VALIDATE_SKIP_TESTS = $(filter $(VALIDATE_TEST_BLACKLIST), \
    $(VALIDATE_ALL_PACKAGES))

# Helper function to run validation on a list of packages in parallel
# Usage: $(call validate-packages-parallel,<package-list>,<script-options>)
define validate-packages-parallel
	@mkdir -p /tmp/conestack-dev
	@rm -f /tmp/conestack-dev/validate_failed.txt
	@for pkg in $(1); do \
		(venv/bin/python scripts/validate_package.py $$pkg $(2) \
			> /tmp/conestack-dev/validate_$$pkg.log 2>&1 \
			&& echo "✓ $$pkg" \
			|| (echo "✗ $$pkg" && echo $$pkg >> /tmp/conestack-dev/validate_failed.txt)) & \
	done; \
	wait; \
	if [ -f /tmp/conestack-dev/validate_failed.txt ]; then \
		echo ""; \
		echo "Failed packages:"; \
		cat /tmp/conestack-dev/validate_failed.txt; \
		echo ""; \
		echo "Check logs in /tmp/conestack-dev/validate_<package>.log"; \
		exit 1; \
	else \
		echo ""; \
		echo "All packages validated successfully"; \
	fi
endef

# Helper function to run validation on a list of packages sequentially
# Usage: $(call validate-packages-sequential,<package-list>,<script-options>)
define validate-packages-sequential
	@mkdir -p /tmp/conestack-dev
	@rm -f /tmp/conestack-dev/validate_failed.txt
	@for pkg in $(1); do \
		venv/bin/python scripts/validate_package.py $$pkg $(2) \
			> /tmp/conestack-dev/validate_$$pkg.log 2>&1 \
			&& echo "✓ $$pkg" \
			|| (echo "✗ $$pkg" && echo $$pkg >> /tmp/conestack-dev/validate_failed.txt); \
	done; \
	if [ -f /tmp/conestack-dev/validate_failed.txt ]; then \
		echo ""; \
		echo "Failed packages:"; \
		cat /tmp/conestack-dev/validate_failed.txt; \
		echo ""; \
		echo "Check logs in /tmp/conestack-dev/validate_<package>.log"; \
		exit 1; \
	else \
		echo ""; \
		echo "All packages validated successfully"; \
	fi
endef

.PHONY: validate-env
validate-env: $(PACKAGES_TARGET)
	@echo "Building all packages..."
	@mkdir -p dist
	$(call validate-packages-parallel,$(VALIDATE_ALL_PACKAGES),--env)

.PHONY: validate-build
validate-build: $(PACKAGES_TARGET)
	@echo "Building all packages..."
	@mkdir -p dist
	$(call validate-packages-parallel,$(VALIDATE_ALL_PACKAGES),--build)

.PHONY: validate-check
validate-check: $(PACKAGES_TARGET)
	@echo "Checking all packages (pyroma + twine)..."
	$(call validate-packages-parallel,$(VALIDATE_ALL_PACKAGES),--check)

.PHONY: validate-test
validate-test: $(PACKAGES_TARGET)
	@echo "Testing packages from wheel (parallel)..."
	$(call validate-packages-parallel,$(VALIDATE_PARALLEL_TESTS),--test)
	@echo ""
	@echo "Testing LDAP packages from wheel (sequential)..."
	$(call validate-packages-sequential,$(VALIDATE_SEQUENTIAL_TESTS),--test)

.PHONY: validate-test-sdist
validate-test-sdist: $(PACKAGES_TARGET)
	@echo "Testing packages from sdist (parallel)..."
	$(call validate-packages-parallel,$(VALIDATE_PARALLEL_TESTS),--test --install-from sdist)
	@echo ""
	@echo "Testing LDAP packages from sdist (sequential)..."
	$(call validate-packages-sequential,$(VALIDATE_SEQUENTIAL_TESTS),--test --install-from sdist)

.PHONY: validate-compare
validate-compare:
	@echo "Comparing wheel and sdist contents..."
	@venv/bin/python scripts/compare_artifacts.py

.PHONY: validate-clean
validate-clean:
	@echo "Cleaning validation artifacts..."
	$(call validate-packages-parallel,$(VALIDATE_ALL_PACKAGES),--clean)
	@rm -rf dist
	@rm -rf /tmp/conestack-dev
	@echo "Validation artifacts cleaned"

.PHONY: validate-all
validate-all:
	@echo "============================================================"
	@echo "Running complete validation QA chain"
	@echo "============================================================"
	@echo ""
	$(MAKE) validate-env
	@echo ""
	$(MAKE) validate-build
	@echo ""
	$(MAKE) validate-compare
	@echo ""
	$(MAKE) validate-check
	@echo ""
	$(MAKE) validate-test
	@echo ""
	$(MAKE) validate-test-sdist
	@echo ""
	$(MAKE) validate-clean
	@echo ""
	@echo "============================================================"
	@echo "Complete validation QA chain finished successfully"
	@echo "============================================================"
