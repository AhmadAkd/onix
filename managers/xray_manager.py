import subprocess
import os
import time
import json
import threading
import tempfile
from typing import Dict, Any, Protocol

import utils
import network_tester
import system_proxy
from managers.core_manager import CoreManager
from managers.xray_generator import XrayConfigGenerator
from constants import (
    PROXY_SERVER_ADDRESS,
    LogLevel,
    CONNECTION_STOP_DELAY,
    CONNECTION_CHECK_DELAY,
    XRAY_EXECUTABLE_NAMES,
    XRAY_LOG_FILE,
)


# --- Callback Protocol ---
class XrayManagerCallbacks(Protocol):
    def log(self, message: str, level: LogLevel = LogLevel.INFO) -> None: ...
    def on_status_change(self, status: str, color: str) -> None: ...
    def on_connect(self, result: int) -> None: ...
    def on_stop(self) -> None: ...
    def on_ip_update(self, ip_address: str) -> None: ...


class XrayManager(CoreManager):
    def __init__(self, settings: Dict[str, Any], callbacks: XrayManagerCallbacks):
        super().__init__(settings, callbacks)
        self.config_generator = XrayConfigGenerator()

    def start(self, config: Dict[str, Any]) -> None:
        if self.is_running and self.process and self.process.poll() is None:
            self.log(
                "Switching servers... Stopping previous connection first.", LogLevel.INFO)
            self.stop()
            time.sleep(CONNECTION_STOP_DELAY)

        self.log("Starting Xray connection...", LogLevel.INFO)
        self.callbacks.on_status_change("Connecting...", "yellow")

        thread = threading.Thread(
            target=self._run_and_log, args=(config,), daemon=True)
        thread.start()

        # Schedule connection check
        check_connection_timer = threading.Timer(
            CONNECTION_CHECK_DELAY / 1000.0, self.check_connection)
        check_connection_timer.start()

    def _run_and_log(self, config: Dict[str, Any]) -> None:
        config_filename = None
        try:
            full_config = self.config_generator.generate_config_json(
                config, self.settings)
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json", encoding="utf-8") as f:
                json.dump(full_config, f, indent=2)
                config_filename = f.name

            self.log(
                "Xray configuration generated. Starting process...", LogLevel.INFO)

            os_key = "windows" if os.name == "nt" else os.name.lower()
            executable_name = XRAY_EXECUTABLE_NAMES.get(os_key, "xray")
            executable_path = utils.get_resource_path(executable_name)

            command = [executable_path, "run", "-c", config_filename]

            creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                creationflags=creation_flags,
                cwd=os.getcwd(),
            )
            self.is_running = True

            with open(XRAY_LOG_FILE, "a", encoding="utf-8") as log_file:
                if self.process.stdout is not None:
                    for line in iter(self.process.stdout.readline, ""):
                        self.log(line.strip(), LogLevel.DEBUG)
                        log_file.write(line)
                        log_file.flush()

        except FileNotFoundError:
            # Use default values if variables are not defined
            exec_name = executable_name if 'executable_name' in locals() else "xray"
            exec_path = executable_path if 'executable_path' in locals() else "xray"
            self.log(
                f"Error: {exec_name} not found at '{exec_path}'!", LogLevel.ERROR)
            self.stop()
        except Exception as e:
            self.log(
                f"An unexpected error occurred during Xray execution: {e}", LogLevel.ERROR)
            self.stop()
        finally:
            if self.is_running:
                self.is_running = False
                self.callbacks.on_stop()
            if config_filename and os.path.exists(config_filename):
                try:
                    os.remove(config_filename)
                except OSError as e:
                    self.log(
                        f"Warning: Could not remove temp config file {config_filename}: {e}", LogLevel.WARNING)

    def stop(self) -> None:
        if not self.is_running and not self.process:
            return

        if self.process and self.process.poll() is None:
            self.process.kill()
            self.log("Xray process terminated.")

        self.is_running = False
        self.process = None
        system_proxy.set_system_proxy(False, self.settings, self.log)
        self.callbacks.on_stop()

    def check_connection(self) -> None:
        result = network_tester.url_test(PROXY_SERVER_ADDRESS)
        if result != -1:
            self.log(
                f"Connection successful! Latency: {result} ms.", LogLevel.SUCCESS)
            system_proxy.set_system_proxy(True, self.settings, self.log)
            self.callbacks.on_connect(result)
            ip_address = network_tester.get_external_ip(PROXY_SERVER_ADDRESS)
            self.callbacks.on_ip_update(ip_address)
        else:
            self.log(
                "Error: Connection test failed. Check server config.", LogLevel.ERROR)
            self.callbacks.on_status_change("Connection Failed", "red")
            self.stop()
