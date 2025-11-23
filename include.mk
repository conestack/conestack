##############################################################################
# Package Validation Targets
##############################################################################

# All packages from mx.ini (48 packages)
VALIDATE_ALL_PACKAGES = \
    odict plumber \
    node node.ext.directory node.ext.fs node.ext.ldap \
    node.ext.ugm node.ext.yaml node.ext.zodb \
    yafowil yafowil.yaml yafowil.lingua yafowil.webob \
    yafowil.bootstrap \
    yafowil.widget.ace yafowil.widget.array yafowil.widget.autocomplete \
    yafowil.widget.chosen yafowil.widget.color yafowil.widget.cron \
    yafowil.widget.datetime yafowil.widget.dict yafowil.widget.image \
    yafowil.widget.location yafowil.widget.multiselect \
    yafowil.widget.richtext yafowil.widget.select2 yafowil.widget.slider \
    yafowil.widget.tiptap yafowil.widget.wysihtml5 \
    yafowil.demo yafowil.documentation yafowil-example-helloworld \
    treibstoff webresource \
    cone.app cone.calendar cone.charts cone.fileupload cone.firebase \
    cone.ugm cone.ldap cone.maps cone.sql cone.tile cone.tokens cone.zodb

# Test blacklist from TODO.rst (6 packages - tests skipped)
VALIDATE_TEST_BLACKLIST = \
    sphinx-conestack-theme treibstoff yafowil-example-helloworld \
    yafowil.demo yafowil.documentation yafowil.webob

# Packages that run tests (48 - 6 = 42 packages)
VALIDATE_WITH_TESTS = $(filter-out $(VALIDATE_TEST_BLACKLIST), \
    $(VALIDATE_ALL_PACKAGES))

# Packages that skip tests (6 packages)
VALIDATE_SKIP_TESTS = $(filter $(VALIDATE_TEST_BLACKLIST), \
    $(VALIDATE_ALL_PACKAGES))

.PHONY: validate-all
validate-all: $(PACKAGES_TARGET)
	@echo "=== Batch Package Validation (with tests) ==="
	@echo "Validating $(words $(VALIDATE_ALL_PACKAGES)) packages in parallel..."
	@echo "  - $(words $(VALIDATE_WITH_TESTS)) packages WITH tests"
	@echo "  - $(words $(VALIDATE_SKIP_TESTS)) packages WITHOUT tests"
	@rm -rf dist/
	@mkdir -p /tmp/conestack-dev
	@failed=""; \
	pids=""; \
	for pkg in $(VALIDATE_WITH_TESTS); do \
		(venv/bin/python scripts/validate_package.py $$pkg --collect-dist \
		 > /tmp/conestack-dev/validate_$$pkg.log 2>&1 && \
		 echo "✓ $$pkg" || \
		 (echo "✗ $$pkg" && echo "$$pkg" >> /tmp/conestack-dev/validate_failed.txt)) & \
		pids="$$pids $$!"; \
	done; \
	for pkg in $(VALIDATE_SKIP_TESTS); do \
		(venv/bin/python scripts/validate_package.py $$pkg --skip-tests \
		 --collect-dist > /tmp/conestack-dev/validate_$$pkg.log 2>&1 && \
		 echo "✓ $$pkg (tests skipped)" || \
		 (echo "✗ $$pkg (tests skipped)" && \
		  echo "$$pkg" >> /tmp/conestack-dev/validate_failed.txt)) & \
		pids="$$pids $$!"; \
	done; \
	wait $$pids; \
	echo ""; \
	echo "=== Validation Complete ==="; \
	if [ -f /tmp/conestack-dev/validate_failed.txt ]; then \
		failed=$$(cat /tmp/conestack-dev/validate_failed.txt); \
		count=$$(wc -l < /tmp/conestack-dev/validate_failed.txt); \
		echo "❌ $$count package(s) FAILED:"; \
		cat /tmp/conestack-dev/validate_failed.txt | sed 's/^/  - /'; \
		echo ""; \
		echo "Check logs in /tmp/conestack-dev/validate_*.log for details"; \
		rm /tmp/conestack-dev/validate_failed.txt; \
		exit 1; \
	else \
		echo "✅ All $(words $(VALIDATE_ALL_PACKAGES)) packages passed!"; \
		echo "Build artifacts collected in dist/"; \
	fi

.PHONY: validate-quick
validate-quick: $(PACKAGES_TARGET)
	@echo "=== Quick Package Validation (skip all tests) ==="
	@echo "Validating $(words $(VALIDATE_ALL_PACKAGES)) packages in parallel..."
	@rm -rf dist/
	@mkdir -p /tmp/conestack-dev
	@failed=""; \
	pids=""; \
	for pkg in $(VALIDATE_ALL_PACKAGES); do \
		(venv/bin/python scripts/validate_package.py $$pkg --skip-tests \
		 --collect-dist > /tmp/conestack-dev/validate_$$pkg.log 2>&1 && \
		 echo "✓ $$pkg" || \
		 (echo "✗ $$pkg" && echo "$$pkg" >> /tmp/conestack-dev/validate_failed.txt)) & \
		pids="$$pids $$!"; \
	done; \
	wait $$pids; \
	echo ""; \
	echo "=== Validation Complete ==="; \
	if [ -f /tmp/conestack-dev/validate_failed.txt ]; then \
		failed=$$(cat /tmp/conestack-dev/validate_failed.txt); \
		count=$$(wc -l < /tmp/conestack-dev/validate_failed.txt); \
		echo "❌ $$count package(s) FAILED:"; \
		cat /tmp/conestack-dev/validate_failed.txt | sed 's/^/  - /'; \
		echo ""; \
		echo "Check logs in /tmp/conestack-dev/validate_*.log for details"; \
		rm /tmp/conestack-dev/validate_failed.txt; \
		exit 1; \
	else \
		echo "✅ All $(words $(VALIDATE_ALL_PACKAGES)) packages passed!"; \
		echo "Build artifacts collected in dist/"; \
	fi

.PHONY: validate-clean
validate-clean:
	@echo "Cleaning validation artifacts..."
	@rm -rf dist/
	@rm -rf /tmp/conestack-dev
	@echo "✓ Cleaned dist/ and validation logs"
