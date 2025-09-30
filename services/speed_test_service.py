"""
Speed Test Service for Onix
Provides real-time speed testing functionality
"""

import threading
import time
import requests
import socket
from typing import Callable, Optional, Dict, Any
from constants import LogLevel


class SpeedTestService:
    """Service for performing speed tests through proxy connections."""

    def __init__(self, log_callback: Callable[[str, LogLevel], None]):
        self.log = log_callback
        self._is_testing = False
        self._stop_event = threading.Event()
        self._test_thread = None

    def start_speed_test(
        self,
        proxy_address: str,
        duration: int = 10,
        callback: Optional[Callable[[float, float], None]] = None,
    ) -> bool:
        """Start a speed test through the given proxy."""
        if self._is_testing:
            self.log("Speed test is already running", LogLevel.WARNING)
            return False

        self._is_testing = True
        self._stop_event.clear()

        self._test_thread = threading.Thread(
            target=self._run_speed_test,
            args=(proxy_address, duration, callback),
            daemon=True,
        )
        self._test_thread.start()

        self.log(f"Started speed test for {duration} seconds", LogLevel.INFO)
        return True

    def stop_speed_test(self):
        """Stop the current speed test."""
        if not self._is_testing:
            return

        self._stop_event.set()
        if self._test_thread and self._test_thread.is_alive():
            self._test_thread.join(timeout=2)

        self._is_testing = False
        self.log("Speed test stopped", LogLevel.INFO)

    def is_testing(self) -> bool:
        """Check if speed test is currently running."""
        return self._is_testing

    def _run_speed_test(
        self,
        proxy_address: str,
        duration: int,
        callback: Optional[Callable[[float, float], None]],
    ):
        """Run the actual speed test."""
        try:
            proxies = {
                "http": f"http://{proxy_address}",
                "https": f"http://{proxy_address}",
            }

            # Test URLs for download speed
            test_urls = [
                "http://speedtest.tele2.net/10MB.zip",
                "http://speedtest.tele2.net/100MB.zip",
                "https://releases.ubuntu.com/20.04/ubuntu-20.04.6-desktop-amd64.iso",
            ]

            start_time = time.time()
            total_downloaded = 0
            total_uploaded = 0

            while time.time() - start_time < duration and not self._stop_event.is_set():
                # Download test
                try:
                    response = requests.get(
                        test_urls[0], proxies=proxies, timeout=5, stream=True
                    )

                    chunk_size = 8192
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if self._stop_event.is_set():
                            break
                        total_downloaded += len(chunk)

                        # Calculate speeds
                        elapsed = time.time() - start_time
                        if elapsed > 0:
                            download_speed = total_downloaded / elapsed
                            upload_speed = total_uploaded / elapsed

                            if callback:
                                callback(download_speed, upload_speed)

                except requests.exceptions.RequestException as e:
                    self.log(f"Download test error: {e}", LogLevel.WARNING)

                # Small delay between tests
                time.sleep(0.1)

            # Final results
            elapsed = time.time() - start_time
            if elapsed > 0:
                final_download_speed = total_downloaded / elapsed
                final_upload_speed = total_uploaded / elapsed

                if callback:
                    callback(final_download_speed, final_upload_speed)

                self.log(
                    f"Speed test completed: {final_download_speed/1024/1024:.2f} MB/s download, "
                    f"{final_upload_speed/1024/1024:.2f} MB/s upload",
                    LogLevel.SUCCESS,
                )

        except Exception as e:
            self.log(f"Speed test error: {e}", LogLevel.ERROR)
        finally:
            self._is_testing = False


class AutoFailoverService:
    """Service for automatic failover between servers."""

    def __init__(self, log_callback: Callable[[str, LogLevel], None]):
        self.log = log_callback
        self._is_monitoring = False
        self._stop_event = threading.Event()
        self._monitor_thread = None
        self._current_server = None
        self._servers = []
        self._failover_callback = None

    def start_monitoring(
        self,
        servers: list,
        current_server: Dict[str, Any],
        failover_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        """Start monitoring servers for automatic failover."""
        if self._is_monitoring:
            self.log("Auto-failover is already running", LogLevel.WARNING)
            return False

        self._servers = servers
        self._current_server = current_server
        self._failover_callback = failover_callback
        self._is_monitoring = True
        self._stop_event.clear()

        self._monitor_thread = threading.Thread(
            target=self._monitor_servers, daemon=True
        )
        self._monitor_thread.start()

        self.log("Started auto-failover monitoring", LogLevel.INFO)
        return True

    def stop_monitoring(self):
        """Stop auto-failover monitoring."""
        if not self._is_monitoring:
            return

        self._stop_event.set()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2)

        self._is_monitoring = False
        self.log("Stopped auto-failover monitoring", LogLevel.INFO)

    def is_monitoring(self) -> bool:
        """Check if auto-failover is currently monitoring."""
        return self._is_monitoring

    def _monitor_servers(self):
        """Monitor servers and perform failover if needed."""
        while not self._stop_event.is_set():
            try:
                # Test current server
                if self._current_server:
                    if not self._test_server_health(self._current_server):
                        self.log(
                            f"Current server {self._current_server.get('name')} failed health check",
                            LogLevel.WARNING,
                        )

                        # Find best alternative server
                        best_server = self._find_best_server()
                        if best_server and best_server != self._current_server:
                            self.log(
                                f"Switching to server: {best_server.get('name')}",
                                LogLevel.INFO,
                            )

                            if self._failover_callback:
                                self._failover_callback(best_server)

                            self._current_server = best_server

                # Wait before next check
                self._stop_event.wait(30)  # Check every 30 seconds

            except Exception as e:
                self.log(f"Auto-failover error: {e}", LogLevel.ERROR)
                self._stop_event.wait(10)  # Wait 10 seconds on error

    def _test_server_health(self, server: Dict[str, Any]) -> bool:
        """Test if a server is healthy."""
        try:
            # Simple TCP ping test
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

    def _find_best_server(self) -> Optional[Dict[str, Any]]:
        """Find the best available server."""
        best_server = None
        best_ping = float("inf")

        for server in self._servers:
            if server == self._current_server:
                continue

            ping = server.get("tcp_ping", -1)
            if ping > 0 and ping < best_ping:
                best_ping = ping
                best_server = server

        return best_server
