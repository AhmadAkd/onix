import json
import os
import subprocess
import sys
import tempfile
import time

import utils
from constants import (
    LogLevel,
    PROXY_HOST,
    SINGBOX_EXECUTABLE_NAMES,
    XRAY_EXECUTABLE_NAMES,
    WAIT_FOR_PROXY_TIMEOUT,
    WAIT_FOR_PROXY_INTERVAL,
)


def _wait_for_port(host, port, timeout=WAIT_FOR_PROXY_TIMEOUT):
    import socket

    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=WAIT_FOR_PROXY_INTERVAL):
                return True
        except OSError:
            time.sleep(WAIT_FOR_PROXY_INTERVAL)
    return False


class TestCoreManager:
    """Keeps a single core process alive with multiple HTTP inbounds for testing."""

    def __init__(self, settings, log_callback, config_generator):
        self.settings = settings
        self.log = log_callback
        self.config_generator = config_generator
        self.process = None
        self.temp_config_file = None
        self.server_ports = {}
        self.active_core = self.settings.get("active_core", "sing-box")

    def is_running(self):
        return self.process is not None and self.process.poll() is None

    def start(self, servers):
        if self.is_running():
            return True

        try:
            # Map server IDs to deterministic ports
            self.server_ports.clear()
            for i, server in enumerate(servers):
                self.server_ports[server.get("id")] = 11000 + i

            # Build test config with HTTP inbounds per server
            test_config = self.config_generator.generate_test_config(
                servers, self.settings)

            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json", encoding="utf-8") as f:
                json.dump(test_config, f, indent=2)
                self.temp_config_file = f.name

            os_key = "windows" if sys.platform.startswith(
                "win") else sys.platform.lower()
            if self.active_core == "sing-box":
                executable_name = SINGBOX_EXECUTABLE_NAMES.get(
                    os_key, "sing-box")
            else:
                executable_name = XRAY_EXECUTABLE_NAMES.get(os_key, "xray")
            executable_path = utils.get_resource_path(executable_name)

            command = [executable_path, "run", "-c", self.temp_config_file]
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith(
                "win") else 0
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                creationflags=creationflags,
            )

            # Wait for first inbound
            first_port = 11000
            if not _wait_for_port(PROXY_HOST, first_port):
                # Try read errors if exited
                if self.process.poll() is not None:
                    try:
                        out, err = self.process.communicate(timeout=1)
                    except subprocess.TimeoutExpired:
                        out, err = "", ""
                    msg = (
                        err or out or f"Core exited with code {self.process.returncode}").strip()
                    self.log(
                        f"Test core failed to start: {msg}", LogLevel.ERROR)
                else:
                    self.log("Test core did not become ready in time.",
                             LogLevel.ERROR)
                self.stop()
                return False

            self.log(
                f"Test core started with {self.active_core} for {len(servers)} servers.", LogLevel.DEBUG)
            return True
        except Exception as e:
            self.log(f"Error starting test core: {e}", LogLevel.ERROR)
            self.stop()
            return False

    def stop(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
        self.process = None
        if self.temp_config_file and os.path.exists(self.temp_config_file):
            try:
                os.remove(self.temp_config_file)
            except OSError:
                pass
        self.temp_config_file = None

    def get_proxy_address(self, server_id):
        port = self.server_ports.get(server_id)
        if not port:
            return None
        return f"{PROXY_HOST}:{port}"
