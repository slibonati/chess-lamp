# Chess Lamp

A Python application that integrates your Govee table lamp with Lichess chess games. The lamp changes color based on whose turn it is during gameplay.

## Features

- 🎮 Monitors active Lichess games in real-time
- 💡 Automatically changes lamp color based on whose turn it is
- 🔵 Blue light when it's your turn
- 🔴 Red light when it's your opponent's turn
- ⚪ Gray light when the game is over

## Prerequisites

- Python 3.7 or higher
- A Lichess account
- A Govee table lamp connected to your network (WiFi)
- API credentials for both services
- **Network Requirements**: The machine running this service needs:
  - Internet access (to reach Lichess API)
  - Access to the same network as your Govee lamp (typically same WiFi network)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Lichess API Token

1. Go to [Lichess API Tokens](https://lichess.org/account/oauth/token/create)
2. Create a new token with appropriate permissions
3. Copy the token

### 3. Get Govee API Credentials

You'll need:
- **Govee API Key**: Get this from the Govee developer portal or app
- **Device MAC Address**: Find this in your Govee Home app under device settings

**Note**: This project uses `govee-api-laggat`, a community library for controlling Govee devices. You can also try other libraries like `govee-api` or `aiogovee` if needed.

### 4. Configure the Application

Copy the example config file and fill in your credentials:

```bash
cp config.json.example config.json
```

Edit `config.json` with your credentials:

```json
{
  "lichess_token": "your_lichess_api_token_here",
  "govee_api_key": "your_govee_api_key_here",
  "govee_device_mac": "your_device_mac_address_here"
}
```

**Alternatively**, you can set environment variables:

```bash
export LICHESS_TOKEN="your_token"
export GOVEE_API_KEY="your_key"
export GOVEE_DEVICE_MAC="your_mac"
```

## Usage

### Running Directly

Run the application directly:

```bash
python chess_lamp.py
```

The application will:
1. Monitor for active Lichess games
2. When a game is detected, start streaming game events
3. Update the lamp color based on whose turn it is

### Running as a Service

**The application can run on any machine on your network** - it doesn't need to be on the same computer where you're playing Lichess. It only needs:
- Internet access to reach the Lichess API
- Network access to your Govee lamp (same WiFi network)

#### Option 1: Simple Background Service (Recommended)

Use the provided script to run as a background service:

```bash
# Make the script executable
chmod +x run_service.sh

# Start the service
./run_service.sh start

# Check status
./run_service.sh status

# Stop the service
./run_service.sh stop

# View logs
tail -f lichess_govee.log
```

#### Option 2: Systemd Service (Linux)

For a more robust system service on Linux:

1. Edit `lichess-govee.service` and update:
   - `YOUR_USERNAME` with your actual username
   - Paths if needed

2. Install the service:
   ```bash
   sudo cp lichess-govee.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable lichess-govee.service
   sudo systemctl start lichess-govee.service
   ```

3. Manage the service:
   ```bash
   sudo systemctl status lichess-govee.service
   sudo systemctl stop lichess-govee.service
   sudo systemctl restart lichess-govee.service
   sudo journalctl -u lichess-govee.service -f  # View logs
   ```

#### Option 3: Docker Compose (Recommended)

Deploy using Docker Compose for easy setup and management:

```bash
# 1. Create config.json from example
cp config.json.example config.json

# 2. Edit config.json with your API credentials
nano config.json

# 3. Start the container
docker compose up -d

# 4. View logs
docker compose logs -f

# 5. Stop the container
docker compose down

# 6. Restart the container
docker compose restart
```

**Note:** The container uses `network_mode: host` to access your Govee lamp on the local network.

### Color Scheme

- **Blue**: Your turn
- **Red**: Opponent's turn
- **Gray**: Game is over

You can customize these colors in the `ChessLamp` class by modifying:
- `self.my_turn_color`
- `self.opponent_turn_color`
- `self.game_over_color`

## How It Works

1. The application uses the `berserk` library to connect to the Lichess API
2. It monitors for ongoing games using the Lichess Games API
3. When a game is detected, it streams game events in real-time using the Board API
4. Based on the move count and player colors, it determines whose turn it is
5. The Govee lamp color is updated accordingly using the `govee-api-laggat` library

## Troubleshooting

### Lamp not responding

- Ensure your Govee lamp is connected to the same network
- Verify the MAC address is correct
- Check that the Govee API key is valid

### Game not detected

- Make sure you have an active game on Lichess
- Verify your Lichess API token has the correct permissions
- Check your internet connection

### API Errors

- Verify all API credentials are correct
- Check rate limits for both Lichess and Govee APIs
- Ensure you're using the correct API endpoints

## Customization

You can customize the behavior by modifying the `ChessLamp` class:

- **Colors**: Change RGB values in the color dictionaries
- **Brightness**: Adjust brightness levels (0-100)
- **Polling interval**: Modify the sleep time in `monitor_games()`

## Deployment

This service can run on **any machine on your network** - it doesn't need to be on the same computer where you play Lichess.

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for detailed deployment instructions including:
- 🐳 Docker deployment (recommended)
- ⚙️ Systemd service (Linux/Raspberry Pi)
- 🚀 Simple background service
- Quick setup script

**Quick deploy with Docker Compose:**
```bash
# 1. Create and edit config.json
cp config.json.example config.json
nano config.json

# 2. Start the service
docker compose up -d

# 3. View logs
docker compose logs -f
```

## License

This project is provided as-is for personal use.

## Contributing

Feel free to submit issues or pull requests if you'd like to improve this integration!

