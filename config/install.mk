###############################################################################
# install
###############################################################################

.PHONY: install
install: openldap mxenv
	@make pip

.PHONY: full-install
full-install: openldap mxenv
	@make deps
	@make pip
