#!/usr/bin/env sh
set -xe

HOST=${PS_API_HOST:-0.0.0.0}
PORT=${PS_API_PORT:-80}
LOG_LEVEL=${PS_LOG_LEVEL:-info}

# Start Uvicorn with live reload
exec uvicorn \
    --reload \
    --host "${HOST}" \
    --port "${PORT}" \
    --log-level "${LOG_LEVEL}" \
    --factory \
    app.api_app:create_api_app

