#!/usr/bin/env sh
set -xe

black app tests
ruff . --fix
