import json
import os
import socket
import time
import requests
import subprocess
import tempfile
import sys  # Added

import utils
import config_generator
import constants  # Changed from from constants import (...)
from constants import (
    PROXY_HOST,
    PROXY_PORT,
    PROXY_SERVER_ADDRESS,
    TCP_PING_TIMEOUT,
    URL_TEST_TIMEOUT,
    GET_EXTERNAL_IP_TIMEOUT,
    WAIT_FOR_PROXY_TIMEOUT,
    WAIT_FOR_PROXY_INTERVAL,
    URL_TEST_DEFAULT_URL,
    GET_EXTERNAL_IP_URL,
)
from message_utils import show_error_message


def tcp_ping(host, port, timeout=TCP_PING_TIMEOUT):
    """Pings a TCP host and port to measure latency."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        start_time = time.time()
        sock.connect((host, port))
        end_time = time.time()
        sock.close()
        return int((end_time - start_time) * 1000)
    except (socket.timeout, ConnectionRefusedError, OSError):
        return -1


def url_test(proxy_address, url=URL_TEST_DEFAULT_URL, timeout=URL_TEST_TIMEOUT):
    """Tests a URL through a given proxy to measure real-world latency."""
    proxies = {"http": f"http://{proxy_address}", "https": f"http://{proxy_address}"}
    try:
        start_time = time.time()
        response = requests.get(url, proxies=proxies, timeout=timeout)
        end_time = time.time()
        if response.status_code == 204:
            return int((end_time - start_time) * 1000)
    except requests.exceptions.RequestException:
        pass
    return -1


def get_external_ip(proxy_address, timeout=GET_EXTERNAL_IP_TIMEOUT):
    """Fetches the external IP address through a given proxy."""
    proxies = {"http": f"http://{proxy_address}", "https": f"http://{proxy_address}"}
    try:
        response = requests.get(GET_EXTERNAL_IP_URL, proxies=proxies, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException:
        return "N/A"


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


class TemporarySingboxInstance:
    def __init__(self, config_content, proxy_host, proxy_port):
        self.config_content = config_content
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.temp_config_file = None
        self.singbox_process = None

    def __enter__(self):
        try:
            # Create temporary config file
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".json", encoding="utf-8"
            ) as f:
                json.dump(self.config_content, f, indent=2)
                self.temp_config_file = f.name

            # Determine sing-box executable name based on OS
            # sys.platform can be 'win32', 'linux', 'darwin'
            os_key = (
                "windows" if sys.platform.startswith("win") else sys.platform.lower()
            )
            singbox_executable = constants.SINGBOX_EXECUTABLE_NAMES.get(os_key)

            if not singbox_executable:
                raise RuntimeError(
                    f"Unsupported OS for sing-box executable: {sys.platform}"
                )

            command = [
                utils.get_resource_path(singbox_executable),
                "run",
                "-c",
                self.temp_config_file,
            ]

            # Use appropriate subprocess flags for Windows
            creationflags = 0
            if sys.platform.startswith("win"):
                creationflags = subprocess.CREATE_NO_WINDOW

            self.singbox_process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
            )

            if not wait_for_proxy(self.proxy_host, self.proxy_port):
                raise RuntimeError("Temporary sing-box proxy did not start in time.")

            return self
        except FileNotFoundError:
            error_msg = f"{singbox_executable} not found. Please ensure it's in the correct directory."
            print(f"ERROR: {error_msg}")
            show_error_message("Error", error_msg)
            raise
        except Exception as e:
            print(f"Error starting temporary sing-box instance: {e}")
            show_error_message("Error", f"Failed to start temporary sing-box: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.singbox_process:
            self.singbox_process.kill()
            self.singbox_process.wait()  # Ensure process is terminated
        if self.temp_config_file and os.path.exists(self.temp_config_file):
            try:
                os.remove(self.temp_config_file)
            except OSError as e:
                print(
                    f"WARNING: Could not remove temporary config file {self.temp_config_file}: {e}"
                )


def run_single_url_test(config, settings={}):
    """Runs a URL test for a single server configuration using a temporary config file."""
    try:
        full_config = config_generator.generate_config_json(config, settings)
        with TemporarySingboxInstance(full_config, PROXY_HOST, PROXY_PORT):
            return url_test(PROXY_SERVER_ADDRESS)
    except RuntimeError as e:
        print(f"ERROR: {e}")
        show_error_message("Error", str(e))
        return -1
    except Exception as e:
        print(f"Error in run_single_url_test: {type(e).__name__}: {e}")
        show_error_message(
            "Error", f"An unexpected error occurred during URL test: {e}"
        )
        return -1
