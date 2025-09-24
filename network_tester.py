import json
import os
import socket
import time
import requests
import subprocess
import tempfile

import utils
import config_generator
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


def run_single_url_test(config, settings={}):
    """Runs a URL test for a single server configuration using a temporary config file."""
    temp_proc = None
    temp_config_file = None
    try:
        full_config = config_generator.generate_config_json(config, settings)
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json", encoding="utf-8"
        ) as f:
            json.dump(full_config, f, indent=2)
            temp_config_file = f.name

        command = [
            utils.get_resource_path("sing-box.exe"),
            "run",
            "-c",
            temp_config_file,
        ]
        temp_proc = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        if wait_for_proxy(PROXY_HOST, PROXY_PORT):
            return url_test(PROXY_SERVER_ADDRESS)
        else:
            return -1
    except FileNotFoundError:
        error_msg = "sing-box.exe not found. Please ensure it's in the correct directory."
        print(f"ERROR: {error_msg}")
        show_error_message("Error", error_msg)
        return -1
    except OSError as e:
        error_msg = f"OS error when running sing-box: {e}"
        print(f"ERROR: {error_msg}")
        show_error_message("Error", error_msg)
        return -1
    except Exception as e: # Catch any other unexpected errors
        # Log the specific exception for debugging
        print(f"Error in run_single_url_test: {type(e).__name__}: {e}")
        show_error_message("Error", f"An unexpected error occurred during URL test: {e}")
        return -1
    finally:
        if temp_proc:
            temp_proc.kill()
        if temp_config_file and os.path.exists(temp_config_file):
            try:
                os.remove(temp_config_file)
            except OSError:
                pass