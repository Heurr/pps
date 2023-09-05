#!/usr/bin/env sh
set -xe

autoflake -ir --remove-all-unused-imports app/ tests/
black app tests
