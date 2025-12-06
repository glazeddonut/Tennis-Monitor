#!/usr/bin/env bash
set -euo pipefail

# Deploy the Tennis Monitor project to a remote NAS from GitHub and start it with Docker Compose.
# Usage:
#   ./scripts/deploy_to_nas.sh USER@NAS_HOST /remote/path/to/project [options]
#
# Example:
#   ./scripts/deploy_to_nas.sh pi@nas.local /home/pi/tennis-monitor
#
# Environment variables used:
#  SKIP_BUILD   - If set, skip `docker compose build` on the NAS
#  SSH_OPTS     - Extra ssh options (optional)
#  GITHUB_REPO  - GitHub repository (default: glazeddonut/Tennis-Monitor)
#  GITHUB_BRANCH - Git branch to deploy (default: main)

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <user@nas> <remote_path>"
  echo "Example: $0 pi@nas.local /home/pi/tennis-monitor"
  exit 2
fi

REMOTE="$1"
REMOTE_PATH="$2"

# GitHub configuration
GITHUB_REPO="${GITHUB_REPO:-glazeddonut/Tennis-Monitor}"
GITHUB_BRANCH="${GITHUB_BRANCH:-main}"
GITHUB_URL="https://github.com/${GITHUB_REPO}.git"

echo "GitHub repository: $GITHUB_URL"
echo "Branch: $GITHUB_BRANCH"
echo "Deploy target: $REMOTE:$REMOTE_PATH"

if [ -z "${SSH_OPTS-}" ]; then
  SSH_OPTS=( -o StrictHostKeyChecking=accept-new )
else
  read -r -a SSH_OPTS <<< "$SSH_OPTS"
fi

echo "Cloning/pulling project from GitHub on NAS..."
SSH_CMD="if [ -d '$REMOTE_PATH/.git' ]; then cd '$REMOTE_PATH' && git fetch origin && git checkout $GITHUB_BRANCH && git pull origin $GITHUB_BRANCH; else git clone -b $GITHUB_BRANCH '$GITHUB_URL' '$REMOTE_PATH'; fi"
ssh "${SSH_OPTS[@]}" "$REMOTE" "$SSH_CMD"


echo "Deploying on NAS..."
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
echo ""
echo "To update in the future, just run this script again:"
echo "  ./scripts/deploy_to_nas.sh $REMOTE $REMOTE_PATH"
