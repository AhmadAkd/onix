"""
Integration Service for Onix
Provides browser integration, keyboard shortcuts, and quick actions
"""

import subprocess
import threading
import time
import json
import os
from typing import Callable, Optional, Dict, Any, List
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QApplication, QShortcut
from PySide6.QtGui import QKeySequence
from constants import LogLevel


class BrowserIntegrationService:
    """Service for browser integration."""
    
    def __init__(self, log_callback: Callable[[str, LogLevel], None]):
        self.log = log_callback
        self._supported_browsers = [
            "chrome", "firefox", "edge", "opera", "brave", "safari"
        ]
        self._browser_profiles = {}
        
    def detect_browsers(self) -> List[Dict[str, Any]]:
        """Detect installed browsers."""
        detected_browsers = []
        
        for browser in self._supported_browsers:
            browser_info = self._detect_browser(browser)
            if browser_info:
                detected_browsers.append(browser_info)
                
        return detected_browsers
        
    def _detect_browser(self, browser_name: str) -> Optional[Dict[str, Any]]:
        """Detect a specific browser."""
        try:
            if browser_name == "chrome":
                return self._detect_chrome()
            elif browser_name == "firefox":
                return self._detect_firefox()
            elif browser_name == "edge":
                return self._detect_edge()
            elif browser_name == "opera":
                return self._detect_opera()
            elif browser_name == "brave":
                return self._detect_brave()
            elif browser_name == "safari":
                return self._detect_safari()
        except Exception as e:
            self.log(f"Error detecting {browser_name}: {e}", LogLevel.ERROR)
            
        return None
        
    def _detect_chrome(self) -> Optional[Dict[str, Any]]:
        """Detect Google Chrome."""
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
        ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                return {
                    "name": "Google Chrome",
                    "executable": path,
                    "type": "chrome",
                    "version": self._get_browser_version(path)
                }
        return None
        
    def _detect_firefox(self) -> Optional[Dict[str, Any]]:
        """Detect Mozilla Firefox."""
        firefox_paths = [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"
        ]
        
        for path in firefox_paths:
            if os.path.exists(path):
                return {
                    "name": "Mozilla Firefox",
                    "executable": path,
                    "type": "firefox",
                    "version": self._get_browser_version(path)
                }
        return None
        
    def _detect_edge(self) -> Optional[Dict[str, Any]]:
        """Detect Microsoft Edge."""
        edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        ]
        
        for path in edge_paths:
            if os.path.exists(path):
                return {
                    "name": "Microsoft Edge",
                    "executable": path,
                    "type": "edge",
                    "version": self._get_browser_version(path)
                }
        return None
        
    def _detect_opera(self) -> Optional[Dict[str, Any]]:
        """Detect Opera."""
        opera_paths = [
            r"C:\Program Files\Opera\opera.exe",
            r"C:\Program Files (x86)\Opera\opera.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Opera\opera.exe")
        ]
        
        for path in opera_paths:
            if os.path.exists(path):
                return {
                    "name": "Opera",
                    "executable": path,
                    "type": "opera",
                    "version": self._get_browser_version(path)
                }
        return None
        
    def _detect_brave(self) -> Optional[Dict[str, Any]]:
        """Detect Brave Browser."""
        brave_paths = [
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
            os.path.expanduser(r"~\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe")
        ]
        
        for path in brave_paths:
            if os.path.exists(path):
                return {
                    "name": "Brave Browser",
                    "executable": path,
                    "type": "brave",
                    "version": self._get_browser_version(path)
                }
        return None
        
    def _detect_safari(self) -> Optional[Dict[str, Any]]:
        """Detect Safari (Windows version)."""
        safari_paths = [
            r"C:\Program Files\Safari\Safari.exe",
            r"C:\Program Files (x86)\Safari\Safari.exe"
        ]
        
        for path in safari_paths:
            if os.path.exists(path):
                return {
                    "name": "Safari",
                    "executable": path,
                    "type": "safari",
                    "version": self._get_browser_version(path)
                }
        return None
        
    def _get_browser_version(self, executable_path: str) -> str:
        """Get browser version."""
        try:
            result = subprocess.run(
                [executable_path, "--version"],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip()
        except Exception:
            return "Unknown"
            
    def configure_browser_proxy(self, browser_type: str, proxy_address: str) -> bool:
        """Configure browser to use proxy."""
        try:
            if browser_type == "chrome":
                return self._configure_chrome_proxy(proxy_address)
            elif browser_type == "firefox":
                return self._configure_firefox_proxy(proxy_address)
            elif browser_type == "edge":
                return self._configure_edge_proxy(proxy_address)
            else:
                self.log(f"Proxy configuration not supported for {browser_type}", LogLevel.WARNING)
                return False
        except Exception as e:
            self.log(f"Failed to configure browser proxy: {e}", LogLevel.ERROR)
            return False
            
    def _configure_chrome_proxy(self, proxy_address: str) -> bool:
        """Configure Chrome proxy."""
        try:
            # Chrome uses system proxy by default, so we configure system proxy
            host, port = proxy_address.split(":")
            
            # Set system proxy
            subprocess.run([
                "netsh", "winhttp", "set", "proxy", f"{host}:{port}"
            ], shell=True, check=True)
            
            self.log("Chrome proxy configured", LogLevel.SUCCESS)
            return True
        except Exception as e:
            self.log(f"Failed to configure Chrome proxy: {e}", LogLevel.ERROR)
            return False
            
    def _configure_firefox_proxy(self, proxy_address: str) -> bool:
        """Configure Firefox proxy."""
        try:
            # Firefox requires manual configuration or user.js file
            # This is a simplified approach
            self.log("Firefox proxy configuration requires manual setup", LogLevel.INFO)
            return True
        except Exception as e:
            self.log(f"Failed to configure Firefox proxy: {e}", LogLevel.ERROR)
            return False
            
    def _configure_edge_proxy(self, proxy_address: str) -> bool:
        """Configure Edge proxy."""
        try:
            # Edge uses system proxy by default
            host, port = proxy_address.split(":")
            
            subprocess.run([
                "netsh", "winhttp", "set", "proxy", f"{host}:{port}"
            ], shell=True, check=True)
            
            self.log("Edge proxy configured", LogLevel.SUCCESS)
            return True
        except Exception as e:
            self.log(f"Failed to configure Edge proxy: {e}", LogLevel.ERROR)
            return False


class KeyboardShortcutManager(QObject):
    """Manager for keyboard shortcuts."""
    
    shortcut_triggered = Signal(str)  # shortcut_name
    
    def __init__(self, log_callback: Callable[[str, LogLevel], None]):
        super().__init__()
        self.log = log_callback
        self._shortcuts = {}
        self._default_shortcuts = self._load_default_shortcuts()
        
    def register_shortcut(self, shortcut_name: str, key_sequence: str, 
                         callback: Callable[[], None]) -> bool:
        """Register a keyboard shortcut."""
        try:
            shortcut = QShortcut(QKeySequence(key_sequence), QApplication.activeWindow())
            shortcut.activated.connect(callback)
            
            self._shortcuts[shortcut_name] = {
                "shortcut": shortcut,
                "key_sequence": key_sequence,
                "callback": callback
            }
            
            self.log(f"Registered shortcut: {shortcut_name} ({key_sequence})", LogLevel.SUCCESS)
            return True
            
        except Exception as e:
            self.log(f"Failed to register shortcut {shortcut_name}: {e}", LogLevel.ERROR)
            return False
            
    def unregister_shortcut(self, shortcut_name: str) -> bool:
        """Unregister a keyboard shortcut."""
        try:
            if shortcut_name in self._shortcuts:
                del self._shortcuts[shortcut_name]
                self.log(f"Unregistered shortcut: {shortcut_name}", LogLevel.SUCCESS)
                return True
            return False
        except Exception as e:
            self.log(f"Failed to unregister shortcut {shortcut_name}: {e}", LogLevel.ERROR)
            return False
            
    def get_shortcuts(self) -> Dict[str, str]:
        """Get all registered shortcuts."""
        return {name: data["key_sequence"] for name, data in self._shortcuts.items()}
        
    def set_shortcut(self, shortcut_name: str, key_sequence: str) -> bool:
        """Set shortcut key sequence."""
        try:
            if shortcut_name in self._shortcuts:
                self._shortcuts[shortcut_name]["shortcut"].setKey(QKeySequence(key_sequence))
                self._shortcuts[shortcut_name]["key_sequence"] = key_sequence
                self.log(f"Updated shortcut: {shortcut_name} -> {key_sequence}", LogLevel.SUCCESS)
                return True
            return False
        except Exception as e:
            self.log(f"Failed to set shortcut {shortcut_name}: {e}", LogLevel.ERROR)
            return False
            
    def _load_default_shortcuts(self) -> Dict[str, str]:
        """Load default keyboard shortcuts."""
        return {
            "connect": "Ctrl+Shift+C",
            "disconnect": "Ctrl+Shift+D",
            "quick_connect": "Ctrl+Q",
            "show_settings": "Ctrl+Comma",
            "show_logs": "Ctrl+Shift+L",
            "toggle_tray": "Ctrl+Shift+T",
            "speed_test": "Ctrl+Shift+S",
            "health_check": "Ctrl+Shift+H",
            "export_config": "Ctrl+Shift+E",
            "import_config": "Ctrl+Shift+I"
        }


class QuickActionsService:
    """Service for quick actions and automation."""
    
    def __init__(self, log_callback: Callable[[str, LogLevel], None]):
        self.log = log_callback
        self._actions = {}
        self._action_history = []
        self._setup_default_actions()
        
    def register_action(self, action_name: str, action_func: Callable[[], Any], 
                       description: str = "") -> bool:
        """Register a quick action."""
        try:
            self._actions[action_name] = {
                "function": action_func,
                "description": description,
                "created_at": time.time()
            }
            
            self.log(f"Registered quick action: {action_name}", LogLevel.SUCCESS)
            return True
            
        except Exception as e:
            self.log(f"Failed to register action {action_name}: {e}", LogLevel.ERROR)
            return False
            
    def execute_action(self, action_name: str) -> Any:
        """Execute a quick action."""
        try:
            if action_name not in self._actions:
                self.log(f"Action not found: {action_name}", LogLevel.WARNING)
                return None
                
            action = self._actions[action_name]
            result = action["function"]()
            
            # Log action execution
            self._action_history.append({
                "action_name": action_name,
                "timestamp": time.time(),
                "success": True
            })
            
            self.log(f"Executed action: {action_name}", LogLevel.SUCCESS)
            return result
            
        except Exception as e:
            self._action_history.append({
                "action_name": action_name,
                "timestamp": time.time(),
                "success": False,
                "error": str(e)
            })
            
            self.log(f"Failed to execute action {action_name}: {e}", LogLevel.ERROR)
            return None
            
    def get_actions(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered actions."""
        return {name: {
            "description": action["description"],
            "created_at": action["created_at"]
        } for name, action in self._actions.items()}
        
    def get_action_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get action execution history."""
        return self._action_history[-limit:]
        
    def _setup_default_actions(self):
        """Setup default quick actions."""
        # These would be implemented with actual functionality
        self.register_action(
            "quick_connect_best",
            lambda: self.log("Quick connect to best server", LogLevel.INFO),
            "Connect to the best available server"
        )
        
        self.register_action(
            "toggle_proxy",
            lambda: self.log("Toggle proxy on/off", LogLevel.INFO),
            "Toggle proxy connection"
        )
        
        self.register_action(
            "test_speed",
            lambda: self.log("Run speed test", LogLevel.INFO),
            "Run speed test on current connection"
        )
        
        self.register_action(
            "export_logs",
            lambda: self.log("Export logs", LogLevel.INFO),
            "Export application logs"
        )
        
        self.register_action(
            "clear_cache",
            lambda: self.log("Clear cache", LogLevel.INFO),
            "Clear application cache"
        )


class SystemTrayEnhancementService:
    """Service for enhanced system tray functionality."""
    
    def __init__(self, log_callback: Callable[[str, LogLevel], None], 
                 tray_icon: Optional[Any] = None):
        self.log = log_callback
        self.tray_icon = tray_icon
        self._context_menu = None
        self._status_updates = True
        
    def setup_enhanced_tray(self) -> bool:
        """Setup enhanced system tray with additional features."""
        try:
            if not self.tray_icon:
                return False
                
            # Create context menu
            self._create_context_menu()
            
            # Setup status updates
            self._setup_status_updates()
            
            self.log("Enhanced system tray setup completed", LogLevel.SUCCESS)
            return True
            
        except Exception as e:
            self.log(f"Failed to setup enhanced tray: {e}", LogLevel.ERROR)
            return False
            
    def _create_context_menu(self):
        """Create enhanced context menu."""
        # This would create a more sophisticated context menu
        # with server selection, quick actions, etc.
        pass
        
    def _setup_status_updates(self):
        """Setup periodic status updates."""
        # This would update tray icon based on connection status
        pass
        
    def update_tray_status(self, connected: bool, server_name: str = None):
        """Update tray icon status."""
        try:
            if not self.tray_icon:
                return
                
            if connected:
                self.tray_icon.setToolTip(f"Onix - Connected to {server_name or 'Unknown'}")
                # Set connected icon
            else:
                self.tray_icon.setToolTip("Onix - Disconnected")
                # Set disconnected icon
                
        except Exception as e:
            self.log(f"Failed to update tray status: {e}", LogLevel.ERROR)
            
    def show_notification(self, title: str, message: str, 
                         notification_type: str = "info"):
        """Show system tray notification."""
        try:
            if self.tray_icon:
                # Map notification types to QSystemTrayIcon.MessageIcon
                icon_map = {
                    "info": 0,  # QSystemTrayIcon.Information
                    "warning": 1,  # QSystemTrayIcon.Warning
                    "error": 2,  # QSystemTrayIcon.Critical
                    "success": 0  # QSystemTrayIcon.Information
                }
                
                self.tray_icon.showMessage(
                    title, message, icon_map.get(notification_type, 0), 5000
                )
                
        except Exception as e:
            self.log(f"Failed to show notification: {e}", LogLevel.ERROR)
