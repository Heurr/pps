#!/usr/bin/env sh
set -xe

COVERAGE_RCFILE=scripts/.coveragerc
export COVERAGE_RCFILE

pytest --capture=sys --cov=app --cov-report=term "$@" tests
