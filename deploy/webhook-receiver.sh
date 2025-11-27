#!/bin/bash
# Webhook receiver script for auto-deploying chess-lamp
# Run this on your remote machine to listen for deployment webhooks

set -e

# Configuration
DEPLOY_DIR="${DEPLOY_DIR:-/home/$(whoami)/chess-lamp}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
LOG_FILE="${LOG_FILE:-/var/log/chess-lamp-deploy.log}"
WEBHOOK_SECRET="${WEBHOOK_SECRET:-your-secret-here}"  # Set this in your environment
PORT="${PORT:-9000}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

deploy() {
    log_info "Starting deployment..."
    
    cd "$DEPLOY_DIR" || {
        log_error "Deploy directory not found: $DEPLOY_DIR"
        exit 1
    }
    
    # Pull latest image
    log_info "Pulling latest image..."
    docker compose -f "$COMPOSE_FILE" pull chess-lamp || {
        log_error "Failed to pull image"
        exit 1
    }
    
    # Restart container with new image
    log_info "Restarting container..."
    docker compose -f "$COMPOSE_FILE" up -d --force-recreate chess-lamp || {
        log_error "Failed to restart container"
        exit 1
    }
    
    # Clean up old images
    log_info "Cleaning up old images..."
    docker image prune -f
    
    log_info "Deployment complete!"
    
    # Show container status
    docker compose -f "$COMPOSE_FILE" ps
}

# Handle command line arguments
if [ "$1" == "deploy" ]; then
    deploy
    exit 0
fi

# Simple HTTP server using Python
if ! command -v python3 &> /dev/null; then
    log_error "python3 is required for webhook receiver"
    exit 1
fi

log_info "Starting webhook receiver on port $PORT..."
log_info "Set WEBHOOK_SECRET environment variable for security"
log_info "Deploy directory: $DEPLOY_DIR"

python3 << EOF
import http.server
import socketserver
import json
import os
import subprocess
import hmac
import hashlib
import threading

PORT = int(os.environ.get('PORT', $PORT))
SECRET = os.environ.get('WEBHOOK_SECRET', '$WEBHOOK_SECRET')
DEPLOY_DIR = os.environ.get('DEPLOY_DIR', '$DEPLOY_DIR')
SCRIPT_PATH = '$0'

def deploy_async():
    """Run deployment in background"""
    subprocess.run(['/bin/bash', SCRIPT_PATH, 'deploy'], cwd=DEPLOY_DIR)

class WebhookHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        # Verify secret if provided
        if SECRET and SECRET != 'your-secret-here':
            sig = self.headers.get('X-Hub-Signature-256', '')
            if sig:
                expected = 'sha256=' + hmac.new(
                    SECRET.encode(),
                    body,
                    hashlib.sha256
                ).hexdigest()
                if not hmac.compare_digest(sig, expected):
                    self.send_response(401)
                    self.end_headers()
                    self.wfile.write(b'Invalid signature')
                    return
        
        # Parse webhook payload
        try:
            payload = json.loads(body.decode())
            event = self.headers.get('X-GitHub-Event', '')
            
            # Only deploy on push to main
            if event == 'push' and payload.get('ref') == 'refs/heads/main':
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'Deployment triggered')
                
                # Trigger deployment in background thread
                thread = threading.Thread(target=deploy_async)
                thread.daemon = True
                thread.start()
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'Event ignored')
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())
    
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
        elif self.path == '/deploy':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Manual deploy triggered')
            thread = threading.Thread(target=deploy_async)
            thread.daemon = True
            thread.start()
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")

with socketserver.TCPServer(("", PORT), WebhookHandler) as httpd:
    print(f"Webhook receiver listening on port {PORT}")
    print(f"Health check: http://localhost:{PORT}/health")
    print(f"Manual deploy: http://localhost:{PORT}/deploy")
    httpd.serve_forever()
EOF
