"""
Diagnostics Service for Onix
Provides network diagnostics and debugging tools
"""

import subprocess
import socket
import threading
import time
import psutil
from typing import Callable, Dict, Any, List
from datetime import datetime, timedelta
from constants import LogLevel


class NetworkDiagnosticsService:
    """Service for network diagnostics."""

    def __init__(self, log_callback: Callable[[str, LogLevel], None]):
        self.log = log_callback
        self._diagnostics_results = {}

    def run_full_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive network diagnostics."""
        self.log("Starting network diagnostics...", LogLevel.INFO)

        results = {
            "timestamp": datetime.now().isoformat(),
            "system_info": self._get_system_info(),
            "network_interfaces": self._get_network_interfaces(),
            "dns_resolution": self._test_dns_resolution(),
            "connectivity": self._test_connectivity(),
            "proxy_test": self._test_proxy_connectivity(),
            "firewall_status": self._check_firewall_status(),
            "routing_table": self._get_routing_table(),
            "port_scan": self._scan_common_ports(),
            "bandwidth_test": self._test_bandwidth(),
            "latency_test": self._test_latency(),
        }

        self._diagnostics_results = results
        self.log("Network diagnostics completed", LogLevel.SUCCESS)
        return results

    def get_diagnostics_summary(self) -> Dict[str, Any]:
        """Get diagnostics summary with issues and recommendations."""
        if not self._diagnostics_results:
            return {"error": "No diagnostics data available"}

        issues = []
        recommendations = []

        # Check DNS resolution
        dns_results = self._diagnostics_results.get("dns_resolution", {})
        if not dns_results.get("success", False):
            issues.append("DNS resolution failed")
            recommendations.append("Check DNS server settings and connectivity")

        # Check connectivity
        connectivity = self._diagnostics_results.get("connectivity", {})
        if not connectivity.get("internet_accessible", False):
            issues.append("No internet connectivity")
            recommendations.append("Check network connection and firewall settings")

        # Check proxy
        proxy_test = self._diagnostics_results.get("proxy_test", {})
        if not proxy_test.get("proxy_working", False):
            issues.append("Proxy connection failed")
            recommendations.append("Check proxy server configuration and status")

        # Check latency
        latency = self._diagnostics_results.get("latency_test", {})
        avg_latency = latency.get("average_latency", 0)
        if avg_latency > 1000:  # > 1 second
            issues.append("High latency detected")
            recommendations.append("Consider switching to a closer server")

        return {
            "issues": issues,
            "recommendations": recommendations,
            "overall_status": "healthy" if not issues else "issues_detected",
            "timestamp": self._diagnostics_results.get("timestamp"),
        }

    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        try:
            return {
                "platform": psutil.WINDOWS if hasattr(psutil, "WINDOWS") else "Unknown",
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "disk_usage": (
                    psutil.disk_usage("/").percent
                    if hasattr(psutil, "disk_usage")
                    else 0
                ),
            }
        except Exception as e:
            return {"error": str(e)}

    def _get_network_interfaces(self) -> List[Dict[str, Any]]:
        """Get network interface information."""
        try:
            interfaces = []
            for interface, addrs in psutil.net_if_addrs().items():
                interface_info = {"name": interface, "addresses": []}

                for addr in addrs:
                    interface_info["addresses"].append(
                        {
                            "family": str(addr.family),
                            "address": addr.address,
                            "netmask": addr.netmask,
                            "broadcast": addr.broadcast,
                        }
                    )

                interfaces.append(interface_info)

            return interfaces
        except Exception as e:
            return [{"error": str(e)}]

    def _test_dns_resolution(self) -> Dict[str, Any]:
        """Test DNS resolution."""
        test_domains = ["google.com", "cloudflare.com", "1.1.1.1"]
        results = {"success": True, "domains": {}}

        for domain in test_domains:
            try:
                socket.gethostbyname(domain)
                results["domains"][domain] = {"resolved": True}
            except socket.gaierror as e:
                results["domains"][domain] = {"resolved": False, "error": str(e)}
                results["success"] = False

        return results

    def _test_connectivity(self) -> Dict[str, Any]:
        """Test basic connectivity."""
        test_urls = [
            "http://www.google.com",
            "https://www.cloudflare.com",
            "http://httpbin.org/ip",
        ]

        results = {"internet_accessible": False, "urls": {}}

        for url in test_urls:
            try:
                import requests

                response = requests.get(url, timeout=10)
                results["urls"][url] = {
                    "accessible": response.status_code == 200,
                    "status_code": response.status_code,
                }
                if response.status_code == 200:
                    results["internet_accessible"] = True
            except Exception as e:
                results["urls"][url] = {"accessible": False, "error": str(e)}

        return results

    def _test_proxy_connectivity(
        self, proxy_address: str = "127.0.0.1:2082"
    ) -> Dict[str, Any]:
        """Test proxy connectivity."""
        try:
            host, port = proxy_address.split(":")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)
                result = sock.connect_ex((host, int(port)))

                return {
                    "proxy_working": result == 0,
                    "proxy_address": proxy_address,
                    "connection_time": time.time(),
                }
        except Exception as e:
            return {
                "proxy_working": False,
                "proxy_address": proxy_address,
                "error": str(e),
            }

    def _check_firewall_status(self) -> Dict[str, Any]:
        """Check firewall status."""
        try:
            # Windows firewall check
            result = subprocess.run(
                ["netsh", "advfirewall", "show", "allprofiles", "state"],
                capture_output=True,
                text=True,
                shell=True,
            )

            return {
                "firewall_enabled": "State" in result.stdout and "ON" in result.stdout,
                "output": result.stdout,
            }
        except Exception as e:
            return {"error": str(e)}

    def _get_routing_table(self) -> List[Dict[str, Any]]:
        """Get routing table."""
        try:
            result = subprocess.run(
                ["route", "print"], capture_output=True, text=True, shell=True
            )

            routes = []
            lines = result.stdout.split("\n")

            for line in lines:
                if line.strip() and not line.startswith("="):
                    parts = line.split()
                    if len(parts) >= 4 and parts[0] != "Network":
                        routes.append(
                            {
                                "network": parts[0],
                                "netmask": parts[1],
                                "gateway": parts[2],
                                "interface": parts[3] if len(parts) > 3 else "",
                            }
                        )

            return routes
        except Exception as e:
            return [{"error": str(e)}]

    def _scan_common_ports(self) -> Dict[str, Any]:
        """Scan common ports for connectivity."""
        common_ports = [80, 443, 53, 22, 21, 25, 110, 143, 993, 995]
        results = {"ports": {}}

        for port in common_ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(1)
                    result = sock.connect_ex(("127.0.0.1", port))
                    results["ports"][port] = {
                        "open": result == 0,
                        "service": self._get_port_service(port),
                    }
            except Exception as e:
                results["ports"][port] = {"open": False, "error": str(e)}

        return results

    def _get_port_service(self, port: int) -> str:
        """Get service name for port."""
        services = {
            80: "HTTP",
            443: "HTTPS",
            53: "DNS",
            22: "SSH",
            21: "FTP",
            25: "SMTP",
            110: "POP3",
            143: "IMAP",
            993: "IMAPS",
            995: "POP3S",
        }
        return services.get(port, "Unknown")

    def _test_bandwidth(self) -> Dict[str, Any]:
        """Test bandwidth (simplified)."""
        try:
            # Simple bandwidth test using requests
            import requests

            start_time = time.time()

            response = requests.get(
                "http://speedtest.tele2.net/10MB.zip", timeout=30, stream=True
            )

            total_bytes = 0
            for chunk in response.iter_content(chunk_size=8192):
                total_bytes += len(chunk)

            end_time = time.time()
            duration = end_time - start_time

            if duration > 0:
                bandwidth_mbps = (total_bytes * 8) / (duration * 1000000)
                return {
                    "bandwidth_mbps": bandwidth_mbps,
                    "bytes_transferred": total_bytes,
                    "duration": duration,
                }
            else:
                return {"error": "Test duration too short"}

        except Exception as e:
            return {"error": str(e)}

    def _test_latency(self) -> Dict[str, Any]:
        """Test latency to various servers."""
        test_servers = [
            ("8.8.8.8", "Google DNS"),
            ("1.1.1.1", "Cloudflare DNS"),
            ("208.67.222.222", "OpenDNS"),
        ]

        results = {"servers": {}, "average_latency": 0}
        total_latency = 0
        successful_tests = 0

        for server, name in test_servers:
            try:
                start_time = time.time()
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(5)
                    sock.connect((server, 53))
                end_time = time.time()

                latency = (end_time - start_time) * 1000  # Convert to milliseconds
                results["servers"][name] = {
                    "server": server,
                    "latency_ms": latency,
                    "success": True,
                }

                total_latency += latency
                successful_tests += 1

            except Exception as e:
                results["servers"][name] = {
                    "server": server,
                    "latency_ms": -1,
                    "success": False,
                    "error": str(e),
                }

        if successful_tests > 0:
            results["average_latency"] = total_latency / successful_tests

        return results


class ConnectionAnalyticsService:
    """Service for connection analytics and monitoring."""

    def __init__(self, log_callback: Callable[[str, LogLevel], None]):
        self.log = log_callback
        self._connection_log = []
        self._analytics_data = {}
        self._monitoring = False
        self._monitor_thread = None
        self._stop_event = threading.Event()

    def start_monitoring(self) -> bool:
        """Start connection monitoring."""
        if self._monitoring:
            return False

        try:
            self._monitoring = True
            self._stop_event.clear()

            self._monitor_thread = threading.Thread(
                target=self._monitor_connections, daemon=True
            )
            self._monitor_thread.start()

            self.log("Connection analytics monitoring started", LogLevel.SUCCESS)
            return True

        except Exception as e:
            self.log(f"Failed to start connection monitoring: {e}", LogLevel.ERROR)
            return False

    def stop_monitoring(self):
        """Stop connection monitoring."""
        if not self._monitoring:
            return

        self._stop_event.set()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2)

        self._monitoring = False
        self.log("Connection analytics monitoring stopped", LogLevel.INFO)

    def log_connection_event(
        self, event_type: str, server_name: str, details: Dict[str, Any] = None
    ):
        """Log a connection event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "server_name": server_name,
            "details": details or {},
        }

        self._connection_log.append(event)

        # Keep only last 1000 events
        if len(self._connection_log) > 1000:
            self._connection_log = self._connection_log[-1000:]

    def get_connection_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """Get connection analytics for specified hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        recent_events = [
            event
            for event in self._connection_log
            if datetime.fromisoformat(event["timestamp"]) >= cutoff_time
        ]

        if not recent_events:
            return {"error": "No data available for the specified period"}

        # Analyze events
        total_connections = len(
            [e for e in recent_events if e["event_type"] == "connected"]
        )
        total_disconnections = len(
            [e for e in recent_events if e["event_type"] == "disconnected"]
        )
        total_errors = len([e for e in recent_events if e["event_type"] == "error"])

        # Server usage statistics
        server_usage = {}
        for event in recent_events:
            server = event["server_name"]
            if server not in server_usage:
                server_usage[server] = 0
            server_usage[server] += 1

        # Connection duration analysis
        connection_durations = []
        connection_start = None

        for event in recent_events:
            if event["event_type"] == "connected":
                connection_start = datetime.fromisoformat(event["timestamp"])
            elif event["event_type"] == "disconnected" and connection_start:
                connection_end = datetime.fromisoformat(event["timestamp"])
                duration = (connection_end - connection_start).total_seconds()
                connection_durations.append(duration)
                connection_start = None

        return {
            "period_hours": hours,
            "total_connections": total_connections,
            "total_disconnections": total_disconnections,
            "total_errors": total_errors,
            "success_rate": (
                (total_connections / (total_connections + total_errors)) * 100
                if (total_connections + total_errors) > 0
                else 0
            ),
            "server_usage": server_usage,
            "average_connection_duration": (
                sum(connection_durations) / len(connection_durations)
                if connection_durations
                else 0
            ),
            "max_connection_duration": (
                max(connection_durations) if connection_durations else 0
            ),
            "min_connection_duration": (
                min(connection_durations) if connection_durations else 0
            ),
            "events": recent_events[-50:],  # Last 50 events
        }

    def _monitor_connections(self):
        """Monitor connection status."""
        while not self._stop_event.is_set():
            try:
                # Monitor active connections
                connections = psutil.net_connections()
                active_connections = len(
                    [c for c in connections if c.status == "ESTABLISHED"]
                )

                self._analytics_data["active_connections"] = active_connections
                self._analytics_data["last_update"] = datetime.now().isoformat()

                time.sleep(10)  # Update every 10 seconds

            except Exception as e:
                self.log(f"Connection monitoring error: {e}", LogLevel.ERROR)
                time.sleep(30)


class DebugModeService:
    """Service for debug mode functionality."""

    def __init__(self, log_callback: Callable[[str, LogLevel], None]):
        self.log = log_callback
        self._debug_mode = False
        self._debug_log = []
        self._debug_callbacks = []

    def enable_debug_mode(self, enabled: bool = True):
        """Enable or disable debug mode."""
        self._debug_mode = enabled
        self.log(f"Debug mode {'enabled' if enabled else 'disabled'}", LogLevel.INFO)

    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled."""
        return self._debug_mode

    def debug_log(self, message: str, category: str = "general", data: Any = None):
        """Log a debug message."""
        if not self._debug_mode:
            return

        debug_entry = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "message": message,
            "data": data,
        }

        self._debug_log.append(debug_entry)

        # Keep only last 1000 debug entries
        if len(self._debug_log) > 1000:
            self._debug_log = self._debug_log[-1000:]

        # Call registered callbacks
        for callback in self._debug_callbacks:
            try:
                callback(debug_entry)
            except Exception as e:
                self.log(f"Debug callback error: {e}", LogLevel.ERROR)

    def get_debug_log(self, category: str = None) -> List[Dict[str, Any]]:
        """Get debug log entries."""
        if category:
            return [entry for entry in self._debug_log if entry["category"] == category]
        return self._debug_log.copy()

    def clear_debug_log(self):
        """Clear debug log."""
        self._debug_log.clear()
        self.log("Debug log cleared", LogLevel.INFO)

    def register_debug_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a debug callback."""
        self._debug_callbacks.append(callback)

    def unregister_debug_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Unregister a debug callback."""
        if callback in self._debug_callbacks:
            self._debug_callbacks.remove(callback)
