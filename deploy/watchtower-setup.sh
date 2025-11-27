#!/bin/bash
# Setup script for Watchtower - automatic container updates
# This is the EASIEST option for auto-deployment

set -e

echo "Setting up Watchtower for automatic chess-lamp updates..."

# Create docker-compose file for Watchtower
cat > docker-compose.watchtower.yml << 'EOF'
name: watchtower

services:
  watchtower:
    image: containrrr/watchtower
    container_name: watchtower
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - WATCHTOWER_CLEANUP=true  # Remove old images after update
      - WATCHTOWER_POLL_INTERVAL=300  # Check every 5 minutes
      - WATCHTOWER_INCLUDE_STOPPED=false
      - WATCHTOWER_REVIVE_STOPPED=false
      # Only watch chess-lamp container
      - WATCHTOWER_LABEL_ENABLE=true
    command: --label-enable chess-lamp
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
EOF

# Add label to chess-lamp service
echo ""
echo "Add this label to your chess-lamp service in docker-compose.prod.yml:"
echo ""
echo "  chess-lamp:"
echo "    labels:"
echo "      - com.centurylinklabs.watchtower.enable=true"
echo ""

# Start Watchtower
echo "Starting Watchtower..."
docker compose -f docker-compose.watchtower.yml up -d

echo ""
echo "✅ Watchtower is now running!"
echo ""
echo "Watchtower will:"
echo "  - Check for new images every 5 minutes"
echo "  - Automatically pull and restart chess-lamp when new image is available"
echo "  - Clean up old images after update"
echo ""
echo "To view Watchtower logs:"
echo "  docker compose -f docker-compose.watchtower.yml logs -f"
echo ""
echo "To stop Watchtower:"
echo "  docker compose -f docker-compose.watchtower.yml down"

