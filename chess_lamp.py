#!/usr/bin/env python3
"""
Chess Lamp
Monitors Lichess games and controls Govee lamp based on whose turn it is.
"""

import json
import os
import sys
import time
import asyncio
from typing import Optional, Dict, Any
import berserk
import requests

# Try to import LAN controller
try:
    from govee_lan import GoveeLANController
    LAN_CONTROL_AVAILABLE = True
except ImportError:
    GoveeLANController = None
    LAN_CONTROL_AVAILABLE = False

# Try to import Govee library - support multiple implementations
try:
    from govee_api_laggat import Govee
    GOVEE_LIB = 'laggat'
except ImportError:
    try:
        from govee_api import Govee
        GOVEE_LIB = 'standard'
    except ImportError:
        try:
            from aiogovee import Govee
            GOVEE_LIB = 'async'
        except ImportError:
            Govee = None
            GOVEE_LIB = None


class ChessLamp:
    """Main class to integrate Lichess game monitoring with Govee lamp control."""
    
    def __init__(self, lichess_token: str, govee_api_key: str, govee_device_mac: str, govee_device_ip: Optional[str] = None):
        """
        Initialize the integration.
        
        Args:
            lichess_token: Lichess API token
            govee_api_key: Govee API key
            govee_device_mac: MAC address of the Govee device
            govee_device_ip: Optional IP address for LAN control
        """
        self.lichess_token = lichess_token
        self.govee_api_key = govee_api_key
        self.govee_device_mac = govee_device_mac
        self.govee_device_ip = govee_device_ip
        
        # Initialize Lichess client
        self.lichess_client = berserk.Client(session=berserk.TokenSession(lichess_token))
        
        # Initialize Govee client
        if Govee is None:
            raise ImportError("No Govee library found. Please install one of: govee-api-laggat, govee-api, or aiogovee")
        self.govee_client = Govee(api_key=govee_api_key)
        self.govee_lib = GOVEE_LIB
        
        # Get actual device identifier from API (MAC format might differ)
        self.govee_device_id = self._get_device_id_from_api()
        
        # Initialize LAN controller if available
        self.lan_controller = None
        if LAN_CONTROL_AVAILABLE and GoveeLANController:
            try:
                self.lan_controller = GoveeLANController(govee_device_mac, govee_device_ip)
                print("✅ LAN control initialized (using correct H6022 protocol format)")
            except Exception as e:
                print(f"⚠️  Could not initialize LAN controller: {e}")
        
        # Track current game state
        self.current_game_id: Optional[str] = None
        self.is_my_turn: Optional[bool] = None
        self.my_color: Optional[str] = None  # 'white' or 'black'
        self.pre_game_state: Optional[Dict[str, Any]] = None  # Store state before game started
        
        # Color configuration - based on turn (not piece color)
        # Your turn: Bright green
        self.my_turn_color = {'r': 0, 'g': 255, 'b': 0}  # Pure green for your turn
        # Opponent's turn: Red
        self.opponent_turn_color = {'r': 255, 'g': 0, 'b': 0}  # Pure red for opponent's turn
        
        # Brightness configuration (0-100)
        # Uniform brightness during gameplay
        self.my_turn_brightness = 40  # 40% brightness when it's your turn (green)
        self.opponent_turn_brightness = 40  # 40% brightness for opponent's turn (red)
        
        # Scene configuration (optional - use scenes instead of colors)
        # Set to None to use colors, or set to scene names/IDs to use scenes
        # Common scene names: "Gaming", "Movie", "Sleep", "Sunset", "Romantic", "Reading", etc.
        # You can find scene names in the Govee app
        # NOTE: Scenes don't work reliably with H6022, so using colors instead
        self.use_scenes = False  # Set to True to enable scene mode
        self.white_scene = None  # Scene name/ID for white pieces (e.g., "Gaming" or scene ID)
        self.black_scene = None  # Scene name/ID for black pieces
        self.game_over_scene = None  # Scene name/ID for game over (will use color if None)
        
        # Default restore color (used when we can't determine the previous color)
        # Yellow-ish warm color: RGB(255, 200, 100) - adjust these values as needed
        # You can customize this to match your preferred default lamp color
        self.default_restore_color = {'r': 255, 'g': 200, 'b': 100}  # Warm yellow/orange
        self.default_restore_brightness = 100  # Full brightness for restore
    
    def _get_device_id_from_api(self) -> str:
        """Get the actual device identifier from Govee API."""
        try:
            headers = {
                "Govee-API-Key": self.govee_api_key,
                "Content-Type": "application/json"
            }
            response = requests.get(
                "https://openapi.api.govee.com/router/api/v1/user/devices",
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                devices = data.get('data', [])
                # Try to find device matching our MAC (case-insensitive, with or without colons)
                mac_normalized = self.govee_device_mac.replace(':', '').upper()
                for device in devices:
                    device_id = device.get('device', '')
                    device_id_normalized = device_id.replace(':', '').upper()
                    # Check if MAC matches (with or without colons)
                    if (mac_normalized in device_id_normalized or 
                        device_id_normalized in mac_normalized or
                        self.govee_device_mac.upper() in device_id.upper()):
                        print(f"✅ Found device: {device.get('deviceName')} ({device.get('sku')})")
                        return device_id
                # If no match, use first H6022 device
                for device in devices:
                    if device.get('sku') == 'H6022':
                        print(f"✅ Using first H6022 device: {device.get('deviceName')}")
                        return device.get('device')
                # Fallback to first device
                if devices:
                    print(f"⚠️  Using first available device: {devices[0].get('deviceName')}")
                    return devices[0].get('device')
            print(f"⚠️  Could not get device list, using MAC from config: {self.govee_device_mac}")
            return self.govee_device_mac
        except Exception as e:
            print(f"⚠️  Error getting device ID from API: {e}, using MAC from config")
            return self.govee_device_mac
        
    def get_lamp_state(self) -> Optional[Dict[str, Any]]:
        """
        Try to get current lamp state (color, brightness, scene, on/off).
        Returns None if we can't get the state.
        Uses fast timeout to avoid blocking.
        """
        # Skip LAN query (H6022 doesn't support it) - go straight to API
        # This saves time since LAN queries have 2s timeouts per command
        
        # Fall back to Cloud API
        # Note: H6022 has limited API support, so this might not work
        # We'll try but won't fail if it doesn't work
        try:
            # Try to get device state from device list (includes current state)
            api_url = "https://openapi.api.govee.com/router/api/v1/user/devices"
            headers = {
                "Govee-API-Key": self.govee_api_key,
                "Content-Type": "application/json"
            }
            response = requests.get(api_url, headers=headers, timeout=3)  # Reduced from 5s to 3s for faster response
            if response.status_code == 200:
                data = response.json()
                # API returns data in different formats - try both
                devices = []
                if isinstance(data.get('data'), list):
                    devices = data.get('data', [])
                elif isinstance(data.get('data'), dict):
                    devices = data.get('data', {}).get('devices', [])
                else:
                    # Sometimes it's just a list
                    if isinstance(data, list):
                        devices = data
                
                # Find our device
                for device in devices:
                    device_id = device.get('device', '')
                    if (device_id == self.govee_device_id or 
                        self.govee_device_mac.replace(':', '').upper() in device_id.replace(':', '').upper()):
                        # Extract state information
                        state = {
                            'onOff': device.get('onOff', 1),
                            'brightness': device.get('brightness', 100),
                        }
                        
                        # Check for scene
                        if 'scene' in device and device.get('scene'):
                            state['scene'] = device.get('scene')
                            print(f"✅ Retrieved lamp state - Current scene: {state['scene']}")
                        
                        # Check for color - might be in different formats
                        color_found = False
                        if 'color' in device:
                            color_data = device.get('color')
                            if isinstance(color_data, dict):
                                if 'r' in color_data or 'red' in color_data:
                                    state['color'] = {
                                        'r': color_data.get('r') or color_data.get('red', 255),
                                        'g': color_data.get('g') or color_data.get('green', 255),
                                        'b': color_data.get('b') or color_data.get('blue', 255)
                                    }
                                    color_found = True
                            elif isinstance(color_data, list) and len(color_data) >= 3:
                                state['color'] = {'r': color_data[0], 'g': color_data[1], 'b': color_data[2]}
                                color_found = True
                        
                        # Also check for properties that might contain color info
                        if 'properties' in device:
                            props = device.get('properties', [])
                            for prop in props:
                                prop_name = prop.get('name', '').lower()
                                if 'color' in prop_name:
                                    color_val = prop.get('value', {})
                                    if isinstance(color_val, dict):
                                        state['color'] = {
                                            'r': color_val.get('r') or color_val.get('red', 255),
                                            'g': color_val.get('g') or color_val.get('green', 255),
                                            'b': color_val.get('b') or color_val.get('blue', 255)
                                        }
                                        color_found = True
                                    elif isinstance(color_val, list) and len(color_val) >= 3:
                                        state['color'] = {'r': color_val[0], 'g': color_val[1], 'b': color_val[2]}
                                        color_found = True
                        
                        if color_found:
                            print(f"✅ Retrieved lamp state - Color: RGB({state['color']['r']}, {state['color']['g']}, {state['color']['b']}), Brightness: {state['brightness']}%")
                        elif state.get('scene'):
                            print(f"✅ Retrieved lamp state - Scene: {state['scene']}, Brightness: {state['brightness']}%")
                        else:
                            print(f"✅ Retrieved lamp state - Brightness: {state['brightness']}% (no color info available)")
                        return state
        except Exception as e:
            print(f"⚠️  Could not get lamp state: {e}")
        
        # If we can't get state, return None (we'll just leave lamp as-is)
        print("⚠️  Could not detect current lamp state/scene - lamp will remain as-is when game ends")
        return None
    
    def restore_lamp_state(self, state: Optional[Dict[str, Any]]) -> bool:
        """
        Restore lamp to a previous state.
        If state is None, do nothing (leave lamp as-is).
        """
        if state is None:
            print("⚠️  No previous state to restore - leaving lamp as-is")
            return False
        
        try:
            # Try to restore based on what we have
            # State might have: onOff, color (r, g, b), brightness, scene, etc.
            
            # First, restore on/off state
            if 'onOff' in state:
                is_on = state.get('onOff') == 1 or state.get('onOff') is True
                if not is_on:
                    # Turn off
                    if self.lan_controller:
                        target_ip = self.lan_controller.device_ip
                        if target_ip:
                            import socket
                            import json
                            off_cmd = {"msg": {"cmd": "turn", "data": {"value": 0}}}
                            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            sock.settimeout(0.3)
                            sock.sendto(json.dumps(off_cmd).encode('utf-8'), (target_ip, 4001))
                            sock.close()
                            print("✅ Restored lamp state (turned off)")
                            return True
            
            # If it was on, restore color/scene
            if 'scene' in state and state.get('scene'):
                scene_name = state.get('scene')
                if self.set_lamp_scene(scene_name):
                    print(f"✅ Restored lamp to scene: {scene_name}")
                    return True
            
            # Restore color if available
            if 'color' in state:
                color = state.get('color')
                if isinstance(color, dict):
                    r = color.get('r', 255)
                    g = color.get('g', 255)
                    b = color.get('b', 255)
                    brightness = state.get('brightness', 100)
                    print(f"Restoring lamp to RGB({r}, {g}, {b}) at {brightness}% brightness...")
                    if self.set_lamp_color({'r': r, 'g': g, 'b': b}, brightness):
                        print(f"✅ Restored lamp color: RGB({r}, {g}, {b}) at {brightness}%")
                        return True
                    else:
                        print(f"⚠️  Failed to restore color via set_lamp_color")
            
            # If we have state but no color/scene, use default restore color with saved brightness
            if 'brightness' in state:
                brightness = state.get('brightness', self.default_restore_brightness)
                # Use default restore color (warm yellow) with the saved brightness
                default_color = self.default_restore_color
                print(f"⚠️  No color info available - using default restore color RGB({default_color['r']}, {default_color['g']}, {default_color['b']}) at {brightness}%")
                if self.set_lamp_color(default_color, brightness):
                    print(f"✅ Restored lamp to default color: RGB({default_color['r']}, {default_color['g']}, {default_color['b']}) at {brightness}%")
                    return True
                else:
                    print(f"⚠️  Failed to restore default color via set_lamp_color")
            
            # If we only have onOff state, at least ensure it's on
            if 'onOff' in state and state.get('onOff') == 1:
                # Device was on, but we don't know color/brightness
                # Just turn it on with a default setting
                print("⚠️  Only have on/off state - turning on with default white at 50%")
                if self.set_lamp_color({'r': 255, 'g': 255, 'b': 255}, 50):
                    print("✅ Turned lamp on with default settings")
                    return True
            
            print("⚠️  Could not restore lamp state (unknown format) - leaving as-is")
            return False
        except Exception as e:
            print(f"⚠️  Error restoring lamp state: {e}")
            return False
    
    def set_lamp_scene(self, scene_name: str) -> bool:
        """
        Set the Govee lamp to a scene.
        Uses Cloud API (scenes not supported via LAN for H6022).
        
        Args:
            scene_name: Name or ID of the scene (e.g., "Gaming", "Movie", "Sleep")
        """
        try:
            api_url = "https://openapi.api.govee.com/v1/devices/control"
            
            headers = {
                "Govee-API-Key": self.govee_api_key,
                "Content-Type": "application/json"
            }
            
            device = self.govee_device_id
            model = "H6022"
            
            # Try scene command
            payload = {
                "device": device,
                "model": model,
                "cmd": {
                    "name": "scene",
                    "value": scene_name
                }
            }
            
            response = requests.put(api_url, headers=headers, json=payload, timeout=3)
            result = response.json() if response.status_code == 200 else {}
            
            if response.status_code == 200 and result.get('code') == 200:
                print(f"✅ Lamp scene set to: {scene_name}")
                return True
            else:
                error_msg = result.get('message', f'HTTP {response.status_code}')
                print(f"⚠️  Could not set scene '{scene_name}': {error_msg}")
                print(f"   (H6022 may not support scenes, or scene name may be incorrect)")
                return False
                
        except Exception as e:
            print(f"⚠️  Error setting scene: {e}")
            return False
    
    def set_lamp_color(self, color: Dict[str, int], brightness: int = 100):
        """
        Set the Govee lamp color.
        Tries LAN control first, then cloud API, then library.
        
        Args:
            color: Dictionary with 'r', 'g', 'b' values (0-255)
            brightness: Brightness level (0-100)
        """
        # Try LAN control first (now using correct format!)
        if self.lan_controller:
            try:
                if self.lan_controller.set_color(color['r'], color['g'], color['b'], brightness):
                    print(f"✅ Lamp color set via LAN to RGB({color['r']}, {color['g']}, {color['b']})")
                    return True
            except Exception as e:
                print(f"⚠️  LAN control failed: {e}, trying cloud API...")
        
        # Fall back to cloud API
        try:
            # Try using the official Govee REST API directly
            # Try the v1 endpoint first (standard API)
            api_url = "https://openapi.api.govee.com/v1/devices/control"
            
            headers = {
                "Govee-API-Key": self.govee_api_key,
                "Content-Type": "application/json"
            }
            
            # Use the device ID from API (might be different format than MAC)
            device = self.govee_device_id
            model = "H6022"
            
            # Convert RGB to the format Govee expects
            payload = {
                "device": device,
                "model": model,
                "cmd": {
                    "name": "color",
                    "value": {
                        "r": color['r'],
                        "g": color['g'],
                        "b": color['b']
                    }
                }
            }
            
            response = requests.put(api_url, headers=headers, json=payload, timeout=5)
            result = response.json() if response.status_code == 200 else {}
            
            # Check if it worked
            if response.status_code == 200 and result.get('code') == 200:
                # Also set brightness
                brightness_payload = {
                    "device": device,
                    "model": model,
                    "cmd": {
                        "name": "brightness",
                        "value": brightness
                    }
                }
                requests.put(api_url, headers=headers, json=brightness_payload, timeout=5)
                print(f"✅ Lamp color set to RGB({color['r']}, {color['g']}, {color['b']})")
                return True
            else:
                # H6022 might not support cloud API - print warning but don't fail completely
                error_msg = result.get('message', f'HTTP {response.status_code}')
                print(f"⚠️  Govee cloud API not available for H6022: {error_msg}")
                print(f"   (H6022 may require LAN control or may not support API)")
                # Still try library as fallback
                return self._set_lamp_color_library(color, brightness)
                
        except Exception as e:
            print(f"⚠️  Direct API call failed: {e}, trying library method...")
            # Fall back to library method
            return self._set_lamp_color_library(color, brightness)
    
    def _set_lamp_color_library(self, color: Dict[str, int], brightness: int = 100):
        """Fallback method using the library."""
        try:
            # Different Govee libraries have different APIs
            if self.govee_lib == 'laggat':
                # govee-api-laggat uses async methods: set_color and set_brightness
                async def _set_color_async():
                    # Ensure lamp is on
                    await self.govee_client.turn_on(self.govee_device_mac)
                    # Set color (RGB tuple)
                    result = await self.govee_client.set_color(
                        self.govee_device_mac,
                        (color['r'], color['g'], color['b'])
                    )
                    # Set brightness
                    await self.govee_client.set_brightness(self.govee_device_mac, brightness)
                    return result
                
                # Run async function
                result = asyncio.run(_set_color_async())
            elif self.govee_lib == 'async':
                # aiogovee might be async
                async def _set_color_async():
                    result = await self.govee_client.set_device_state(
                        self.govee_device_mac,
                        {'color': {'r': color['r'], 'g': color['g'], 'b': color['b']}, 'brightness': brightness}
                    )
                    return result
                result = asyncio.run(_set_color_async())
            else:
                # Standard govee-api (synchronous)
                result = self.govee_client.set_color(
                    device=self.govee_device_mac,
                    rgb=(color['r'], color['g'], color['b']),
                    brightness=brightness
                )
            # Check if result indicates an error
            if isinstance(result, tuple) and len(result) == 2:
                success, message = result
                if not success:
                    print(f"⚠️  Govee library returned error: {message}")
                    return None
                else:
                    print(f"✅ Lamp color set to RGB({color['r']}, {color['g']}, {color['b']})")
            else:
                print(f"✅ Lamp color set to RGB({color['r']}, {color['g']}, {color['b']})")
            return result
        except Exception as e:
            print(f"❌ Error setting lamp color with library: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_current_game(self) -> Optional[Dict[str, Any]]:
        """Get the current ongoing game."""
        try:
            # Get current games - berserk returns an iterator
            games = list(self.lichess_client.games.get_ongoing())
            if games:
                # Return the first ongoing game
                game = games[0]
                # Extract game ID - it might be in different formats
                if isinstance(game, dict):
                    game_id = game.get('gameId') or game.get('id') or game.get('fullId')
                    if game_id:
                        return {'gameId': game_id, 'full': game}
                return {'gameId': str(game), 'full': game}
            return None
        except Exception as e:
            print(f"Error getting current game: {e}")
            return None
    
    def determine_turn(self, game_data: Dict[str, Any]) -> Optional[bool]:
        """
        Determine if it's the user's turn.
        
        Args:
            game_data: Game data from Lichess API (can be gameFull or gameState)
            
        Returns:
            True if it's the user's turn, False if opponent's turn, None if unknown
        """
        try:
            # Get the current player's username from the token
            user_info = self.lichess_client.account.get()
            my_username = user_info.get('username', '').lower()
            
            # Extract game state - might be nested in 'state' key for gameFull
            if 'state' in game_data:
                game_state = game_data['state']
            else:
                game_state = game_data
            
            # Get player info - might be in 'white'/'black' or 'players'
            white_player = None
            black_player = None
            
            if 'white' in game_data:
                white_player = game_data['white'].get('name', '').lower() if isinstance(game_data['white'], dict) else str(game_data['white']).lower()
            elif 'players' in game_data and 'white' in game_data['players']:
                white_player = game_data['players']['white'].get('user', {}).get('name', '').lower()
            
            if 'black' in game_data:
                black_player = game_data['black'].get('name', '').lower() if isinstance(game_data['black'], dict) else str(game_data['black']).lower()
            elif 'players' in game_data and 'black' in game_data['players']:
                black_player = game_data['players']['black'].get('user', {}).get('name', '').lower()
            
            # Determine whose turn it is from moves
            moves = game_state.get('moves', '')
            move_count = len(moves.split()) if moves else 0
            
            # Even number of moves = white's turn, odd = black's turn
            is_white_turn = (move_count % 2 == 0)
            
            # Determine which color the user is playing
            if white_player and white_player == my_username:
                self.my_color = 'white'
                return is_white_turn
            elif black_player and black_player == my_username:
                self.my_color = 'black'
                return not is_white_turn
            
            return None
        except Exception as e:
            print(f"Error determining turn: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def monitor_game_state(self, game_id: str):
        """
        Monitor a specific game by polling its state.
        Regular games can't use Board API streaming, so we poll instead.
        
        Args:
            game_id: The ID of the game to monitor
        """
        try:
            print(f"Monitoring game {game_id}")
            
            while True:
                try:
                    # Get current game state
                    games = list(self.lichess_client.games.get_ongoing())
                    current_game = None
                    for game in games:
                        if isinstance(game, dict):
                            gid = game.get('gameId') or game.get('id')
                            if gid == game_id:
                                current_game = game
                                break
                    
                    if not current_game:
                        print(f"Game {game_id} no longer found (game ended or not ongoing)")
                        print("Game over - Restoring lamp to previous state...")
                        if self.pre_game_state:
                            print(f"Previous state: {self.pre_game_state}")
                        restored = self.restore_lamp_state(self.pre_game_state)
                        if not restored:
                            print("⚠️  State restoration may have failed - check logs above")
                        self.current_game_id = None
                        self.pre_game_state = None
                        break
                    
                    # Get whose turn it is - the API provides this directly!
                    is_my_turn = current_game.get('isMyTurn', False)
                    
                    # Check game status
                    status = current_game.get('status', {})
                    if isinstance(status, dict):
                        status_name = status.get('name', '')
                    else:
                        status_name = str(status)
                    
                    # Check for opponent abandonment/disconnection
                    opponent_abandoned = False
                    if status_name in ['timeout', 'outoftime']:
                        # Check if it was the opponent who timed out (not us)
                        winner = current_game.get('winner')
                        if winner:
                            # If there's a winner and it's not us, opponent abandoned
                            user_info = self.lichess_client.account.get()
                            my_username = user_info.get('username', '').lower()
                            winner_username = winner.get('name', '').lower() if isinstance(winner, dict) else str(winner).lower()
                            if winner_username == my_username:
                                opponent_abandoned = True
                                print("⚠️  Opponent left/disconnected without resigning!")
                    
                    # Also check for 'abandoned' status
                    if status_name == 'abandoned':
                        opponent_abandoned = True
                        print("⚠️  Opponent abandoned the game!")
                    
                    # Check player connection status if available
                    if 'players' in current_game:
                        players = current_game.get('players', {})
                        opponent_color = 'black' if self.my_color == 'white' else 'white'
                        opponent_data = players.get(opponent_color, {})
                        if isinstance(opponent_data, dict):
                            # Check if opponent is connected/active
                            is_connected = opponent_data.get('connected', True)
                            if not is_connected and not is_my_turn:
                                # Opponent is disconnected and it's their turn
                                print("⚠️  Opponent appears to be disconnected!")
                                opponent_abandoned = True
                    
                    # If opponent abandoned, reduce brightness by half
                    if opponent_abandoned and not hasattr(self, '_abandonment_handled'):
                        print("⚠️  Opponent left - Reducing brightness by half...")
                        # Get current color (should be red if opponent's turn, green if our turn)
                        current_color = self.opponent_turn_color if not is_my_turn else self.my_turn_color
                        current_brightness = self.opponent_turn_brightness if not is_my_turn else self.my_turn_brightness
                        # Reduce brightness by half
                        reduced_brightness = max(1, current_brightness // 2)  # At least 1% brightness
                        print(f"Setting lamp to RGB({current_color['r']}, {current_color['g']}, {current_color['b']}) at {reduced_brightness}% brightness (half of {current_brightness}%)")
                        self.set_lamp_color(current_color, brightness=reduced_brightness)
                        self._abandonment_handled = True  # Mark as handled so we don't do it multiple times
                        # Wait a moment before continuing
                        time.sleep(2)
                    
                    if status_name in ['mate', 'resign', 'draw', 'stalemate', 'timeout', 'outoftime', 'cheat', 'abandoned']:
                        if opponent_abandoned:
                            print("Game ended - Opponent left/disconnected. Restoring lamp to previous state...")
                        else:
                            print("Game is over! Restoring lamp to previous state...")
                        if self.pre_game_state:
                            print(f"Previous state: {self.pre_game_state}")
                        restored = self.restore_lamp_state(self.pre_game_state)
                        if not restored:
                            print("⚠️  State restoration may have failed - check logs above")
                        # Clean up abandonment flag
                        if hasattr(self, '_abandonment_handled'):
                            delattr(self, '_abandonment_handled')
                        self.current_game_id = None
                        self.pre_game_state = None
                        break
                    
                    # Determine which color we're playing (if not already set)
                    # The game data has a 'color' field that directly tells us!
                    if self.my_color is None:
                        my_color_from_game = current_game.get('color')
                        if my_color_from_game:
                            self.my_color = my_color_from_game.lower()
                            print(f"You are playing {self.my_color.upper()}")
                        else:
                            # Fallback: try to determine from white/black fields
                            user_info = self.lichess_client.account.get()
                            my_username = user_info.get('username', '').lower()
                            
                            white_player = None
                            black_player = None
                            if 'white' in current_game:
                                white_player = current_game['white'].get('name', '').lower() if isinstance(current_game['white'], dict) else str(current_game['white']).lower()
                            if 'black' in current_game:
                                black_player = current_game['black'].get('name', '').lower() if isinstance(current_game['black'], dict) else str(current_game['black']).lower()
                            
                            if white_player == my_username:
                                self.my_color = 'white'
                                print(f"You are playing WHITE")
                            elif black_player == my_username:
                                self.my_color = 'black'
                                print(f"You are playing BLACK")
                    
                    # Update lamp based on whose turn it is (green for my turn, red for opponent)
                    if is_my_turn != self.is_my_turn:
                        self.is_my_turn = is_my_turn
                        if is_my_turn:
                            print(f"It's your turn! - Setting GREEN RGB({self.my_turn_color['r']}, {self.my_turn_color['g']}, {self.my_turn_color['b']}) at {self.my_turn_brightness}% brightness")
                            self.set_lamp_color(self.my_turn_color, brightness=self.my_turn_brightness)
                        else:
                            print(f"Opponent's turn - Setting RED RGB({self.opponent_turn_color['r']}, {self.opponent_turn_color['g']}, {self.opponent_turn_color['b']}) at {self.opponent_turn_brightness}% brightness")
                            self.set_lamp_color(self.opponent_turn_color, brightness=self.opponent_turn_brightness)
                    
                    # Poll every 0.8 seconds for faster response (with rate limit handling)
                    time.sleep(0.8)
                    
                except KeyboardInterrupt:
                    print("\nStopping game monitor...")
                    break
                except Exception as e:
                    error_str = str(e)
                    if '429' in error_str or 'Too Many Requests' in error_str:
                        print(f"⚠️  Rate limited - waiting longer before retry...")
                        time.sleep(5)  # Wait when rate limited, but not too long
                    else:
                        print(f"Error monitoring game: {e}")
                        time.sleep(1)  # Shorter error delay
        
        except Exception as e:
            print(f"Error in game monitor: {e}")
            import traceback
            traceback.print_exc()
    
    def monitor_games(self):
        """Monitor for ongoing games and stream events."""
        print("Monitoring for Lichess games...")
        print("Start a game on Lichess to begin!")
        
        while True:
            try:
                # Check for ongoing games
                game = self.get_current_game()
                
                if game and game.get('gameId') != self.current_game_id:
                    # Found new game - set color immediately for fast response
                    print(f"Found new game: {game.get('gameId')}")
                    self.current_game_id = game.get('gameId')
                    
                    # Initialize turn state from current game data
                    if isinstance(game.get('full'), dict):
                        game_data = game.get('full')
                        is_my_turn = game_data.get('isMyTurn', False)
                        self.is_my_turn = is_my_turn
                        
                        # Determine which color we're playing - use 'color' field from game data
                        my_color_from_game = game_data.get('color')
                        if my_color_from_game:
                            self.my_color = my_color_from_game.lower()
                            print(f"Game started - You are playing {self.my_color.upper()}")
                            # Set color IMMEDIATELY for fast response
                            if is_my_turn:
                                print("It's your turn! - Setting GREEN")
                                self.set_lamp_color(self.my_turn_color, brightness=self.my_turn_brightness)
                            else:
                                print("Opponent's turn - Setting RED")
                                self.set_lamp_color(self.opponent_turn_color, brightness=self.opponent_turn_brightness)
                        else:
                            # Fallback: try to determine from white/black fields
                            user_info = self.lichess_client.account.get()
                            my_username = user_info.get('username', '').lower()
                            
                            white_player = None
                            black_player = None
                            if 'white' in game_data:
                                white_player = game_data['white'].get('name', '').lower() if isinstance(game_data['white'], dict) else str(game_data['white']).lower()
                            if 'black' in game_data:
                                black_player = game_data['black'].get('name', '').lower() if isinstance(game_data['black'], dict) else str(game_data['black']).lower()
                            
                            if white_player == my_username:
                                self.my_color = 'white'
                                print(f"Game started - You are playing WHITE")
                                if is_my_turn:
                                    print("It's your turn! - Setting GREEN")
                                    self.set_lamp_color(self.my_turn_color, brightness=self.my_turn_brightness)
                                else:
                                    print("Opponent's turn - Setting RED")
                                    self.set_lamp_color(self.opponent_turn_color, brightness=self.opponent_turn_brightness)
                            elif black_player == my_username:
                                self.my_color = 'black'
                                print(f"Game started - You are playing BLACK")
                                if is_my_turn:
                                    print("It's your turn! - Setting GREEN")
                                    self.set_lamp_color(self.my_turn_color, brightness=self.my_turn_brightness)
                                else:
                                    print("Opponent's turn - Setting RED")
                                    self.set_lamp_color(self.opponent_turn_color, brightness=self.opponent_turn_brightness)
                    
                    # Save state in background (non-blocking) - use timeout to avoid delay
                    print("Saving current lamp state (non-blocking)...")
                    import threading
                    def save_state():
                        try:
                            self.pre_game_state = self.get_lamp_state()
                            if self.pre_game_state:
                                print("✅ Lamp state saved - will restore when game ends")
                            else:
                                print("⚠️  Could not get lamp state - lamp will remain as-is when game ends")
                        except:
                            pass  # Don't block on state save
                    threading.Thread(target=save_state, daemon=True).start()
                    
                    self.monitor_game_state(self.current_game_id)
                else:
                    # No game or same game, check more frequently
                    time.sleep(2)  # Reduced from 5s to 2s for faster game detection
            
            except KeyboardInterrupt:
                print("\nStopping monitor...")
                break
            except Exception as e:
                print(f"Error in monitor loop: {e}")
                time.sleep(2)  # Reduced from 5s to 2s


def load_config() -> Dict[str, str]:
    """Load configuration from config.json or environment variables."""
    config = {}
    
    # Try to load from config.json
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        # Fall back to environment variables
        config = {
            'lichess_token': os.getenv('LICHESS_TOKEN', ''),
            'govee_api_key': os.getenv('GOVEE_API_KEY', ''),
            'govee_device_mac': os.getenv('GOVEE_DEVICE_MAC', ''),
            'govee_device_ip': os.getenv('GOVEE_DEVICE_IP', '')  # Optional
        }
    
    return config


def main():
    """Main entry point."""
    print("=" * 50)
    print("Chess Lamp")
    print("=" * 50)
    
    # Load configuration
    config = load_config()
    
    # Validate configuration
    required_keys = ['lichess_token', 'govee_api_key', 'govee_device_mac']
    missing_keys = [key for key in required_keys if not config.get(key)]
    
    if missing_keys:
        print(f"Error: Missing required configuration: {', '.join(missing_keys)}")
        print("\nPlease set these in config.json or as environment variables:")
        for key in missing_keys:
            print(f"  - {key.upper()}")
        sys.exit(1)
    
    # Create integration instance
    integration = ChessLamp(
        lichess_token=config['lichess_token'],
        govee_api_key=config['govee_api_key'],
        govee_device_mac=config['govee_device_mac'],
        govee_device_ip=config.get('govee_device_ip')  # Optional, for LAN control
    )
    
    # Start monitoring
    integration.monitor_games()


if __name__ == '__main__':
    main()

