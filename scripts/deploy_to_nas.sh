#!/usr/bin/env bash
set -euo pipefail

# Deploy the Tennis Monitor project to a remote NAS and start it with Docker Compose.
# Usage:
#   ./scripts/deploy_to_nas.sh USER@NAS_HOST /remote/path/to/project [options]
#
# Example:
#   ./scripts/deploy_to_nas.sh pi@nas.local /home/pi/tennis-monitor
#
# Environment variables used:
#  RSYNC_OPTS   - Extra rsync options (optional)
#  SKIP_BUILD   - If set, skip `docker compose build` on the NAS
#  SSH_OPTS     - Extra ssh options (optional)

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <user@nas> <remote_path>"
  echo "Example: $0 pi@nas.local /home/pi/tennis-monitor"
  exit 2
fi

REMOTE="$1"
REMOTE_PATH="$2"

HERE=$(cd "$(dirname "$0")/.." && pwd)
echo "Local project: $HERE"
echo "Deploy target: $REMOTE:$REMOTE_PATH"

# Default rsync options
if [ -z "${RSYNC_OPTS-}" ]; then
  RSYNC_OPTS=( -avz --delete --progress )
else
  # split into array
  read -r -a RSYNC_OPTS <<< "$RSYNC_OPTS"
fi

if [ -z "${SSH_OPTS-}" ]; then
  SSH_OPTS=( -o StrictHostKeyChecking=accept-new )
else
  read -r -a SSH_OPTS <<< "$SSH_OPTS"
fi

RSYNC_EXCLUDES=(
  "venv"
  ".git"
  "__pycache__"
  "*.pyc"
  "tests"
  "*.tar"
  "*.egg-info"
)

RSYNC_EXCLUDE_ARGS=()
for e in "${RSYNC_EXCLUDES[@]}"; do
  RSYNC_EXCLUDE_ARGS+=(--exclude="$e")
done

echo "Syncing project to NAS..."
rsync "${RSYNC_OPTS[@]}" "${RSYNC_EXCLUDE_ARGS[@]}" "$HERE/" "$REMOTE:$REMOTE_PATH/"

echo "Copying .env (if present) to NAS and restricting permissions..."
if [ -f "$HERE/.env" ]; then
  scp "${SSH_OPTS[@]}" "$HERE/.env" "$REMOTE:$REMOTE_PATH/.env"
  ssh "${SSH_OPTS[@]}" "$REMOTE" "chmod 600 '$REMOTE_PATH/.env' || true"
else
  echo "Warning: .env not found in project root; ensure config exists on NAS at $REMOTE_PATH/.env"
fi

echo "Running deploy commands on NAS..."
SSH_CMD="cd '$REMOTE_PATH' && docker compose pull || true"
if [ -z "${SKIP_BUILD-}" ]; then
  SSH_CMD+=" && docker compose build"
else
  SSH_CMD+=" && echo 'SKIP_BUILD set; skipping docker compose build'"
fi
SSH_CMD+=" && docker compose up -d --remove-orphans"

echo "SSH -> $REMOTE: running: $SSH_CMD"
ssh "${SSH_OPTS[@]}" "$REMOTE" "$SSH_CMD"

echo "Deployment complete. Check logs with: ssh $REMOTE 'docker compose logs -f tennis-monitor'"
