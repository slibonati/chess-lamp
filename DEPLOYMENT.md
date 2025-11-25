# Deployment Guide

This guide covers deploying Chess Lamp using Docker.

## Quick Start

```bash
# 1. Initial setup (install dependencies, create config)
./deploy.sh setup

# 2. Edit config.json with your API credentials
nano config.json

# 3. Deploy using Docker
./deploy.sh docker
```

## Docker Deployment 🐳

**Best for:** Any machine with Docker, easy updates, isolation

**Requirements:**
- Docker and Docker Compose installed
- Network access to Govee lamp (same WiFi)

**Steps:**

```bash
# Option A: Using environment variables
export LICHESS_TOKEN="your_token"
export GOVEE_API_KEY="your_key"
export GOVEE_DEVICE_MAC="your_mac"
./deploy.sh docker

# Option B: Using config.json
# Edit config.json first, then:
./deploy.sh docker
```

**Manage:**
```bash
docker compose logs -f          # View logs
docker compose stop             # Stop
docker compose restart          # Restart
docker compose down             # Remove
```

**Advantages:**
- ✅ Isolated environment
- ✅ Easy to update
- ✅ Works on any OS with Docker
- ✅ Automatic restarts

---

## Deployment Targets

### Raspberry Pi

```bash
# On your Raspberry Pi
git clone <your-repo> /home/pi/chess-lamp
cd /home/pi/chess-lamp
./deploy.sh setup
nano config.json  # Add your credentials
./deploy.sh docker
```

### Home Server / NAS

```bash
# On your server
git clone <your-repo> /opt/chess-lamp
cd /opt/chess-lamp
./deploy.sh setup
nano config.json
./deploy.sh docker
```

### Cloud VM / VPS

**Note:** Your Govee lamp must be accessible from the cloud. Options:
1. Use a VPN to connect VM to your home network
2. Use Govee's cloud API (if available)
3. Run a local proxy/bridge service

---

## Configuration

### Using config.json

1. Copy the example:
   ```bash
   cp config.json.example config.json
   ```

2. Edit with your credentials:
   ```json
   {
     "lichess_token": "your_lichess_token",
     "govee_api_key": "your_govee_api_key",
     "govee_device_mac": "AA:BB:CC:DD:EE:FF",
     "govee_device_ip": "192.168.1.179"
   }
   ```

### Using Environment Variables

For Docker, create a `.env` file:
```bash
LICHESS_TOKEN=your_token
GOVEE_API_KEY=your_key
GOVEE_DEVICE_MAC=your_mac
GOVEE_DEVICE_IP=192.168.1.179
```

---

## Network Requirements

The deployment machine needs:

1. **Internet Access** - To reach Lichess API
2. **Local Network Access** - To control Govee lamp (same WiFi network)

**Testing connectivity:**
```bash
# Test internet
ping -c 3 lichess.org

# Test local network (if you know lamp IP)
ping -c 3 <govee_lamp_ip>
```

---

## Troubleshooting

### Service won't start

1. Check configuration:
   ```bash
   cat config.json  # Verify credentials are set
   ```

2. Test manually:
   ```bash
   docker compose run --rm chess-lamp python3 chess_lamp.py
   ```

3. Check logs:
   ```bash
   docker compose logs -f
   ```

### Lamp not responding

1. Verify device MAC address in config
2. Ensure machine is on same WiFi network
3. Check Govee API key is valid
4. Try controlling lamp manually with Govee app

### Game not detected

1. Verify Lichess API token is valid
2. Check you have an active game on Lichess
3. Test API connection:
   ```python
   import berserk
   client = berserk.Client(session=berserk.TokenSession("your_token"))
   print(list(client.games.get_ongoing()))
   ```

---

## Updating

```bash
cd /path/to/chess-lamp
git pull
docker compose up -d --build
```

---

## Security Notes

- ⚠️ Never commit `config.json` to git (it's in `.gitignore`)
- ⚠️ Keep your API tokens secure
- ⚠️ Use environment variables in production if possible
- ⚠️ Consider using a secrets manager for production deployments

---

## Next Steps

After deployment:

1. Verify the service is running: `docker compose ps`
2. Check logs: `docker compose logs -f`
3. Start a game on Lichess
4. Watch the lamp change colors based on turns!

For issues or questions, check the main README.md or open an issue.
