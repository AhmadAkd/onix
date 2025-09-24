import subprocess
import os
import time
import json
import threading
import tempfile

import utils
import network_tester
import system_proxy
import config_generator
from constants import (
    PROXY_SERVER_ADDRESS,
    LogLevel,
    CONNECTION_STOP_DELAY,
    CONNECTION_CHECK_DELAY,
)


class SingboxManager:
    def __init__(self, settings, callbacks):
        self.settings = settings
        self.callbacks = callbacks
        self.singbox_process = None
        self.is_running = False

    def start(self, config):
        if (
            self.is_running
            and self.singbox_process
            and self.singbox_process.poll() is None
        ):
            self.log(
                "Switching servers... Stopping previous connection first.",
                LogLevel.INFO,
            )
            self.stop()
            time.sleep(CONNECTION_STOP_DELAY)

        self.log("Starting connection...", LogLevel.INFO)
        self.callbacks.get("on_status_change", lambda s, c: None)(
            "Connecting...", "yellow"
        )

        thread = threading.Thread(target=self._run_and_log, args=(config,), daemon=True)
        thread.start()

        self.callbacks.get("schedule", lambda t, c: None)(
            CONNECTION_CHECK_DELAY, self.check_connection
        )

    def _run_and_log(self, config):
        config_filename = None
        try:
            full_config = config_generator.generate_config_json(config, self.settings)
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".json", encoding="utf-8"
            ) as f:
                json.dump(full_config, f, indent=2)
                config_filename = f.name

            self.log("Validating configuration...", LogLevel.INFO)
            check_command = [
                utils.get_resource_path("sing-box.exe"),
                "check",
                "-c",
                config_filename,
            ]
            result = subprocess.run(
                check_command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            if result.returncode != 0:
                error_message = result.stdout.strip() or result.stderr.strip()
                self.log(
                    f"Configuration check failed! Error: {error_message}",
                    LogLevel.ERROR,
                )
                self.callbacks.get("schedule", lambda t, c: None)(0, self.stop)
                return

            self.log("Configuration is valid. Starting process...", LogLevel.INFO)
            command = [
                utils.get_resource_path("sing-box.exe"),
                "run",
                "-c",
                config_filename,
            ]
            self.singbox_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            self.is_running = True

            for line in iter(self.singbox_process.stdout.readline, ""):
                self.log(line.strip(), LogLevel.DEBUG)

        except FileNotFoundError:
            self.log(
                f"Error: sing-box.exe not found at '{utils.get_resource_path('sing-box.exe')}'!",
                LogLevel.ERROR,
            )
        except Exception as e:
            self.log(
                f"An unexpected error occurred during sing-box execution: {type(e).__name__}: {e}",
                LogLevel.ERROR,
            )
        finally:
            if self.is_running:
                self.is_running = False
                self.callbacks.get("on_stop", lambda: None)()
            if config_filename and os.path.exists(config_filename):
                try:
                    os.remove(config_filename)
                except OSError:
                    pass

    def stop(self):
        if not self.is_running and not self.singbox_process:
            return

        process_to_kill = self.singbox_process
        self.is_running = False
        self.singbox_process = None

        if process_to_kill and process_to_kill.poll() is None:
            try:
                process_to_kill.kill()
                self.log("Sing-box process terminated.")
            except Exception as e:
                self.log(
                    f"Failed to terminate sing-box process: {type(e).__name__}: {e}",
                    LogLevel.ERROR,
                )

        system_proxy.set_system_proxy(False, self.settings, self.log)
        self.callbacks.get("on_stop", lambda: None)()

    def check_connection(self):
        result = network_tester.url_test(PROXY_SERVER_ADDRESS)
        if result != -1:
            self.log(f"Connection successful! Latency: {result} ms.")
            system_proxy.set_system_proxy(True, self.settings, self.log)
            self.callbacks.get("on_connect", lambda r: None)(result)

            ip_thread = threading.Thread(target=self._fetch_ip_and_update, daemon=True)
            ip_thread.start()
        else:
            self.log("Error: Connection test failed. Check server config.")
            self.callbacks.get("on_status_change", lambda s, c: None)(
                "Connection Failed", "red"
            )
            self.stop()

    def _fetch_ip_and_update(self):
        ip_address = network_tester.get_external_ip(PROXY_SERVER_ADDRESS)
        self.callbacks.get("on_ip_update", lambda ip: None)(ip_address)

    def log(self, message, level=LogLevel.INFO):
        self.callbacks.get("log", lambda msg, lvl: None)(message, level)
