#!/usr/bin/env sh
set -e

HOST=${PS_API_HOST:-0.0.0.0}
PORT=${PS_API_PORT:-5000}
LOG_LEVEL=${PS_LOG_LEVEL:-info}

# Start Uvicorn in production mode
exec uvicorn \
    --proxy-headers \
    --host "${HOST}" \
    --port "${PORT}" \
    --log-level "${LOG_LEVEL}" \
    --factory \
    app.api_app:create_api_app
