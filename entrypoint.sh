#!/usr/bin/env bash
set -euo pipefail

# Entry point for the Tennis Monitor Docker container.
# Runs the API server with integrated monitor in background.

cd /app

# If the user wants headful mode, they can set BOOKING_HEADLESS=false in the container env
if [ "${BOOKING_HEADLESS-true}" = "false" ]; then
  export PLAYWRIGHT_HEADLESS=0
else
  export PLAYWRIGHT_HEADLESS=1
fi

exec python -m api_server
