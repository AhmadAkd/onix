import threading
import time
from typing import Callable, Dict, List, Optional

from constants import LogLevel, HEALTH_CHECK_EMA_ALPHA, HEALTH_CHECK_MAX_BACKOFF, HEALTH_CHECK_MIN_BACKOFF, TEST_ENDPOINTS
from services.ping_service import direct_tcp, proxy_tcp_connect, url_latency_via_proxy


class HealthChecker:
    """Periodic health checker with exponential backoff and EMA smoothing."""

    def __init__(self, settings: dict, log_callback: Callable[[str, LogLevel], None]):
        self.settings = settings
        self.log = log_callback
        self._stop_event = threading.Event()
        self._thread = None
        self._server_stats = {}  # server_id -> {tcp_ema, url_ema, failures, last_test}
        self._test_core_manager = None
        self._test_callback = None

    def set_test_core_manager(self, core_manager):
        """Set the persistent test core manager for proxy-based tests."""
        self._test_core_manager = core_manager

    def set_test_callback(self, callback: Callable[[dict, int, str], None]):
        """Set callback to report test results to UI."""
        self._test_callback = callback

    def start(self, servers: List[dict], test_types: List[str] = None, interval_seconds: int = 30):
        """Start periodic health checking."""
        if self._thread and self._thread.is_alive():
            return

        if test_types is None:
            test_types = ["tcp", "url"]

        self._test_types = test_types
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._health_check_loop,
            args=(servers, interval_seconds),
            daemon=True
        )
        self._thread.start()
        self.log(
            f"Health checker started for {test_types} with {interval_seconds}s interval", LogLevel.INFO)

    def stop(self):
        """Stop health checking."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self.log("Health checker stopped", LogLevel.INFO)

    def _health_check_loop(self, servers: List[dict], interval_seconds: int):
        """Main health check loop."""
        while not self._stop_event.is_set():
            for server in servers:
                if self._stop_event.is_set():
                    break

                server_id = server.get("id")
                if not server_id:
                    continue

                # Check if we should test this server (backoff logic)
                if not self._should_test_server(server_id):
                    continue

                # Test the server
                self._test_single_server(server)

                # Small delay between servers
                time.sleep(0.5)

            # Wait for next interval
            self._stop_event.wait(interval_seconds)

    def _should_test_server(self, server_id: str) -> bool:
        """Check if server should be tested based on backoff logic."""
        stats = self._server_stats.get(server_id, {})
        failures = stats.get("failures", 0)
        last_test = stats.get("last_test", 0)

        # Exponential backoff: 1s, 2s, 4s, 8s, 16s, max 60s
        backoff_seconds = min(HEALTH_CHECK_MAX_BACKOFF,
                              HEALTH_CHECK_MIN_BACKOFF * (2 ** min(failures, 6)))
        return time.time() - last_test > backoff_seconds

    def _test_single_server(self, server: dict):
        """Test a single server and update stats."""
        server_id = server.get("id")
        server_name = server.get("name", "Unknown")

        # Initialize stats if needed
        if server_id not in self._server_stats:
            self._server_stats[server_id] = {
                "tcp_ema": None,
                "url_ema": None,
                "failures": 0,
                "last_test": 0
            }

        stats = self._server_stats[server_id]
        stats["last_test"] = time.time()

        # Test TCP (direct or via proxy) if enabled
        tcp_result = -1
        if "tcp" in self._test_types:
            tcp_result = self._test_tcp(server)
            if tcp_result != -1:
                stats["failures"] = 0  # Reset failure count on success
                stats["tcp_ema"] = self._update_ema(
                    stats["tcp_ema"], tcp_result)
            else:
                stats["failures"] += 1
                stats["tcp_ema"] = None

        # Test URL (via proxy if available) if enabled
        url_result = -1
        if "url" in self._test_types:
            url_result = self._test_url(server)
            if url_result != -1:
                stats["url_ema"] = self._update_ema(
                    stats["url_ema"], url_result)
            else:
                stats["url_ema"] = None

        # Report results to UI
        if self._test_callback:
            if tcp_result != -1:
                self._test_callback(server, int(
                    stats["tcp_ema"] or tcp_result), "tcp")
            if url_result != -1:
                self._test_callback(server, int(
                    stats["url_ema"] or url_result), "url")

    def _test_tcp(self, server: dict) -> int:
        """Test TCP connectivity."""
        if self._test_core_manager:
            # Use proxy-based test
            proxy_address = self._test_core_manager.get_proxy_address(
                server.get("id"))
            if proxy_address:
                tcp_config = TEST_ENDPOINTS["tcp"]
                return proxy_tcp_connect(proxy_address, tcp_config["host"], tcp_config["port"])

        # Fallback to direct TCP
        return direct_tcp(server.get("server"), server.get("port"))

    def _test_url(self, server: dict) -> int:
        """Test URL latency."""
        if not self._test_core_manager:
            return -1

        proxy_address = self._test_core_manager.get_proxy_address(
            server.get("id"))
        if not proxy_address:
            return -1

        url_config = TEST_ENDPOINTS["url"]
        return url_latency_via_proxy(
            proxy_address,
            url=url_config["url"],
            is_cancelled=lambda: self._stop_event.is_set()
        )

    def _update_ema(self, current_ema: Optional[float], new_value: int, alpha: float = None) -> float:
        """Update exponential moving average."""
        if alpha is None:
            alpha = HEALTH_CHECK_EMA_ALPHA
        if current_ema is None:
            return float(new_value)
        return alpha * new_value + (1 - alpha) * current_ema

    def get_server_stats(self, server_id: str) -> dict:
        """Get current stats for a server."""
        return self._server_stats.get(server_id, {})

    def reset_server_stats(self, server_id: str):
        """Reset stats for a server."""
        if server_id in self._server_stats:
            del self._server_stats[server_id]
