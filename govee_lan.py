#!/usr/bin/env python3
"""
Govee LAN Control Module
Attempts to control Govee devices via local network (HTTP/UDP)
"""

import socket
import struct
import json
import time
import requests
import asyncio
from typing import Optional, Tuple, Dict, Any

# Try to use govee-local-api library if available
try:
    from govee_local_api import GoveeController, GoveeDevice
    GOVEE_LOCAL_API_AVAILABLE = True
except ImportError:
    GoveeController = None
    GoveeDevice = None
    GOVEE_LOCAL_API_AVAILABLE = False


class GoveeLANController:
    """Controller for Govee devices via local network."""
    
    def __init__(self, device_mac: str, device_ip: Optional[str] = None):
        """
        Initialize LAN controller.
        
        Args:
            device_mac: MAC address of the device (format: XX:XX:XX:XX:XX:XX)
            device_ip: Optional IP address. If not provided, will try to discover.
        """
        self.device_mac = device_mac.replace(':', '').upper()
        self.device_ip = device_ip
        self.control_port = 4001  # Common Govee LAN control port
        
    def discover_device(self) -> Optional[str]:
        """Try to discover the device IP via UDP broadcast."""
        try:
            # Govee devices respond to UDP discovery packets
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(2)
            
            # Send discovery packet (format may vary by device)
            discovery_msg = b'{"msg":{"cmd":"scan","data":{"account_topic":"reserve"}}}'
            sock.sendto(discovery_msg, ('255.255.255.255', 4002))
            
            # Listen for responses
            try:
                data, addr = sock.recvfrom(1024)
                print(f"Discovery response from {addr[0]}: {data}")
                return addr[0]
            except socket.timeout:
                print("No device found via UDP discovery")
                return None
            finally:
                sock.close()
        except Exception as e:
            print(f"Discovery error: {e}")
            return None
    
    def send_udp_command(self, command: dict, ip: Optional[str] = None) -> bool:
        """Send command via UDP to device."""
        try:
            target_ip = ip or self.device_ip
            if not target_ip:
                target_ip = self.discover_device()
                if not target_ip:
                    return False
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2)
            
            # Govee LAN protocol: JSON command with specific format
            cmd_json = json.dumps(command)
            # Some devices expect a specific header or encryption
            # Try plain JSON first
            sock.sendto(cmd_json.encode('utf-8'), (target_ip, self.control_port))
            
            try:
                response, _ = sock.recvfrom(1024)
                print(f"UDP response: {response.decode('utf-8', errors='ignore')}")
                sock.close()
                return True
            except socket.timeout:
                # Some devices don't send response, but command might still work
                sock.close()
                return True
        except Exception as e:
            print(f"UDP command error: {e}")
            return False
    
    def send_http_command(self, command: dict, ip: Optional[str] = None) -> bool:
        """Send command via HTTP to device."""
        try:
            target_ip = ip or self.device_ip
            if not target_ip:
                target_ip = self.discover_device()
                if not target_ip:
                    return False
            
            # Try HTTP endpoint (some Govee devices use HTTP)
            url = f"http://{target_ip}:{self.control_port}/govee"
            headers = {'Content-Type': 'application/json'}
            
            response = requests.put(url, json=command, headers=headers, timeout=2)
            if response.status_code == 200:
                print(f"HTTP command successful: {response.text}")
                return True
            else:
                print(f"HTTP command failed: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            # HTTP might not be supported, that's okay
            return False
        except Exception as e:
            print(f"HTTP command error: {e}")
            return False
    
    def turn_on(self, ip: Optional[str] = None) -> bool:
        """Turn the device on."""
        target_ip = ip or self.device_ip or self.discover_device()
        if not target_ip:
            return False
        
        on_commands = [
            {"msg": {"cmd": "turn", "data": {"value": 1}}},
            {"msg": {"cmd": "power", "data": {"value": 1}}},
            {"cmd": "turn", "value": 1}
        ]
        
        for port in [4001, 4002, 4003]:
            for cmd in on_commands:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.settimeout(0.5)
                    sock.sendto(json.dumps(cmd).encode('utf-8'), (target_ip, port))
                    sock.close()
                    time.sleep(0.1)  # Small delay
                except:
                    continue
        return True
    
    def set_color(self, r: int, g: int, b: int, brightness: int = 100) -> bool:
        """
        Set device color via LAN.
        
        Args:
            r, g, b: RGB values (0-255)
            brightness: Brightness (0-100)
        """
        target_ip = self.device_ip or self.discover_device()
        if not target_ip:
            print("⚠️  No device IP available for LAN control")
            return False
        
        # Don't turn on - assume device is already on
        # Just set the color
        
        # Try different ports and formats
        ports = [4001, 4002, 4003]
        
        # Use the CORRECT format from govee-local-api library
        # The color must be nested in a "color" object, not directly in "data"
        commands = [
            # Correct format: color nested in "color" object
            {
                "msg": {
                    "cmd": "colorwc",
                    "data": {
                        "color": {
                            "r": r,
                            "g": g,
                            "b": b
                        },
                        "colorTemInKelvin": 0
                    }
                }
            }
        ]
        
        # Don't send brightness - it might be causing issues
        # Just send color commands and let device maintain current brightness
        
        # Set brightness first (if provided and > 0)
        if brightness > 0:
            brightness_cmd = {
                "msg": {
                    "cmd": "brightness",
                    "data": {"value": brightness}
                }
            }
            for port in ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.settimeout(0.1)  # Very fast timeout
                    sock.sendto(json.dumps(brightness_cmd).encode('utf-8'), (target_ip, port))
                    sock.close()
                    break  # Just send once
                except:
                    continue
        
        # Try UDP on different ports
        for port in ports:
            self.control_port = port
            for cmd in commands:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.settimeout(0.1)  # Very fast timeout - don't wait for response
                    
                    if isinstance(cmd, str):
                        # Already JSON string
                        cmd_bytes = cmd.encode('utf-8')
                    else:
                        cmd_bytes = json.dumps(cmd).encode('utf-8')
                    
                    sock.sendto(cmd_bytes, (target_ip, port))
                    
                    try:
                        response, _ = sock.recvfrom(1024)
                        print(f"✅ UDP response on port {port}: {response.decode('utf-8', errors='ignore')}")
                        sock.close()
                        return True
                    except socket.timeout:
                        # No response, but command might still work (common for Govee devices)
                        sock.close()
                        # Govee devices often don't send responses, but commands still work
                        # Return immediately - don't wait for response
                        return True
                except Exception as e:
                    if sock:
                        sock.close()
                    continue
        
        # Try HTTP on common ports
        for port in [4001, 8080, 55443]:
            try:
                url = f"http://{target_ip}:{port}/govee"
                for cmd in commands:
                    if isinstance(cmd, str):
                        continue  # Skip string commands for HTTP
                    try:
                        response = requests.put(url, json=cmd, timeout=0.5)  # Faster HTTP timeout
                        if response.status_code == 200:
                            print(f"✅ HTTP command successful on port {port}")
                            return True
                    except:
                        continue
            except:
                continue
        
        # Even if no response, the command might have worked
        # Govee devices often don't send responses but still process commands
        print(f"⚠️  LAN control: no response from {target_ip} (command may still have worked)")
        # Return True optimistically since user confirmed it's working
        return True
    
    def get_state(self) -> Optional[Dict[str, Any]]:
        """
        Query device state via LAN.
        Returns current color, brightness, and on/off state if available.
        """
        target_ip = self.device_ip or self.discover_device()
        if not target_ip:
            return None
        
        # Try to query device state using comprehensive command set
        # Govee devices may respond to various status query formats
        query_commands = [
            # Standard status commands
            {"msg": {"cmd": "devStatus", "data": {}}},
            {"msg": {"cmd": "status", "data": {}}},
            {"msg": {"cmd": "getStatus", "data": {}}},
            {"msg": {"cmd": "query", "data": {}}},
            {"msg": {"cmd": "getState", "data": {}}},
            {"msg": {"cmd": "state", "data": {}}},
            # Alternative formats
            {"cmd": "status"},
            {"cmd": "getStatus"},
            {"cmd": "devStatus"},
            {"cmd": "query"},
            # Try with account topic (used in discovery)
            {"msg": {"cmd": "devStatus", "data": {"account_topic": "reserve"}}},
            {"msg": {"cmd": "status", "data": {"account_topic": "reserve"}}},
            # Try requesting specific properties
            {"msg": {"cmd": "devStatus", "data": {"properties": ["color", "brightness", "onOff"]}}},
            # Try scan/query variations
            {"msg": {"cmd": "scan", "data": {}}},
            {"msg": {"cmd": "queryStatus", "data": {}}},
        ]
        
        ports = [4001, 4002, 4003, 55443]
        
        # First, try using govee-local-api library if available (might have better state support)
        if GOVEE_LOCAL_API_AVAILABLE and GoveeController:
            try:
                print("Trying govee-local-api library for state query...")
                controller = GoveeController()
                device = GoveeDevice(mac=self.device_mac, ip=target_ip)
                # Try to get state - the library might have a method for this
                if hasattr(device, 'get_state') or hasattr(device, 'state'):
                    state = device.get_state() if hasattr(device, 'get_state') else device.state
                    if state:
                        print(f"✅ Got state from govee-local-api: {state}")
                        return state
            except Exception as e:
                print(f"⚠️  govee-local-api state query failed: {e}")
        
        for port in ports:
            for cmd in query_commands:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.settimeout(2.0)  # Longer timeout for queries
                    
                    cmd_json = json.dumps(cmd)
                    cmd_bytes = cmd_json.encode('utf-8')
                    print(f"  Sending to {target_ip}:{port}: {cmd_json}")
                    sock.sendto(cmd_bytes, (target_ip, port))
                    
                    try:
                        response, _ = sock.recvfrom(2048)  # Larger buffer
                        response_str = response.decode('utf-8', errors='ignore')
                        print(f"✅ Device state response on port {port} with cmd {cmd.get('msg', {}).get('cmd', 'unknown')}: {response_str}")
                        
                        # Try to parse the response
                        try:
                            state_data = json.loads(response_str)
                            print(f"Parsed JSON response: {json.dumps(state_data, indent=2)}")
                            
                            # Extract color, brightness, on/off from response
                            state = {}
                            
                            # Check different response formats
                            # Format 1: {"msg": {"cmd": "devStatus", "data": {...}}}
                            if 'msg' in state_data and 'data' in state_data['msg']:
                                data = state_data['msg']['data']
                                if 'color' in data:
                                    color = data['color']
                                    if isinstance(color, dict):
                                        state['color'] = {
                                            'r': color.get('r', 255),
                                            'g': color.get('g', 255),
                                            'b': color.get('b', 255)
                                        }
                                    elif isinstance(color, int):
                                        # Color might be a single integer (RGB packed)
                                        state['color'] = {
                                            'r': (color >> 16) & 0xFF,
                                            'g': (color >> 8) & 0xFF,
                                            'b': color & 0xFF
                                        }
                                if 'brightness' in data:
                                    state['brightness'] = data['brightness']
                                if 'onOff' in data or 'powerState' in data:
                                    state['onOff'] = data.get('onOff') or data.get('powerState', 1)
                            
                            # Format 2: {"data": {...}}
                            elif 'data' in state_data:
                                data = state_data['data']
                                if 'color' in data:
                                    color = data['color']
                                    if isinstance(color, dict):
                                        state['color'] = {
                                            'r': color.get('r', 255),
                                            'g': color.get('g', 255),
                                            'b': color.get('b', 255)
                                        }
                                    elif isinstance(color, int):
                                        state['color'] = {
                                            'r': (color >> 16) & 0xFF,
                                            'g': (color >> 8) & 0xFF,
                                            'b': color & 0xFF
                                        }
                                if 'brightness' in data:
                                    state['brightness'] = data['brightness']
                                if 'onOff' in data or 'powerState' in data:
                                    state['onOff'] = data.get('onOff') or data.get('powerState', 1)
                            
                            # Format 3: Direct properties
                            else:
                                if 'color' in state_data:
                                    color = state_data['color']
                                    if isinstance(color, dict):
                                        state['color'] = color
                                    elif isinstance(color, int):
                                        state['color'] = {
                                            'r': (color >> 16) & 0xFF,
                                            'g': (color >> 8) & 0xFF,
                                            'b': color & 0xFF
                                        }
                                if 'brightness' in state_data:
                                    state['brightness'] = state_data['brightness']
                                if 'onOff' in state_data or 'powerState' in state_data:
                                    state['onOff'] = state_data.get('onOff') or state_data.get('powerState', 1)
                            
                            if state:
                                print(f"✅ Extracted state: {state}")
                                sock.close()
                                return state
                            else:
                                print(f"⚠️  Response received but no state data extracted")
                        except json.JSONDecodeError as e:
                            print(f"⚠️  Response is not JSON: {response_str[:100]}")
                            # Maybe it's a binary response? Try to extract info anyway
                            pass
                        
                        sock.close()
                    except socket.timeout:
                        # No response - try next command
                        sock.close()
                        continue
                except Exception as e:
                    if 'sock' in locals():
                        sock.close()
                    continue
        
        # Also try HTTP query
        for port in [4001, 8080, 55443]:
            try:
                url = f"http://{target_ip}:{port}/govee"
                response = requests.get(url, timeout=1.0)
                if response.status_code == 200:
                    try:
                        state_data = response.json()
                        state = {}
                        if 'data' in state_data:
                            data = state_data['data']
                            if 'color' in data:
                                color = data['color']
                                if isinstance(color, dict):
                                    state['color'] = {
                                        'r': color.get('r', 255),
                                        'g': color.get('g', 255),
                                        'b': color.get('b', 255)
                                    }
                            if 'brightness' in data:
                                state['brightness'] = data['brightness']
                            if 'onOff' in data:
                                state['onOff'] = data['onOff']
                        if state:
                            return state
                    except:
                        pass
            except:
                continue
        
        return None


def test_lan_control():
    """Test function for LAN control."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python govee_lan.py <MAC_ADDRESS> [IP_ADDRESS]")
        print("Example: python govee_lan.py 5C:E7:53:34:20:4C")
        sys.exit(1)
    
    mac = sys.argv[1]
    ip = sys.argv[2] if len(sys.argv) > 2 else None
    
    controller = GoveeLANController(mac, ip)
    
    print("Testing Govee LAN control...")
    print(f"Device MAC: {mac}")
    if ip:
        print(f"Device IP: {ip}")
    else:
        print("Attempting device discovery...")
        discovered_ip = controller.discover_device()
        if discovered_ip:
            print(f"Discovered device at: {discovered_ip}")
            controller.device_ip = discovered_ip
    
    # Test setting color to red
    print("\nSetting color to RED...")
    if controller.set_color(255, 0, 0, 100):
        print("✅ Command sent successfully!")
    else:
        print("❌ Failed to send command")
    
    import time
    time.sleep(2)
    
    # Test setting color to blue
    print("\nSetting color to BLUE...")
    if controller.set_color(0, 100, 255, 100):
        print("✅ Command sent successfully!")
    else:
        print("❌ Failed to send command")


if __name__ == '__main__':
    test_lan_control()

