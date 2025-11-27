#!/bin/bash
# Simple polling script that checks for new images and updates
# Run this as a cron job (e.g., every 5 minutes)

set -e

DEPLOY_DIR="${DEPLOY_DIR:-/home/$(whoami)/chess-lamp}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
LOG_FILE="${LOG_FILE:-/var/log/chess-lamp-update.log}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

cd "$DEPLOY_DIR" || exit 1

# Get current image digest
CURRENT_DIGEST=$(docker compose -f "$COMPOSE_FILE" images chess-lamp | tail -n +2 | awk '{print $3}' || echo "")

log "Checking for updates (current: $CURRENT_DIGEST)..."

# Pull latest image
docker compose -f "$COMPOSE_FILE" pull chess-lamp

# Get new image digest
NEW_DIGEST=$(docker compose -f "$COMPOSE_FILE" images chess-lamp | tail -n +2 | awk '{print $3}' || echo "")

if [ "$CURRENT_DIGEST" != "$NEW_DIGEST" ]; then
    log "New image detected! Updating container..."
    docker compose -f "$COMPOSE_FILE" up -d --force-recreate chess-lamp
    docker image prune -f
    log "Update complete!"
else
    log "No updates available"
fi

