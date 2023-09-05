#!/usr/bin/env sh
set -xe

PACKAGE=app

# Static code analysis.
PYLINT_PROCESSES=2
pylint -j ${PYLINT_PROCESSES} $(ls -d ${PACKAGE}/*/)
flake8 ${PACKAGE}

black --check ${PACKAGE} tests
