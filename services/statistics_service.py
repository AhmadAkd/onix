"""
Statistics Service for Onix
Provides real-time statistics and performance monitoring
"""

import threading
import time
import psutil
import requests
import gc
from typing import Callable, Optional, Dict, Any, List
from collections import deque
from constants import LogLevel


class RealTimeStatisticsService:
    """Service for real-time statistics monitoring with memory leak prevention."""

    def __init__(self, log_callback: Callable[[str, LogLevel], None]):
        self.log = log_callback
        self._is_monitoring = False
        self._monitor_thread = None
        self._stop_event = threading.Event()
        self._statistics = {
            "upload_speed": 0.0,
            "download_speed": 0.0,
            "total_upload": 0,
            "total_download": 0,
            "connection_time": 0,
            "packets_sent": 0,
            "packets_received": 0,
            "ping": -1,
            "server_load": 0.0,
            "memory_usage": 0.0,
            "cpu_usage": 0.0,
        }
        # Memory leak prevention: Use weakref for callback and limit history
        self._speed_history = deque(maxlen=60)  # Last 60 seconds
        self._callback = None
        self._start_time = None
        self._cleanup_counter = 0
        self._max_cleanup_interval = 100  # Cleanup every 100 iterations

    def start_monitoring(
        self, callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> bool:
        """Start real-time statistics monitoring."""
        if self._is_monitoring:
            self.log("Statistics monitoring is already active", LogLevel.WARNING)
            return False

        try:
            self._is_monitoring = True
            self._stop_event.clear()
            self._callback = callback
            self._start_time = time.time()

            self._monitor_thread = threading.Thread(
                target=self._monitor_statistics, daemon=True
            )
            self._monitor_thread.start()

            self.log("Real-time statistics monitoring started", LogLevel.SUCCESS)
            return True

        except Exception as e:
            self.log(f"Failed to start statistics monitoring: {e}", LogLevel.ERROR)
            return False

    def stop_monitoring(self):
        """Stop statistics monitoring with proper cleanup."""
        if not self._is_monitoring:
            return

        self._stop_event.set()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2)

        # Cleanup to prevent memory leaks
        self._cleanup_resources()
        self._is_monitoring = False
        self.log("Statistics monitoring stopped", LogLevel.INFO)

    def is_monitoring(self) -> bool:
        """Check if monitoring is active."""
        return self._is_monitoring

    def get_statistics(self) -> Dict[str, Any]:
        """Get current statistics."""
        return self._statistics.copy()

    def get_speed_history(self) -> List[Dict[str, Any]]:
        """Get speed history for charts."""
        return list(self._speed_history)

    def _cleanup_resources(self):
        """Cleanup resources to prevent memory leaks."""
        try:
            # Clear callback reference
            self._callback = None

            # Clear speed history if it's too large
            if len(self._speed_history) > 30:
                # Keep only last 30 entries
                temp_list = list(self._speed_history)[-30:]
                self._speed_history.clear()
                self._speed_history.extend(temp_list)

            # Force garbage collection
            gc.collect()

        except Exception as e:
            self.log(f"Error during cleanup: {e}", LogLevel.WARNING)

    def _monitor_statistics(self):
        """Monitor system and network statistics with memory leak prevention."""
        last_upload = 0
        last_download = 0
        last_time = time.time()

        while not self._stop_event.is_set():
            try:
                current_time = time.time()
                time_delta = current_time - last_time

                # Get network statistics
                net_io = psutil.net_io_counters()
                current_upload = net_io.bytes_sent
                current_download = net_io.bytes_recv

                # Calculate speeds
                if time_delta > 0:
                    upload_speed = (current_upload - last_upload) / time_delta
                    download_speed = (current_download - last_download) / time_delta
                else:
                    upload_speed = 0
                    download_speed = 0

                # Update statistics
                self._statistics.update(
                    {
                        "upload_speed": upload_speed,
                        "download_speed": download_speed,
                        "total_upload": current_upload,
                        "total_download": current_download,
                        "connection_time": (
                            current_time - self._start_time if self._start_time else 0
                        ),
                        "packets_sent": net_io.packets_sent,
                        "packets_received": net_io.packets_recv,
                        "memory_usage": psutil.virtual_memory().percent,
                        "cpu_usage": psutil.cpu_percent(),
                    }
                )

                # Add to speed history (deque automatically limits size)
                self._speed_history.append(
                    {
                        "timestamp": current_time,
                        "upload_speed": upload_speed,
                        "download_speed": download_speed,
                    }
                )

                # Update ping
                self._update_ping()

                # Callback if provided (with error handling)
                if self._callback:
                    try:
                        self._callback(self._statistics)
                    except Exception as callback_error:
                        self.log(f"Callback error: {callback_error}", LogLevel.WARNING)

                # Periodic cleanup to prevent memory leaks
                self._cleanup_counter += 1
                if self._cleanup_counter >= self._max_cleanup_interval:
                    self._cleanup_resources()
                    self._cleanup_counter = 0

                # Update for next iteration
                last_upload = current_upload
                last_download = current_download
                last_time = current_time

                time.sleep(1)  # Update every second

            except Exception as e:
                self.log(f"Statistics monitoring error: {e}", LogLevel.ERROR)
                time.sleep(5)

    def _update_ping(self):
        """Update ping statistics."""
        try:
            # Test ping to a reliable server
            import subprocess

            result = subprocess.run(
                ["ping", "-n", "1", "8.8.8.8"],
                capture_output=True,
                text=True,
                timeout=3,
            )

            if result.returncode == 0:
                # Extract ping time from output
                output = result.stdout
                if "time=" in output:
                    ping_str = output.split("time=")[1].split("ms")[0]
                    self._statistics["ping"] = float(ping_str)
                else:
                    self._statistics["ping"] = -1
            else:
                self._statistics["ping"] = -1

        except Exception:
            self._statistics["ping"] = -1


class LoadBalancingService:
    """Service for load balancing between servers."""

    def __init__(self, log_callback: Callable[[str, LogLevel], None]):
        self.log = log_callback
        self._is_active = False
        self._servers = []
        self._current_server = None
        self._monitor_thread = None
        self._stop_event = threading.Event()
        self._failover_callback = None

    def start_load_balancing(
        self,
        servers: List[Dict[str, Any]],
        failover_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> bool:
        """Start load balancing between servers."""
        if self._is_active:
            self.log("Load balancing is already active", LogLevel.WARNING)
            return False

        try:
            self._servers = servers
            self._failover_callback = failover_callback
            self._is_active = True
            self._stop_event.clear()

            self._monitor_thread = threading.Thread(
                target=self._monitor_servers, daemon=True
            )
            self._monitor_thread.start()

            self.log("Load balancing started", LogLevel.SUCCESS)
            return True

        except Exception as e:
            self.log(f"Failed to start load balancing: {e}", LogLevel.ERROR)
            return False

    def stop_load_balancing(self):
        """Stop load balancing with proper cleanup."""
        if not self._is_active:
            return

        self._stop_event.set()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2)

        # Cleanup to prevent memory leaks
        self._servers.clear()
        self._failover_callback = None
        self._current_server = None
        gc.collect()

        self._is_active = False
        self.log("Load balancing stopped", LogLevel.INFO)

    def is_active(self) -> bool:
        """Check if load balancing is active."""
        return self._is_active

    def get_best_server(self) -> Optional[Dict[str, Any]]:
        """Get the best available server."""
        if not self._servers:
            return None

        # Sort by ping and server load
        sorted_servers = sorted(
            self._servers,
            key=lambda s: (s.get("tcp_ping", 999), s.get("server_load", 100)),
        )

        return sorted_servers[0] if sorted_servers else None

    def _monitor_servers(self):
        """Monitor server health and performance."""
        while not self._stop_event.is_set():
            try:
                # Test current server
                if self._current_server:
                    if not self._test_server_health(self._current_server):
                        self.log(
                            f"Current server {self._current_server.get('name')} failed health check",
                            LogLevel.WARNING,
                        )

                        # Switch to best available server
                        best_server = self.get_best_server()
                        if best_server and best_server != self._current_server:
                            self.log(
                                f"Switching to server: {best_server.get('name')}",
                                LogLevel.INFO,
                            )

                            if self._failover_callback:
                                self._failover_callback(best_server)

                            self._current_server = best_server

                time.sleep(30)  # Check every 30 seconds

            except Exception as e:
                self.log(f"Load balancing error: {e}", LogLevel.ERROR)
                time.sleep(10)

    def _test_server_health(self, server: Dict[str, Any]) -> bool:
        """Test if a server is healthy."""
        try:
            import socket

            host = server.get("server")
            port = server.get("port")

            if not host or not port:
                return False

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                return result == 0

        except Exception:
            return False


class SmartRoutingService:
    """Service for smart routing based on performance."""

    def __init__(self, log_callback: Callable[[str, LogLevel], None]):
        self.log = log_callback
        self._routing_rules = []
        self._performance_data = {}

    def add_routing_rule(self, rule: Dict[str, Any]) -> bool:
        """Add a smart routing rule."""
        try:
            self._routing_rules.append(rule)
            self.log(
                f"Added routing rule: {rule.get('name', 'Unnamed')}", LogLevel.SUCCESS
            )
            return True
        except Exception as e:
            self.log(f"Failed to add routing rule: {e}", LogLevel.ERROR)
            return False

    def remove_routing_rule(self, rule_name: str) -> bool:
        """Remove a routing rule."""
        try:
            self._routing_rules = [
                r for r in self._routing_rules if r.get("name") != rule_name
            ]
            self.log(f"Removed routing rule: {rule_name}", LogLevel.SUCCESS)
            return True
        except Exception as e:
            self.log(f"Failed to remove routing rule: {e}", LogLevel.ERROR)
            return False

    def get_routing_rules(self) -> List[Dict[str, Any]]:
        """Get all routing rules."""
        return self._routing_rules.copy()

    def update_performance_data(self, server_id: str, performance: Dict[str, Any]):
        """Update performance data for a server."""
        self._performance_data[server_id] = performance

    def get_optimal_route(self, destination: str) -> Optional[Dict[str, Any]]:
        """Get optimal route for a destination."""
        # This would implement smart routing logic
        # For now, return the first available rule
        return self._routing_rules[0] if self._routing_rules else None


class GeoBlockingDetectionService:
    """Service for detecting geo-blocking."""

    def __init__(self, log_callback: Callable[[str, LogLevel], None]):
        self.log = log_callback
        self._test_urls = [
            "https://www.google.com",
            "https://www.youtube.com",
            "https://www.facebook.com",
            "https://www.twitter.com",
            "https://www.instagram.com",
        ]

    def detect_geo_blocking(self, proxy_address: str) -> Dict[str, Any]:
        """Detect geo-blocking for various services."""
        results = {}

        for url in self._test_urls:
            try:
                # Test without proxy
                response_direct = requests.get(url, timeout=10)
                direct_accessible = response_direct.status_code == 200

                # Test with proxy
                proxies = {
                    "http": f"http://{proxy_address}",
                    "https": f"http://{proxy_address}",
                }
                response_proxy = requests.get(url, proxies=proxies, timeout=10)
                proxy_accessible = response_proxy.status_code == 200

                results[url] = {
                    "direct_accessible": direct_accessible,
                    "proxy_accessible": proxy_accessible,
                    "blocked": not direct_accessible and proxy_accessible,
                }

            except Exception as e:
                results[url] = {
                    "direct_accessible": False,
                    "proxy_accessible": False,
                    "blocked": False,
                    "error": str(e),
                }

        return results
