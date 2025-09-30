import json
import os
import socket
import time
import requests
import subprocess
import tempfile
import sys  # Added

import utils
from constants import (
    LogLevel,
    PROXY_HOST,
    TCP_PING_TIMEOUT,
    URL_TEST_TIMEOUT,
    GET_EXTERNAL_IP_TIMEOUT,
    WAIT_FOR_PROXY_TIMEOUT,
    WAIT_FOR_PROXY_INTERVAL,
    URL_TEST_DEFAULT_URL,
    GET_EXTERNAL_IP_URL,
    SINGBOX_EXECUTABLE_NAMES,
    XRAY_EXECUTABLE_NAMES,
)


def find_free_port():
    """Finds and returns an available TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
        return port


def tcp_ping(host, port, timeout=TCP_PING_TIMEOUT, proxy_address=None):
    """Pings a TCP host and port to measure latency."""
    start_time = time.time()
    try:
        if proxy_address:
            # For TCP tests through a proxy, we establish a TCP connection to the target
            # via the HTTP proxy using a CONNECT request. This is faster than a full HTTP GET.
            proxy_host, proxy_port = proxy_address.split(":")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                sock.connect((proxy_host, int(proxy_port)))

                # Send HTTP CONNECT request to the proxy
                connect_request = (
                    f"CONNECT {host}:{port} HTTP/1.1\r\n"
                    f"Host: {host}:{port}\r\n\r\n"
                )
                sock.sendall(connect_request.encode())
                response = sock.recv(1024)
                # Be tolerant: accept HTTP/1.0 or HTTP/1.1 and any 200 status
                try:
                    header_line = response.split(b"\r\n", 1)[0]
                except Exception:
                    header_line = response
                if b" 200" not in header_line or not header_line.startswith(b"HTTP/"):
                    raise ConnectionRefusedError("Proxy CONNECT failed")
        else:
            # Direct TCP connection
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                sock.connect((host, port))
        # If we reach here, the connection was successful.
        end_time = time.time()
        return round((end_time - start_time) * 1000)
    except (socket.timeout, ConnectionRefusedError, OSError):
        return -1  # Return -1 on failure for TCP tests
    except Exception:
        # For any other unexpected errors, return -1
        return -1


def _url_test_request(proxy_address, url=URL_TEST_DEFAULT_URL, timeout=URL_TEST_TIMEOUT):
    """Tests a URL through a given proxy to measure real-world latency."""
    proxies = {"http": f"http://{proxy_address}",
               "https": f"http://{proxy_address}"}
    try:
        start_time = time.time()
        response = requests.get(url, proxies=proxies, timeout=timeout)
        end_time = time.time()
        # Accept 204 (No Content) and 200 (OK) as success to better support
        # various captive portals/CDNs/proxies that return 200.
        if response.status_code in (204, 200):
            return round((end_time - start_time) * 1000)
    except requests.exceptions.RequestException:
        pass
    return -1


def perform_test_on_proxy(proxy_address, test_type="url"):
    """
    Performs a latency test on a given proxy address.
    'url': Performs a full HTTP GET request.
    'tcp': Performs a faster TCP-only handshake test.
    """
    if test_type == "tcp":
        # For TCP test, we just ping a known reliable and fast host like Google's DNS.
        # The connection goes through the proxy, so it measures the protocol latency.
        return tcp_ping("8.8.8.8", 53, timeout=TCP_PING_TIMEOUT, proxy_address=proxy_address), "direct_tcp"
    else:  # Default to URL test
        return _url_test_request(proxy_address, timeout=URL_TEST_TIMEOUT), "url"


def get_external_ip(proxy_address, timeout=GET_EXTERNAL_IP_TIMEOUT):
    """Fetches the external IP address through a given proxy."""
    proxies = {"http": f"http://{proxy_address}",
               "https": f"http://{proxy_address}"}
    try:
        response = requests.get(GET_EXTERNAL_IP_URL,
                                proxies=proxies, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException:
        return "N/A"


def url_test(proxy_address, url=URL_TEST_DEFAULT_URL, timeout=URL_TEST_TIMEOUT):
    """Backward-compatible wrapper used by managers to test URL through proxy.
    Returns latency in ms or -1 on failure.
    """
    return _url_test_request(proxy_address, url=url, timeout=timeout)


def wait_for_proxy(host, port, timeout=WAIT_FOR_PROXY_TIMEOUT):
    """Waits for the proxy server to become available."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(
                (host, port), timeout=WAIT_FOR_PROXY_INTERVAL
            ):
                return True
        except (socket.timeout, ConnectionRefusedError):
            time.sleep(WAIT_FOR_PROXY_INTERVAL)
    return False


class CoreTester:
    """
    Manages a temporary core instance (sing-box or Xray) for testing multiple servers.
    It creates a single core process with multiple inbounds, each routing to a different server outbound.
    """

    def __init__(self, servers, settings, config_generator, log_callback):
        self.servers = servers
        self.settings = settings
        self.config_generator = config_generator
        self.log = log_callback
        self.temp_config_file = None
        self.core_process = None
        self.server_ports = {}  # Maps server ID to its test port
        self._ready = False

    def __enter__(self):
        try:
            # 1. Generate the special test configuration
            test_config = self.config_generator.generate_test_config(
                self.servers, self.settings)

            # 2. Map server IDs to their assigned inbound ports
            for i, server in enumerate(self.servers):
                port = 11000 + i
                self.server_ports[server.get("id")] = port

            # 3. Write config to a temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".json", encoding="utf-8"
            ) as f:
                json.dump(test_config, f, indent=2)
                self.temp_config_file = f.name

            # 4. Determine which core executable to use
            active_core = self.settings.get("active_core", "sing-box")
            os_key = "windows" if sys.platform.startswith(
                "win") else sys.platform.lower()

            if active_core == "sing-box":
                executable_name = SINGBOX_EXECUTABLE_NAMES.get(
                    os_key, "sing-box")
            else:  # xray
                executable_name = XRAY_EXECUTABLE_NAMES.get(os_key, "xray")

            executable_path = utils.get_resource_path(executable_name)

            command = [
                executable_path,
                "run",
                "-c",
                self.temp_config_file,
            ]

            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith(
                "win") else 0

            self.core_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                creationflags=creationflags,
            )

            # 5. Wait for the first proxy port to become available
            first_port = 11000
            if not wait_for_proxy(PROXY_HOST, first_port):
                # --- Enhanced Error Handling ---
                # Check if the process terminated early, which usually indicates a config error.
                if self.core_process.poll() is not None:
                    try:
                        # Try to get output without blocking forever
                        stdout_output, stderr_output = self.core_process.communicate(
                            timeout=1)
                        error_details = stderr_output.strip() or stdout_output.strip()
                        if not error_details:
                            error_details = f"Process exited with code {self.core_process.returncode}."
                    except subprocess.TimeoutExpired:
                        error_details = "Process exited but could not read its error output."
                    raise RuntimeError(
                        f"Temporary {active_core} instance failed to start. Core error: {error_details}")
                else:
                    raise RuntimeError(
                        f"Temporary {active_core} instance for testing did not start in time.")

            self._ready = True
            self.log(
                f"CoreTester ready with {active_core} for {len(self.servers)} servers.", LogLevel.DEBUG)

            return self

        except FileNotFoundError:
            self.log(
                f"{executable_name} not found. Please ensure it's in the correct directory.", LogLevel.ERROR)
            raise
        except Exception as e:
            self.log(
                f"Error starting CoreTester instance: {e}", LogLevel.ERROR)
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.core_process:
            self.core_process.terminate()
            self.core_process.wait()
        if self.temp_config_file and os.path.exists(self.temp_config_file):
            try:
                os.remove(self.temp_config_file)
            except OSError as e:
                self.log(
                    f"Could not remove temp config file {self.temp_config_file}: {e}", LogLevel.WARNING)

    def is_ready(self):
        return self._ready

    def test_server(self, server_config, test_type="url"):
        """Tests a single server by using its assigned proxy port."""
        server_id = server_config.get("id")
        port = self.server_ports.get(server_id)
        if not port:
            self.log(
                f"No port assigned for server ID {server_id}", LogLevel.ERROR)
            return -1

        proxy_address = f"{PROXY_HOST}:{port}"
        # Use the generic test function, which now returns a tuple (result, type)
        return perform_test_on_proxy(proxy_address, test_type)
