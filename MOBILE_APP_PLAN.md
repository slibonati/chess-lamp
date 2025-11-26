# Mobile App Plan for Chess-Lamp Control

## Overview
Create an Android app (and potentially iOS) to control chess-lamp settings in real-time.

## Architecture

### Backend (Chess-Lamp)
1. **Add HTTP API Server** to chess-lamp.py
   - Use Flask or FastAPI (lightweight, easy)
   - RESTful endpoints for:
     - GET `/api/status` - Current theme, colors, brightness, game status
     - POST `/api/theme` - Change theme
     - POST `/api/colors` - Set custom colors
     - POST `/api/brightness` - Adjust brightness
     - POST `/api/dimming` - Toggle/enable dimming settings
     - GET `/api/themes` - List all available themes

2. **API Features:**
   - Real-time status updates
   - Hot reload support (already implemented)
   - CORS enabled for mobile app
   - Simple authentication (optional API key)

### Android App
1. **Tech Stack Options:**
   - **Option A: Native Android (Kotlin)**
     - Best performance, native feel
     - More work, but full control
   
   - **Option B: React Native / Flutter**
     - Cross-platform (Android + iOS)
     - Faster development
     - Good performance

   - **Option C: Progressive Web App (PWA)**
     - Works on any device with browser
     - No app store needed
     - Easiest to deploy

2. **App Features:**
   - Theme selector (dropdown/list)
   - Color preview
   - Brightness sliders
   - Dimming toggle and duration
   - Current game status (if playing)
   - Quick theme buttons
   - Settings persistence

## Implementation Steps

### Phase 1: Backend API
1. Add Flask/FastAPI to requirements.txt
2. Create API endpoints in chess_lamp.py
3. Run API server in separate thread
4. Test with curl/Postman

### Phase 2: Android App (Native)
1. Create Android project structure
2. UI with Material Design
3. HTTP client to connect to chess-lamp API
4. Theme selector and controls
5. Real-time status updates

### Phase 3: Polish
1. Error handling
2. Connection management
3. Settings persistence
4. Notifications (optional)

## Quick Start: Web Interface First?

We could start with a simple web interface that works on mobile browsers:
- Single HTML page with JavaScript
- Works on Android, iOS, desktop
- No app store needed
- Can be served by the Flask API

Then build native app later if desired.

## Next Steps

Would you like me to:
1. **Start with web interface** (fastest, works everywhere)
2. **Build native Android app** (better UX, more work)
3. **Both** (web first, then native)

Let me know and I'll start building!

