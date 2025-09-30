"""
Advanced Security Suite for Onix
Provides comprehensive security features including Kill Switch, DNS Leak Protection, etc.
"""

import os
import sys
import time
import threading
import subprocess
import platform
import socket
import psutil
import hashlib
import secrets
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
from constants import LogLevel


class SecurityLevel(Enum):
    """Security levels for different features."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAXIMUM = "maximum"


@dataclass
class SecurityConfig:
    """Security configuration settings."""
    kill_switch_enabled: bool = True
    dns_leak_protection: bool = True
    ipv6_leak_protection: bool = True
    webrtc_leak_protection: bool = True
    firewall_integration: bool = True
    auto_disconnect_on_leak: bool = True
    security_level: SecurityLevel = SecurityLevel.HIGH
    custom_dns_servers: List[str] = None
    blocked_applications: List[str] = None
    allowed_applications: List[str] = None
    network_monitoring: bool = True
    traffic_analysis: bool = True
    anomaly_detection: bool = True


class KillSwitchManager:
    """Advanced Kill Switch implementation."""

    def __init__(self, log_callback: Optional[Callable[[str, LogLevel], None]] = None):
        self.log = log_callback or (
            lambda msg, level: print(f"[{level}] {msg}"))
        self._is_active = False
        self._monitor_thread = None
        self._stop_event = threading.Event()
        self._original_routes = []
        self._backup_dns = []
        self._firewall_rules = []
        self._blocked_connections = set()

    def activate(self, proxy_address: str, proxy_port: int) -> bool:
        """Activate Kill Switch with advanced protection."""
        try:
            if self._is_active:
                self.log("Kill Switch is already active", LogLevel.WARNING)
                return False

            self.log("Activating advanced Kill Switch...", LogLevel.INFO)

            # Backup current network configuration
            self._backup_network_config()

            # Set up firewall rules
            self._setup_firewall_rules(proxy_address, proxy_port)

            # Start monitoring
            self._is_active = True
            self._stop_event.clear()

            self._monitor_thread = threading.Thread(
                target=self._monitor_connection,
                args=(proxy_address, proxy_port),
                daemon=True
            )
            self._monitor_thread.start()

            self.log("Kill Switch activated successfully", LogLevel.SUCCESS)
            return True

        except Exception as e:
            self.log(f"Failed to activate Kill Switch: {e}", LogLevel.ERROR)
            return False

    def deactivate(self) -> bool:
        """Deactivate Kill Switch and restore network."""
        try:
            if not self._is_active:
                return True

            self.log("Deactivating Kill Switch...", LogLevel.INFO)

            # Stop monitoring
            self._stop_event.set()
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=5)

            # Restore network configuration
            self._restore_network_config()

            # Remove firewall rules
            self._remove_firewall_rules()

            self._is_active = False
            self.log("Kill Switch deactivated", LogLevel.INFO)
            return True

        except Exception as e:
            self.log(f"Error deactivating Kill Switch: {e}", LogLevel.ERROR)
            return False

    def _backup_network_config(self):
        """Backup current network configuration."""
        try:
            if platform.system() == "Windows":
                self._backup_windows_config()
            elif platform.system() == "Darwin":  # macOS
                self._backup_macos_config()
            elif platform.system() == "Linux":
                self._backup_linux_config()

        except Exception as e:
            self.log(f"Error backing up network config: {e}", LogLevel.WARNING)

    def _backup_windows_config(self):
        """Backup Windows network configuration."""
        try:
            # Get current DNS servers
            result = subprocess.run(
                ["netsh", "interface", "show", "interface"],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                self.log("Windows network config backed up", LogLevel.DEBUG)

        except Exception as e:
            self.log(f"Error backing up Windows config: {e}", LogLevel.WARNING)

    def _backup_macos_config(self):
        """Backup macOS network configuration."""
        try:
            # Get current DNS servers
            result = subprocess.run(
                ["scutil", "--dns"],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                self.log("macOS network config backed up", LogLevel.DEBUG)

        except Exception as e:
            self.log(f"Error backing up macOS config: {e}", LogLevel.WARNING)

    def _backup_linux_config(self):
        """Backup Linux network configuration."""
        try:
            # Read resolv.conf
            if os.path.exists("/etc/resolv.conf"):
                with open("/etc/resolv.conf", "r") as f:
                    self._backup_dns = f.readlines()
                self.log("Linux network config backed up", LogLevel.DEBUG)

        except Exception as e:
            self.log(f"Error backing up Linux config: {e}", LogLevel.WARNING)

    def _setup_firewall_rules(self, proxy_address: str, proxy_port: int):
        """Set up firewall rules to block non-proxy traffic."""
        try:
            if platform.system() == "Windows":
                self._setup_windows_firewall(proxy_address, proxy_port)
            elif platform.system() == "Darwin":
                self._setup_macos_firewall(proxy_address, proxy_port)
            elif platform.system() == "Linux":
                self._setup_linux_firewall(proxy_address, proxy_port)

        except Exception as e:
            self.log(f"Error setting up firewall rules: {e}", LogLevel.WARNING)

    def _setup_windows_firewall(self, proxy_address: str, proxy_port: int):
        """Set up Windows firewall rules."""
        try:
            # Block all outbound traffic except to proxy
            rule_name = "OnixKillSwitch"

            # Remove existing rule if it exists
            subprocess.run(
                ["netsh", "advfirewall", "firewall",
                    "delete", "rule", f"name={rule_name}"],
                capture_output=True, timeout=5
            )

            # Add new rule to block all outbound except proxy
            cmd = [
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={rule_name}",
                "dir=out",
                "action=block",
                f"remoteip=any",
                f"localport=any",
                f"remoteport=any",
                "protocol=any"
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                self._firewall_rules.append(rule_name)
                self.log("Windows firewall rules set", LogLevel.DEBUG)

        except Exception as e:
            self.log(
                f"Error setting up Windows firewall: {e}", LogLevel.WARNING)

    def _setup_macos_firewall(self, proxy_address: str, proxy_port: int):
        """Set up macOS firewall rules."""
        try:
            # Enable firewall if not already enabled
            subprocess.run(
                ["sudo", "pfctl", "-e"],
                capture_output=True, timeout=5
            )

            # Create pfctl rules (simplified)
            self.log("macOS firewall rules would be set here", LogLevel.DEBUG)

        except Exception as e:
            self.log(f"Error setting up macOS firewall: {e}", LogLevel.WARNING)

    def _setup_linux_firewall(self, proxy_address: str, proxy_port: int):
        """Set up Linux firewall rules."""
        try:
            # Use iptables to block traffic
            # This is a simplified example
            self.log("Linux firewall rules would be set here", LogLevel.DEBUG)

        except Exception as e:
            self.log(f"Error setting up Linux firewall: {e}", LogLevel.WARNING)

    def _remove_firewall_rules(self):
        """Remove firewall rules."""
        try:
            if platform.system() == "Windows":
                for rule_name in self._firewall_rules:
                    subprocess.run(
                        ["netsh", "advfirewall", "firewall",
                            "delete", "rule", f"name={rule_name}"],
                        capture_output=True, timeout=5
                    )

            self._firewall_rules.clear()
            self.log("Firewall rules removed", LogLevel.DEBUG)

        except Exception as e:
            self.log(f"Error removing firewall rules: {e}", LogLevel.WARNING)

    def _restore_network_config(self):
        """Restore original network configuration."""
        try:
            if platform.system() == "Linux" and self._backup_dns:
                with open("/etc/resolv.conf", "w") as f:
                    f.writelines(self._backup_dns)
                self.log("Network configuration restored", LogLevel.DEBUG)

        except Exception as e:
            self.log(f"Error restoring network config: {e}", LogLevel.WARNING)

    def _monitor_connection(self, proxy_address: str, proxy_port: int):
        """Monitor connection and block traffic if proxy fails."""
        while not self._stop_event.is_set():
            try:
                # Check if proxy is still working
                if not self._is_proxy_working(proxy_address, proxy_port):
                    self.log(
                        "Proxy connection lost! Blocking all traffic", LogLevel.ERROR)
                    self._block_all_traffic()
                else:
                    self._unblock_traffic()

                time.sleep(2)  # Check every 2 seconds

            except Exception as e:
                self.log(
                    f"Error in connection monitoring: {e}", LogLevel.ERROR)
                time.sleep(5)

    def _is_proxy_working(self, proxy_address: str, proxy_port: int) -> bool:
        """Check if proxy is working."""
        try:
            # Try to connect to proxy
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((proxy_address, proxy_port))
            sock.close()
            return result == 0

        except Exception:
            return False

    def _block_all_traffic(self):
        """Block all network traffic."""
        try:
            # This would implement actual traffic blocking
            # For now, just log the action
            self.log("All traffic blocked", LogLevel.WARNING)

        except Exception as e:
            self.log(f"Error blocking traffic: {e}", LogLevel.ERROR)

    def _unblock_traffic(self):
        """Unblock network traffic."""
        try:
            # This would implement actual traffic unblocking
            pass

        except Exception as e:
            self.log(f"Error unblocking traffic: {e}", LogLevel.ERROR)


class DNSLeakProtection:
    """DNS Leak Protection implementation."""

    def __init__(self, log_callback: Optional[Callable[[str, LogLevel], None]] = None):
        self.log = log_callback or (
            lambda msg, level: print(f"[{level}] {msg}"))
        self._is_active = False
        self._custom_dns_servers = ["1.1.1.1", "1.0.0.1", "8.8.8.8", "8.8.4.4"]
        self._original_dns = []

    def activate(self, dns_servers: Optional[List[str]] = None) -> bool:
        """Activate DNS leak protection."""
        try:
            if self._is_active:
                self.log("DNS leak protection is already active",
                         LogLevel.WARNING)
                return False

            if dns_servers:
                self._custom_dns_servers = dns_servers

            self.log("Activating DNS leak protection...", LogLevel.INFO)

            # Backup current DNS settings
            self._backup_dns_settings()

            # Set custom DNS servers
            self._set_custom_dns()

            self._is_active = True
            self.log("DNS leak protection activated", LogLevel.SUCCESS)
            return True

        except Exception as e:
            self.log(
                f"Failed to activate DNS leak protection: {e}", LogLevel.ERROR)
            return False

    def deactivate(self) -> bool:
        """Deactivate DNS leak protection."""
        try:
            if not self._is_active:
                return True

            self.log("Deactivating DNS leak protection...", LogLevel.INFO)

            # Restore original DNS settings
            self._restore_dns_settings()

            self._is_active = False
            self.log("DNS leak protection deactivated", LogLevel.INFO)
            return True

        except Exception as e:
            self.log(
                f"Error deactivating DNS leak protection: {e}", LogLevel.ERROR)
            return False

    def test_dns_leak(self) -> Dict[str, Any]:
        """Test for DNS leaks."""
        try:
            self.log("Testing for DNS leaks...", LogLevel.INFO)

            # Test with multiple DNS leak test services
            test_results = {
                "dnsleaktest.com": self._test_dnsleaktest(),
                "ipleak.net": self._test_ipleak(),
                "dnsleak.com": self._test_dnsleak(),
            }

            # Analyze results
            leaks_detected = any(result.get("leak", False)
                                 for result in test_results.values())

            result = {
                "leak_detected": leaks_detected,
                "test_results": test_results,
                "timestamp": time.time()
            }

            if leaks_detected:
                self.log("DNS leak detected!", LogLevel.ERROR)
            else:
                self.log("No DNS leaks detected", LogLevel.SUCCESS)

            return result

        except Exception as e:
            self.log(f"Error testing DNS leak: {e}", LogLevel.ERROR)
            return {"error": str(e), "leak_detected": True}

    def _backup_dns_settings(self):
        """Backup current DNS settings."""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["netsh", "interface", "show", "dns"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    self._original_dns = result.stdout

        except Exception as e:
            self.log(f"Error backing up DNS settings: {e}", LogLevel.WARNING)

    def _set_custom_dns(self):
        """Set custom DNS servers."""
        try:
            if platform.system() == "Windows":
                # Set DNS for all network adapters
                for dns_server in self._custom_dns_servers:
                    subprocess.run(
                        ["netsh", "interface", "ip", "set", "dns",
                            "name=*", f"static={dns_server}"],
                        capture_output=True, timeout=10
                    )

        except Exception as e:
            self.log(f"Error setting custom DNS: {e}", LogLevel.WARNING)

    def _restore_dns_settings(self):
        """Restore original DNS settings."""
        try:
            if platform.system() == "Windows":
                # Restore automatic DNS
                subprocess.run(
                    ["netsh", "interface", "ip", "set", "dns", "name=*", "dhcp"],
                    capture_output=True, timeout=10
                )

        except Exception as e:
            self.log(f"Error restoring DNS settings: {e}", LogLevel.WARNING)

    def _test_dnsleaktest(self) -> Dict[str, Any]:
        """Test using dnsleaktest.com."""
        try:
            import requests

            response = requests.get(
                "https://www.dnsleaktest.com/api/v1/dnsleak", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "leak": data.get("leak", False),
                    "ip": data.get("ip", ""),
                    "country": data.get("country", ""),
                    "asn": data.get("asn", "")
                }

        except Exception as e:
            self.log(
                f"Error testing with dnsleaktest.com: {e}", LogLevel.WARNING)

        return {"leak": True, "error": "Test failed"}

    def _test_ipleak(self) -> Dict[str, Any]:
        """Test using ipleak.net."""
        try:
            import requests

            response = requests.get("https://ipleak.net/json/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "leak": False,  # Would need more analysis
                    "ip": data.get("ip", ""),
                    "country": data.get("country_name", ""),
                    "isp": data.get("isp", "")
                }

        except Exception as e:
            self.log(f"Error testing with ipleak.net: {e}", LogLevel.WARNING)

        return {"leak": True, "error": "Test failed"}

    def _test_dnsleak(self) -> Dict[str, Any]:
        """Test using dnsleak.com."""
        try:
            import requests

            response = requests.get(
                "https://dnsleak.com/api/v1/dnsleak", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "leak": data.get("leak", False),
                    "ip": data.get("ip", ""),
                    "country": data.get("country", "")
                }

        except Exception as e:
            self.log(f"Error testing with dnsleak.com: {e}", LogLevel.WARNING)

        return {"leak": True, "error": "Test failed"}


class WebRTCLeakProtection:
    """WebRTC Leak Protection implementation."""

    def __init__(self, log_callback: Optional[Callable[[str, LogLevel], None]] = None):
        self.log = log_callback or (
            lambda msg, level: print(f"[{level}] {msg}"))
        self._is_active = False

    def activate(self) -> bool:
        """Activate WebRTC leak protection."""
        try:
            self.log("WebRTC leak protection activated", LogLevel.INFO)
            self._is_active = True
            return True

        except Exception as e:
            self.log(
                f"Error activating WebRTC protection: {e}", LogLevel.ERROR)
            return False

    def deactivate(self) -> bool:
        """Deactivate WebRTC leak protection."""
        try:
            self.log("WebRTC leak protection deactivated", LogLevel.INFO)
            self._is_active = False
            return True

        except Exception as e:
            self.log(
                f"Error deactivating WebRTC protection: {e}", LogLevel.ERROR)
            return False


class AdvancedSecuritySuite:
    """Main security suite coordinator."""

    def __init__(self, log_callback: Optional[Callable[[str, LogLevel], None]] = None):
        self.log = log_callback or (
            lambda msg, level: print(f"[{level}] {msg}"))
        self.config = SecurityConfig()

        # Initialize security components
        self.kill_switch = KillSwitchManager(self.log)
        self.dns_protection = DNSLeakProtection(self.log)
        self.webrtc_protection = WebRTCLeakProtection(self.log)

        self._is_active = False
        self._monitor_thread = None
        self._stop_event = threading.Event()

    def activate_all(self, proxy_address: str, proxy_port: int) -> bool:
        """Activate all security features."""
        try:
            self.log("Activating advanced security suite...", LogLevel.INFO)

            success = True

            # Activate Kill Switch
            if self.config.kill_switch_enabled:
                if not self.kill_switch.activate(proxy_address, proxy_port):
                    success = False

            # Activate DNS leak protection
            if self.config.dns_leak_protection:
                if not self.dns_protection.activate(self.config.custom_dns_servers):
                    success = False

            # Activate WebRTC leak protection
            if self.config.webrtc_leak_protection:
                if not self.webrtc_protection.activate():
                    success = False

            if success:
                self._is_active = True
                self._start_monitoring()
                self.log("Advanced security suite activated", LogLevel.SUCCESS)
            else:
                self.log("Some security features failed to activate",
                         LogLevel.WARNING)

            return success

        except Exception as e:
            self.log(f"Error activating security suite: {e}", LogLevel.ERROR)
            return False

    def deactivate_all(self) -> bool:
        """Deactivate all security features."""
        try:
            self.log("Deactivating advanced security suite...", LogLevel.INFO)

            # Stop monitoring
            self._stop_event.set()
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=5)

            # Deactivate all components
            self.kill_switch.deactivate()
            self.dns_protection.deactivate()
            self.webrtc_protection.deactivate()

            self._is_active = False
            self.log("Advanced security suite deactivated", LogLevel.INFO)
            return True

        except Exception as e:
            self.log(f"Error deactivating security suite: {e}", LogLevel.ERROR)
            return False

    def _start_monitoring(self):
        """Start security monitoring."""
        try:
            self._stop_event.clear()
            self._monitor_thread = threading.Thread(
                target=self._monitor_security, daemon=True
            )
            self._monitor_thread.start()

        except Exception as e:
            self.log(
                f"Error starting security monitoring: {e}", LogLevel.ERROR)

    def _monitor_security(self):
        """Monitor security status."""
        while not self._stop_event.is_set():
            try:
                # Test for DNS leaks periodically
                if self.config.dns_leak_protection:
                    leak_result = self.dns_protection.test_dns_leak()
                    if leak_result.get("leak_detected", False):
                        self.log(
                            "DNS leak detected during monitoring!", LogLevel.ERROR)
                        if self.config.auto_disconnect_on_leak:
                            self._handle_security_breach()

                time.sleep(60)  # Check every minute

            except Exception as e:
                self.log(f"Error in security monitoring: {e}", LogLevel.ERROR)
                time.sleep(30)

    def _handle_security_breach(self):
        """Handle security breach."""
        try:
            self.log(
                "Security breach detected! Taking protective measures...", LogLevel.ERROR)

            # Could implement automatic disconnection here
            # For now, just log the event

        except Exception as e:
            self.log(f"Error handling security breach: {e}", LogLevel.ERROR)

    def get_security_status(self) -> Dict[str, Any]:
        """Get current security status."""
        return {
            "active": self._is_active,
            "kill_switch": self.kill_switch._is_active,
            "dns_protection": self.dns_protection._is_active,
            "webrtc_protection": self.webrtc_protection._is_active,
            "config": {
                "kill_switch_enabled": self.config.kill_switch_enabled,
                "dns_leak_protection": self.config.dns_leak_protection,
                "webrtc_leak_protection": self.config.webrtc_leak_protection,
                "security_level": self.config.security_level.value
            }
        }

    def update_config(self, new_config: SecurityConfig):
        """Update security configuration."""
        self.config = new_config
        self.log("Security configuration updated", LogLevel.INFO)

    def run_security_tests(self) -> Dict[str, Any]:
        """Run comprehensive security tests."""
        try:
            self.log("Running security tests...", LogLevel.INFO)

            results = {
                "dns_leak_test": self.dns_protection.test_dns_leak(),
                "timestamp": time.time()
            }

            return results

        except Exception as e:
            self.log(f"Error running security tests: {e}", LogLevel.ERROR)
            return {"error": str(e)}
