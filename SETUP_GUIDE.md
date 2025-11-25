# Setup Guide: Obtaining API Keys and Credentials

This guide walks you through obtaining all the required credentials for Chess Lamp.

## Required Information

You need **3 pieces of information**:

1. **Lichess API Token** - To monitor your chess games
2. **Govee API Key** - To control your Govee lamp
3. **Govee Device MAC Address** - To identify your specific lamp

---

## 1. Lichess API Token

### Step-by-Step Instructions

1. **Log in to Lichess**
   - Go to [lichess.org](https://lichess.org/) and sign in to your account
   - If you don't have an account, create one (it's free)

2. **Navigate to API Token Page**
   - Go directly to: [https://lichess.org/account/oauth/token/create](https://lichess.org/account/oauth/token/create)
   - Or: Click your username → Preferences → API → Personal API Access Tokens

3. **Create a New Token**
   - Click **"Create a new token"** or **"Generate Token"**
   - **Description**: Enter something like "Govee Lamp Integration" or "Chess Game Monitor"
   - **Scopes/Permissions**: You'll see a list of checkboxes or toggles. Look for and select:
     - ✅ **Anything related to "games" or "ongoing games"** (REQUIRED - this is essential!)
     - ✅ **Anything related to "account" or "user info"** (needed to identify which player you are)
     - ✅ **"board:play" or "Board API" or "board play"** (REQUIRED - needed to stream game events!)
       - ⚠️ **This is critical!** Without this, you'll get "Missing scope: board:play" errors
     - ⚠️ **Note**: The exact wording may vary. Common names you might see:
       - "Read ongoing games" or "game:read" or "games:read"
       - "Read account info" or "account:read" or "user:read"
       - "Board API" or "board:play" or "stream game state"
     - 💡 **Tip**: If you're unsure, you can select most read permissions - it's better to have more than less for this integration
   - Click **"Generate Token"** or **"Create"**

4. **Copy Your Token**
   - ⚠️ **IMPORTANT**: Copy the token immediately - you won't be able to see it again!
   - The token will look something like: `lip_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - Store it securely (you'll need it for the config file)

### Token Format
- Starts with `lip_` followed by a long string of characters
- Example: `lip_AbCdEf1234567890XyZ`

### What Permissions Does the Code Actually Need?

The integration code uses these Lichess API endpoints:
- `games.get_ongoing()` - To detect when you have an active game
- `account.get()` - To get your username and identify which color you're playing
- `board.stream_game_state()` - To monitor game moves in real-time

**If you can't find exact permission names**, look for:
- Any permission that mentions **"games"** or **"ongoing"**
- Any permission that mentions **"account"** or **"user"** or **"profile"**
- Any permission that mentions **"board"** or **"stream"**

**If the interface just has checkboxes without clear labels:**
- Select all the "read" permissions (not "write" unless you want to make moves)
- The token will work as long as it can read your games and account info

---

## 2. Govee API Key

### Method 1: Through Govee Home App (Recommended)

1. **Open Govee Home App**
   - Install the Govee Home app on your phone if you haven't already
   - Log in to your Govee account

2. **Navigate to Settings**
   - Tap the **profile icon** (bottom right corner)
   - Tap the **settings gear icon** (top right corner)

3. **Apply for API Key**
   - Look for **"Apply for API Key"** or **"Developer"** or **"API"** option
   - Fill in the application form:
     - **Name**: Your name
     - **Reason for Application**: Something like "Personal home automation project" or "Integration with chess game monitor"
   - Agree to terms and conditions
   - Submit the application

4. **Receive API Key**
   - Govee will send the API key to your registered email address
   - This usually takes a few minutes to a few hours
   - Check your email (and spam folder)

### Method 2: Email Govee Support (Alternative)

If you can't find the option in the app:

1. **Send an Email**
   - Email: [support@govee.com](mailto:support@govee.com)
   - Subject: "API Key Request for Home Automation"
   - Include:
     - Your Govee account email
     - Brief explanation: "I want to integrate my Govee lamp with a chess game monitor"
     - Your device model (if known)

2. **Wait for Response**
   - Govee support will send you an API key via email
   - This may take 1-2 business days

### API Key Format
- Usually a long alphanumeric string
- Example: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` or just a long string

---

## 3. Govee Device MAC Address

The MAC address is a unique identifier for your specific Govee lamp.

### Method 1: Through Govee Home App (Easiest)

1. **Open Govee Home App**
   - Make sure your lamp is connected and visible in the app

2. **Find Your Device**
   - Tap on your lamp/device in the device list

3. **Access Device Settings**
   - Tap the **settings/gear icon** for that device
   - Or tap **"Device Settings"** or **"Device Info"**

4. **Find MAC Address**
   - Look for **"MAC Address"**, **"Device MAC"**, or **"MAC"**
   - It will be in format: `AA:BB:CC:DD:EE:FF` or `AA-BB-CC-DD-EE-FF`
   - Copy this value

### Method 2: Check Device Label

Some Govee devices have the MAC address printed on:
- The device itself (check the bottom or back)
- The original packaging
- The user manual

### Method 3: Using Govee API (If You Have API Key)

Once you have your Govee API key, you can list all your devices:

```python
from govee_api_laggat import Govee

govee = Govee(api_key="your_api_key")
devices = govee.get_devices()
for device in devices:
    print(f"Device: {device['deviceName']}, MAC: {device['device']}")
```

### MAC Address Format
- Format: `AA:BB:CC:DD:EE:FF` (with colons) or `AA-BB-CC-DD-EE-FF` (with dashes)
- Example: `A4:C1:38:XX:XX:XX`
- The code should handle both formats, but colons are preferred

---

## 4. Creating Your Config File

Once you have all three pieces of information:

1. **Copy the example config:**
   ```bash
   cp config.json.example config.json
   ```

2. **Edit config.json:**
   ```json
   {
     "lichess_token": "lip_your_actual_token_here",
     "govee_api_key": "your_actual_govee_api_key_here",
     "govee_device_mac": "AA:BB:CC:DD:EE:FF"
   }
   ```

3. **Replace the placeholder values** with your actual credentials

### Example:
```json
{
  "lichess_token": "lip_AbCdEf1234567890XyZ",
  "govee_api_key": "abc123def456ghi789",
  "govee_device_mac": "A4:C1:38:12:34:56"
}
```

---

## 5. Alternative: Using Environment Variables

Instead of `config.json`, you can set environment variables:

```bash
export LICHESS_TOKEN="lip_your_token_here"
export GOVEE_API_KEY="your_api_key_here"
export GOVEE_DEVICE_MAC="AA:BB:CC:DD:EE:FF"
```

Then run the script:
```bash
python chess_lamp.py
```

---

## Troubleshooting

### Can't find Lichess API token page?
- Direct link: https://lichess.org/account/oauth/token/create
- Make sure you're logged in first

### Don't see the exact permission names listed?
- **This is normal!** Lichess may have updated their interface or use different wording
- Look for any checkboxes/toggles related to:
  - **Games** (ongoing games, game state, etc.)
  - **Account** (user info, profile, etc.)
  - **Board** (board API, game streaming, etc.)
- **If you see technical scope names** like `game:read`, `account:read`, `board:play`, those are the correct ones
- **If unsure**: Select all "read" permissions - having extra read permissions won't hurt
- **Minimum needed**: Something that lets you read your ongoing games and account info

### Govee API key not in app?
- Try updating the Govee Home app to the latest version
- Look for "Developer" or "API" in settings
- Email support@govee.com as backup

### Can't find MAC address?
- Make sure your device is connected to the Govee app
- Check device settings/info in the app
- Some devices show it in the device name or details
- Try the API method if you have your API key

### Testing Your Credentials

**Test Lichess Token:**
```python
import berserk
client = berserk.Client(session=berserk.TokenSession("your_token"))
print(client.account.get())  # Should print your account info
```

**Test Govee API Key:**
```python
from govee_api_laggat import Govee
govee = Govee(api_key="your_key")
devices = govee.get_devices()
print(devices)  # Should list your devices
```

---

## Security Reminders

⚠️ **IMPORTANT SECURITY NOTES:**

- ❌ **NEVER** commit `config.json` to git (it should be in `.gitignore`)
- ❌ **NEVER** share your API keys publicly
- ✅ Store keys securely
- ✅ Use environment variables in production if possible
- ✅ Regenerate tokens if you suspect they're compromised

---

## Next Steps

Once you have all three credentials configured:

1. Test the setup:
   ```bash
   python chess_lamp.py
   ```

2. Start a game on Lichess and watch your lamp change colors!

3. See [DEPLOYMENT.md](DEPLOYMENT.md) for running as a service.

---

## Still Need Help?

- Check the main [README.md](README.md) for usage instructions
- Review [DEPLOYMENT.md](DEPLOYMENT.md) for deployment options
- Make sure your Govee lamp is on the same WiFi network as the machine running the script

