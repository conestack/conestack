###############################################################################
# Conestack project
###############################################################################

include $(INCLUDE_FOLDER)/python-ldap.mk

###############################################################################
# project settings
###############################################################################

#MXDEV=-e sources/mxdev
#MXENV=-e sources/mxenv

SYSTEM_DEPENDENCIES=\
	build-essential \
	curl \
	libsasl2-dev \
	libssl-dev \
	libdb-dev \
	libltdl-dev

###############################################################################
# install
###############################################################################

.PHONY: project-install
project-install: python-ldap
	@make install


###############################################################################
# clean
###############################################################################

.PHONY: project-clean
project-clean: clean openldap-clean

.PHONY: project-full-clean
project-full-clean: full-clean openldap-clean
