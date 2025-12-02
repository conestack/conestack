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
    yafowil.webob \

# Packages that run tests
VALIDATE_WITH_TESTS = $(filter-out $(VALIDATE_TEST_BLACKLIST), \
    $(VALIDATE_ALL_PACKAGES))

# Packages that skip tests
VALIDATE_SKIP_TESTS = $(filter $(VALIDATE_TEST_BLACKLIST), \
    $(VALIDATE_ALL_PACKAGES))

# Helper function to run validation on a list of packages in parallel
# Usage: $(call validate-packages,<package-list>,<script-options>)
define validate-packages
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

.PHONY: validate-env
validate-env: $(PACKAGES_TARGET)
	@echo "Building all packages..."
	@mkdir -p dist
	$(call validate-packages,$(VALIDATE_ALL_PACKAGES),--env)

.PHONY: validate-build
validate-build: $(PACKAGES_TARGET)
	@echo "Building all packages..."
	@mkdir -p dist
	$(call validate-packages,$(VALIDATE_ALL_PACKAGES),--build)

.PHONY: validate-check
validate-check: $(PACKAGES_TARGET)
	@echo "Checking all packages (pyroma + twine)..."
	$(call validate-packages,$(VALIDATE_ALL_PACKAGES),--check)

.PHONY: validate-test
validate-test: $(PACKAGES_TARGET)
	@echo "Testing packages from wheel (excluding blacklist)..."
	$(call validate-packages,$(VALIDATE_WITH_TESTS),--test)

.PHONY: validate-test-sdist
validate-test-sdist: $(PACKAGES_TARGET)
	@echo "Testing packages from sdist (excluding blacklist)..."
	$(call validate-packages,$(VALIDATE_WITH_TESTS),--test --install-from sdist)

.PHONY: validate-clean
validate-clean:
	@echo "Cleaning validation artifacts..."
	$(call validate-packages,$(VALIDATE_ALL_PACKAGES),--clean)
	@rm -rf dist
	@rm -rf /tmp/conestack-dev
	@echo "Validation artifacts cleaned"
