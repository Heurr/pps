#!/usr/bin/env sh
set -xe

PACKAGE=app

mypy --cache-dir=/dev/null --show-error-codes ${PACKAGE}
