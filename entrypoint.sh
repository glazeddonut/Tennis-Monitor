#!/usr/bin/env bash
set -euo pipefail

# Entry point for the Tennis Monitor Docker container.
# This script simply runs the monitor using the container's Python environment.

cd /app

# If the user wants headful mode, they can set BOOKING_HEADLESS=false in the container env
if [ "${BOOKING_HEADLESS-true}" = "false" ]; then
  export PLAYWRIGHT_HEADLESS=0
else
  export PLAYWRIGHT_HEADLESS=1
fi

exec python -m main
