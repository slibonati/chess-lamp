# CI/CD Deployment Guide

This guide explains how to set up automated deployment for chess-lamp using GitHub Actions and automatic updates on your remote machine.

## Quick Start (10 minutes)

**For the simplest setup using Watchtower:**

1. **Push this code** - GitHub Actions will automatically build and push the image
2. **Set up GHCR** (first time only):
   - After workflow completes, go to **Packages** tab in GitHub
   - Set package visibility to **Public** (or create PAT for private)
   - See [deploy/ghcr-setup.md](deploy/ghcr-setup.md) for detailed steps
3. **On remote machine:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/chess-lamp.git
   cd chess-lamp
   cp config.json.example config.json
   nano config.json  # Add your API credentials
   # Edit docker-compose.prod.yml: replace 'slibonati' with your GitHub username
   ./deploy/watchtower-setup.sh
   docker compose -f docker-compose.prod.yml up -d
   ```

That's it! Watchtower will automatically update your container when new images are available.

**New to GHCR?** See [deploy/ghcr-setup.md](deploy/ghcr-setup.md) for a quick setup guide.

## Overview

The CI/CD pipeline works as follows:

1. **GitHub Actions** builds and pushes Docker image to GitHub Container Registry (GHCR) on code changes
2. **Remote Machine** automatically pulls the latest image and restarts the container

## Prerequisites

- GitHub repository (public or private)
- Remote machine with Docker and Docker Compose installed
- Network access from remote machine to GitHub Container Registry

## Step 1: GitHub Container Registry (GHCR) Setup

### First Time Setup

**GitHub Container Registry (GHCR) is free and integrated with GitHub!** No separate account needed.

1. **Push this code to GitHub** - The workflow will automatically build and push on first run
2. **After first build, configure package visibility:**
   - Go to your GitHub repository
   - Click on **Packages** (right sidebar, or go to `https://github.com/YOUR_USERNAME?tab=packages`)
   - Find `chess-lamp` package
   - Click on it → **Package settings** → **Change visibility**
   - Choose:
     - **Public** (recommended for public repos) - Anyone can pull, no auth needed
     - **Private** - Only you/your org can pull, requires authentication

### GitHub Actions Setup

The GitHub Actions workflow is already configured in `.github/workflows/docker-build.yml`. It will:

- Trigger on pushes to `main` branch
- Build Docker image
- Push to `ghcr.io/<your-username>/chess-lamp:latest`
- **No additional setup needed** - GitHub Actions uses the built-in `GITHUB_TOKEN` automatically

### Manual Trigger

You can also manually trigger the workflow:
1. Go to **Actions** tab in GitHub
2. Select **Build and Push Docker Image**
3. Click **Run workflow**

### Verify Image Was Created

After pushing code or triggering workflow:
1. Check **Actions** tab - workflow should complete successfully
2. Go to **Packages** (or visit `https://github.com/YOUR_USERNAME?tab=packages`)
3. You should see `chess-lamp` package with version tags

## Step 2: Update Image Name in docker-compose.prod.yml

**Important:** Update `docker-compose.prod.yml` with your actual GitHub username and repository name:

```yaml
image: ghcr.io/YOUR_USERNAME/chess-lamp:latest
```

For example, if your GitHub username is `slibonati` and repo is `chess-lamp`:
```yaml
image: ghcr.io/slibonati/chess-lamp:latest
```

## Step 3: Configure Remote Machine

On your remote machine, you have **three options** for automatic updates:

### Option A: Watchtower (Recommended - Easiest)

Watchtower automatically monitors your containers and updates them when new images are available.

**Setup:**

```bash
# 1. Clone or copy your chess-lamp directory to remote machine
cd ~
git clone https://github.com/your-username/chess-lamp.git
cd chess-lamp

# 2. Create config.json
cp config.json.example config.json
nano config.json  # Add your API credentials

# 3. Update docker-compose.prod.yml with your image
# Edit docker-compose.prod.yml and set:
#   image: ghcr.io/your-username/chess-lamp:latest

# 4. Add label to chess-lamp service in docker-compose.prod.yml:
services:
  chess-lamp:
    image: ghcr.io/your-username/chess-lamp:latest
    labels:
      - com.centurylinklabs.watchtower.enable=true
    # ... rest of config

# 5. Run Watchtower setup script
chmod +x deploy/watchtower-setup.sh
./deploy/watchtower-setup.sh

# 6. Start chess-lamp
docker compose -f docker-compose.prod.yml up -d
```

**How it works:**
- Watchtower checks for new images every 5 minutes
- When a new image is detected, it automatically pulls and restarts the container
- Old images are cleaned up automatically

**View logs:**
```bash
docker compose -f docker-compose.watchtower.yml logs -f
```

### Option B: Webhook Receiver (More Control)

A webhook receiver listens for GitHub webhooks and triggers deployment when code is pushed.

**Setup:**

```bash
# 1. On remote machine, set up webhook receiver
cd ~/chess-lamp
chmod +x deploy/webhook-receiver.sh

# 2. Set environment variables
export DEPLOY_DIR="$HOME/chess-lamp"
export COMPOSE_FILE="docker-compose.prod.yml"
export WEBHOOK_SECRET="your-secret-here"  # Choose a strong secret
export PORT=9000

# 3. Run as a service (using systemd)
sudo nano /etc/systemd/system/chess-lamp-webhook.service
```

**Systemd service file:**
```ini
[Unit]
Description=Chess Lamp Webhook Receiver
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/chess-lamp
Environment="DEPLOY_DIR=/home/your-username/chess-lamp"
Environment="COMPOSE_FILE=docker-compose.prod.yml"
Environment="WEBHOOK_SECRET=your-secret-here"
Environment="PORT=9000"
ExecStart=/home/your-username/chess-lamp/deploy/webhook-receiver.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable chess-lamp-webhook
sudo systemctl start chess-lamp-webhook

# Check status
sudo systemctl status chess-lamp-webhook
```

**Configure GitHub Webhook:**

1. Go to your GitHub repository
2. **Settings** → **Webhooks** → **Add webhook**
3. **Payload URL**: `http://your-remote-machine-ip:9000` (or use a reverse proxy)
4. **Content type**: `application/json`
5. **Secret**: Same as `WEBHOOK_SECRET` you set above
6. **Events**: Select "Just the push event"
7. **Active**: ✅
8. Click **Add webhook**

**Note:** If your remote machine is behind a firewall, you may need to:
- Set up port forwarding
- Use a reverse proxy (nginx, Caddy)
- Use a tunneling service (ngrok, Cloudflare Tunnel)

### Option C: Cron Job Polling (Simple but Less Efficient)

A cron job periodically checks for new images and updates.

**Setup:**

```bash
# 1. Make script executable
chmod +x deploy/poll-update.sh

# 2. Add to crontab (check every 5 minutes)
crontab -e

# Add this line:
*/5 * * * * /home/your-username/chess-lamp/deploy/poll-update.sh
```

**How it works:**
- Script runs every 5 minutes
- Pulls latest image
- If image changed, restarts container
- Cleans up old images

## Step 4: Authentication (Private Repositories)

If your repository is **private**, you need to authenticate with GHCR on your remote machine:

```bash
# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# Or create a Personal Access Token (PAT) with read:packages permission
# Then login:
docker login ghcr.io -u YOUR_USERNAME -p YOUR_PAT
```

**For Watchtower with private repos:**

Add authentication to Watchtower:

```yaml
# In docker-compose.watchtower.yml
services:
  watchtower:
    environment:
      - DOCKER_USERNAME=YOUR_USERNAME
      - DOCKER_PASSWORD=YOUR_PAT
```

## Step 5: Test Image Pull

Before deploying, test that you can pull the image:

```bash
# For public packages (no auth needed):
docker pull ghcr.io/YOUR_USERNAME/chess-lamp:latest

# For private packages (auth required first):
docker login ghcr.io -u YOUR_USERNAME -p YOUR_PAT
docker pull ghcr.io/YOUR_USERNAME/chess-lamp:latest
```

If this works, you're ready to deploy!

## Step 6: Initial Deployment

```bash
# 1. Pull the image
docker compose -f docker-compose.prod.yml pull

# 2. Start the container
docker compose -f docker-compose.prod.yml up -d

# 3. Check logs
docker compose -f docker-compose.prod.yml logs -f
```

## Verification

After setup, test the deployment:

1. Make a small change to the code
2. Push to `main` branch
3. GitHub Actions will build and push new image
4. Within 5 minutes (or immediately with webhook), your remote machine should update

**Check if update worked:**
```bash
# View container logs
docker compose -f docker-compose.prod.yml logs -f

# Check image version
docker compose -f docker-compose.prod.yml images

# Check Watchtower logs (if using Option A)
docker compose -f docker-compose.watchtower.yml logs -f
```

## Troubleshooting

### Image not found (404)

- Verify image name matches: `ghcr.io/your-username/chess-lamp:latest`
- Check repository visibility (private repos need authentication)
- Verify GitHub Actions workflow completed successfully

### Container not updating

**Watchtower:**
- Check Watchtower logs: `docker compose -f docker-compose.watchtower.yml logs`
- Verify label is set: `com.centurylinklabs.watchtower.enable=true`
- Check Watchtower is running: `docker ps | grep watchtower`

**Webhook:**
- Test webhook manually: `curl http://localhost:9000/deploy`
- Check webhook logs: `sudo journalctl -u chess-lamp-webhook -f`
- Verify GitHub webhook is receiving events (check in GitHub webhook settings)

**Cron:**
- Check cron logs: `tail -f /var/log/chess-lamp-update.log`
- Verify cron job is running: `crontab -l`

### Authentication issues

- Verify GHCR token has `read:packages` permission
- Check token hasn't expired
- Try logging in manually: `docker login ghcr.io`

## Comparison of Options

| Option | Pros | Cons | Best For |
|--------|------|------|----------|
| **Watchtower** | ✅ Easiest setup<br>✅ Automatic cleanup<br>✅ No webhook needed | ⚠️ Polls every 5 min (not instant) | Most users |
| **Webhook** | ✅ Instant updates<br>✅ More control<br>✅ Can add custom logic | ⚠️ Requires webhook setup<br>⚠️ Needs network access | Production setups |
| **Cron** | ✅ Simple<br>✅ No extra services | ⚠️ Less efficient<br>⚠️ Polls even when no updates | Simple setups |

## Security Considerations

1. **Webhook Secret**: Always use a strong secret for webhook authentication
2. **Firewall**: Only expose webhook port if necessary, or use a reverse proxy
3. **GHCR Tokens**: Use fine-grained PATs with minimal permissions
4. **Network**: Consider using VPN or SSH tunnel for webhook access

## Next Steps

- Set up monitoring/alerting for failed deployments
- Add deployment notifications (Slack, Discord, email)
- Implement rollback mechanism
- Add health checks

