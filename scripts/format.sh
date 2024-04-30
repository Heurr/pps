#!/usr/bin/env sh
set -xe

black app tests
ruff check . --fix
