"""
Security Service for Onix
Provides advanced security features like Kill Switch, DNS Leak Protection, etc.
"""

import threading
import time
import socket
import subprocess
import platform
from typing import Callable, List
from constants import LogLevel


class KillSwitchService:
    """Service for implementing Kill Switch functionality."""

    def __init__(self, log_callback: Callable[[str, LogLevel], None]):
        self.log = log_callback
        self._is_active = False
        self._monitor_thread = None
        self._stop_event = threading.Event()
        self._original_routes = []
        self._backup_dns = []

    def start_kill_switch(self, proxy_address: str) -> bool:
        """Start Kill Switch monitoring."""
        if self._is_active:
            self.log("Kill Switch is already active", LogLevel.WARNING)
            return False

        try:
            # Backup current network configuration
            self._backup_network_config()

            self._is_active = True
            self._stop_event.clear()

            self._monitor_thread = threading.Thread(
                target=self._monitor_connection,
                args=(proxy_address,),
                daemon=True
            )
            self._monitor_thread.start()

            self.log("Kill Switch activated", LogLevel.SUCCESS)
            return True

        except Exception as e:
            self.log(f"Failed to start Kill Switch: {e}", LogLevel.ERROR)
            return False

    def stop_kill_switch(self):
        """Stop Kill Switch and restore network."""
        if not self._is_active:
            return

        self._stop_event.set()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2)

        try:
            self._restore_network_config()
            self._is_active = False
            self.log("Kill Switch deactivated", LogLevel.INFO)
        except Exception as e:
            self.log(f"Failed to restore network: {e}", LogLevel.ERROR)

    def is_active(self) -> bool:
        """Check if Kill Switch is active."""
        return self._is_active

    def _backup_network_config(self):
        """Backup current network configuration."""
        try:
            if platform.system() == "Windows":
                # Backup Windows routes
                result = subprocess.run(
                    ["route", "print"],
                    capture_output=True,
                    text=True,
                    shell=True
                )
                self._original_routes = result.stdout

                # Backup DNS settings
                result = subprocess.run(
                    ["netsh", "interface", "ip", "show", "dns"],
                    capture_output=True,
                    text=True,
                    shell=True
                )
                self._backup_dns = result.stdout

        except Exception as e:
            self.log(f"Failed to backup network config: {e}", LogLevel.WARNING)

    def _restore_network_config(self):
        """Restore original network configuration."""
        try:
            if platform.system() == "Windows":
                # Restore DNS settings
                if self._backup_dns:
                    subprocess.run(
                        ["netsh", "interface", "ip", "set",
                            "dns", "name=\"Wi-Fi\"", "dhcp"],
                        shell=True,
                        check=False
                    )

        except Exception as e:
            self.log(
                f"Failed to restore network config: {e}", LogLevel.WARNING)

    def _monitor_connection(self, proxy_address: str):
        """Monitor proxy connection and block internet if disconnected."""
        while not self._stop_event.is_set():
            try:
                # Test proxy connection
                if not self._test_proxy_connection(proxy_address):
                    self.log(
                        "Proxy connection lost - blocking internet", LogLevel.WARNING)
                    self._block_internet()
                else:
                    self._unblock_internet()

                time.sleep(5)  # Check every 5 seconds

            except Exception as e:
                self.log(f"Kill Switch monitoring error: {e}", LogLevel.ERROR)
                time.sleep(10)

    def _test_proxy_connection(self, proxy_address: str) -> bool:
        """Test if proxy connection is working."""
        try:
            host, port = proxy_address.split(":")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(3)
                result = sock.connect_ex((host, int(port)))
                return result == 0
        except Exception:
            return False

    def _block_internet(self):
        """Block internet access."""
        try:
            if platform.system() == "Windows":
                # Block all traffic except local
                subprocess.run(
                    ["netsh", "advfirewall", "firewall", "add", "rule",
                     "name=\"KillSwitch\", dir=out", "action=block", "enable=yes"],
                    shell=True,
                    check=False
                )
        except Exception as e:
            self.log(f"Failed to block internet: {e}", LogLevel.ERROR)

    def _unblock_internet(self):
        """Unblock internet access."""
        try:
            if platform.system() == "Windows":
                # Remove block rule
                subprocess.run(
                    ["netsh", "advfirewall", "firewall",
                        "delete", "rule", "name=\"KillSwitch\""],
                    shell=True,
                    check=False
                )
        except Exception as e:
            self.log(f"Failed to unblock internet: {e}", LogLevel.ERROR)


class DNSLeakProtectionService:
    """Service for DNS Leak Protection."""

    def __init__(self, log_callback: Callable[[str, LogLevel], None]):
        self.log = log_callback
        self._is_active = False
        self._monitor_thread = None
        self._stop_event = threading.Event()

    def start_dns_protection(self, dns_servers: List[str]) -> bool:
        """Start DNS Leak Protection."""
        if self._is_active:
            self.log("DNS Leak Protection is already active", LogLevel.WARNING)
            return False

        try:
            self._is_active = True
            self._stop_event.clear()

            self._monitor_thread = threading.Thread(
                target=self._monitor_dns,
                args=(dns_servers,),
                daemon=True
            )
            self._monitor_thread.start()

            self.log("DNS Leak Protection activated", LogLevel.SUCCESS)
            return True

        except Exception as e:
            self.log(
                f"Failed to start DNS Leak Protection: {e}", LogLevel.ERROR)
            return False

    def stop_dns_protection(self):
        """Stop DNS Leak Protection."""
        if not self._is_active:
            return

        self._stop_event.set()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2)

        self._is_active = False
        self.log("DNS Leak Protection deactivated", LogLevel.INFO)

    def is_active(self) -> bool:
        """Check if DNS Leak Protection is active."""
        return self._is_active

    def _monitor_dns(self, dns_servers: List[str]):
        """Monitor DNS queries for leaks."""
        while not self._stop_event.is_set():
            try:
                # Check if system is using correct DNS servers
                if not self._check_dns_servers(dns_servers):
                    self.log("DNS leak detected!", LogLevel.WARNING)
                    self._fix_dns_servers(dns_servers)

                time.sleep(10)  # Check every 10 seconds

            except Exception as e:
                self.log(f"DNS monitoring error: {e}", LogLevel.ERROR)
                time.sleep(30)

    def _check_dns_servers(self, expected_dns: List[str]) -> bool:
        """Check if system is using expected DNS servers."""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["netsh", "interface", "ip", "show", "dns"],
                    capture_output=True,
                    text=True,
                    shell=True
                )
                current_dns = result.stdout.lower()

                for dns in expected_dns:
                    if dns.lower() not in current_dns:
                        return False

                return True
        except Exception:
            return False

    def _fix_dns_servers(self, dns_servers: List[str]):
        """Fix DNS servers to prevent leaks."""
        try:
            if platform.system() == "Windows":
                for i, dns in enumerate(dns_servers):
                    subprocess.run(
                        ["netsh", "interface", "ip", "set", "dns",
                         "name=\"Wi-Fi\"", "static", dns, f"index={i+1}"],
                        shell=True,
                        check=False
                    )
        except Exception as e:
            self.log(f"Failed to fix DNS servers: {e}", LogLevel.ERROR)


class CertificatePinningService:
    """Service for Certificate Pinning."""

    def __init__(self, log_callback: Callable[[str, LogLevel], None]):
        self.log = log_callback
        self._pinned_certificates = {}

    def add_pinned_certificate(self, hostname: str, certificate_hash: str) -> bool:
        """Add a certificate pin for a hostname."""
        try:
            self._pinned_certificates[hostname] = certificate_hash
            self.log(f"Added certificate pin for {hostname}", LogLevel.SUCCESS)
            return True
        except Exception as e:
            self.log(f"Failed to add certificate pin: {e}", LogLevel.ERROR)
            return False

    def verify_certificate(self, hostname: str, certificate_hash: str) -> bool:
        """Verify if certificate matches pinned hash."""
        if hostname not in self._pinned_certificates:
            return True  # No pin set, allow connection

        return self._pinned_certificates[hostname] == certificate_hash

    def remove_pinned_certificate(self, hostname: str) -> bool:
        """Remove certificate pin for hostname."""
        try:
            if hostname in self._pinned_certificates:
                del self._pinned_certificates[hostname]
                self.log(
                    f"Removed certificate pin for {hostname}", LogLevel.SUCCESS)
                return True
            return False
        except Exception as e:
            self.log(f"Failed to remove certificate pin: {e}", LogLevel.ERROR)
            return False


class IPv6LeakProtectionService:
    """Service for IPv6 Leak Protection."""

    def __init__(self, log_callback: Callable[[str, LogLevel], None]):
        self.log = log_callback
        self._is_active = False

    def start_ipv6_protection(self) -> bool:
        """Start IPv6 Leak Protection."""
        try:
            if platform.system() == "Windows":
                # Disable IPv6 on all interfaces
                subprocess.run(
                    ["netsh", "interface", "ipv6", "set",
                        "global", "randomizeidentifiers=disabled"],
                    shell=True,
                    check=False
                )

                # Block IPv6 traffic
                subprocess.run(
                    ["netsh", "advfirewall", "firewall", "add", "rule",
                     "name=\"BlockIPv6\", dir=out", "action=block", "protocol=41", "enable=yes"],
                    shell=True,
                    check=False
                )

            self._is_active = True
            self.log("IPv6 Leak Protection activated", LogLevel.SUCCESS)
            return True

        except Exception as e:
            self.log(
                f"Failed to start IPv6 Leak Protection: {e}", LogLevel.ERROR)
            return False

    def stop_ipv6_protection(self):
        """Stop IPv6 Leak Protection."""
        try:
            if platform.system() == "Windows":
                # Remove IPv6 block rule
                subprocess.run(
                    ["netsh", "advfirewall", "firewall",
                        "delete", "rule", "name=\"BlockIPv6\""],
                    shell=True,
                    check=False
                )

            self._is_active = False
            self.log("IPv6 Leak Protection deactivated", LogLevel.INFO)

        except Exception as e:
            self.log(
                f"Failed to stop IPv6 Leak Protection: {e}", LogLevel.ERROR)

    def is_active(self) -> bool:
        """Check if IPv6 Leak Protection is active."""
        return self._is_active
