import subprocess
import os
import requests
import time
import json
import threading
import tempfile

import utils
import network_tester
import system_proxy
import constants  # This was already present, but let's ensure it's correct.
from managers.core_manager import CoreManager
import config_generator
from constants import (
    PROXY_SERVER_ADDRESS,
    LogLevel,
    STATS_API_PORT,
    CONNECTION_STOP_DELAY,
    CONNECTION_CHECK_DELAY,
    SINGBOX_LOG_FILE,
)


class SingboxManager(CoreManager):
    def __init__(self, settings, callbacks):
        super().__init__(settings, callbacks)
        self.stats_thread = None
        self.stop_stats_thread = threading.Event()
        self.connection_check_timer = None

    def start(self, config):
        if self.is_running and self.process and self.process.poll() is None:
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

        thread = threading.Thread(
            target=self._run_and_log, args=(config,), daemon=True)
        thread.start()

        # Schedule connection check and store the timer reference
        self.connection_check_timer = threading.Timer(
            CONNECTION_CHECK_DELAY / 1000.0, self.check_connection)
        self.connection_check_timer.start()

    def _run_and_log(self, config):
        config_filename = None
        log_file = None
        try:
            full_config = config_generator.generate_config_json(
                config, self.settings)
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
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            self.is_running = True

            # Open the log file in append mode
            log_file = open(SINGBOX_LOG_FILE, "a", encoding="utf-8")

            for line in iter(self.process.stdout.readline, ""):
                self.log(line.strip(), LogLevel.DEBUG)
                log_file.write(line)

        except FileNotFoundError:
            self.log(
                f"Error: sing-box.exe not found at '{utils.get_resource_path('sing-box.exe')}'!",
                LogLevel.ERROR,
            )
        except Exception as e:
            self.log(
                f"An unexpected error occurred during sing-box execution: {type(e).__name__}: {e}",
                constants.LogLevel.ERROR,
            )
        finally:
            if self.is_running:
                self.is_running = False
                self.callbacks.get("on_stop", lambda: None)()
            if config_filename and os.path.exists(config_filename):
                if log_file:
                    log_file.close()
                try:
                    os.remove(config_filename)
                except OSError as e:
                    self.log(
                        f"Warning: Could not remove temp config file {config_filename}: {e}", LogLevel.WARNING)

    def stop(self):
        if not self.is_running and not self.process:
            return

        # Cancel connection check timer if it exists
        if self.connection_check_timer:
            self.connection_check_timer.cancel()
            self.connection_check_timer = None

        process_to_kill = self.process
        self.is_running = False
        self.process = None

        self.stop_stats_thread.set()

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
        # Only check connection if we're actually running
        if not self.is_running:
            return

        result = network_tester.url_test(PROXY_SERVER_ADDRESS)
        if result != -1:
            self.log(
                f"Connection successful! Latency: {result} ms.", LogLevel.SUCCESS)
            system_proxy.set_system_proxy(True, self.settings, self.log)
            self.callbacks.get("on_connect", lambda r: None)(result)

            ip_thread = threading.Thread(
                target=self._fetch_ip_and_update, daemon=True)
            ip_thread.start()

            self._start_stats_polling()
        else:
            self.log(
                "Error: Connection test failed. Check server config.", LogLevel.ERROR)
            self.callbacks.get("on_status_change", lambda s, c: None)(
                "Connection Failed", "red"
            )
            self.stop()

    def _fetch_ip_and_update(self):
        ip_address = network_tester.get_external_ip(PROXY_SERVER_ADDRESS)
        self.callbacks.get("on_ip_update", lambda ip: None)(ip_address)

    def _start_stats_polling(self):
        if self.stats_thread and self.stats_thread.is_alive():
            return

        self.stop_stats_thread.clear()
        self.stats_thread = threading.Thread(
            target=self._poll_stats, daemon=True)
        self.stats_thread.start()

    def _poll_stats(self):
        last_uplink = 0
        last_downlink = 0
        last_time = time.time()

        while not self.stop_stats_thread.is_set():
            try:
                response = requests.get(
                    f"http://127.0.0.1:{STATS_API_PORT}/stats")
                stats = response.json()
                current_uplink = stats.get("uplink_total", 0)
                current_downlink = stats.get("downlink_total", 0)
                current_time = time.time()

                time_delta = current_time - last_time
                if time_delta > 0:
                    up_speed = (current_uplink - last_uplink) / time_delta
                    down_speed = (current_downlink -
                                  last_downlink) / time_delta
                    self.callbacks.get("on_speed_update", lambda u, d: None)(
                        up_speed, down_speed)

                last_uplink = current_uplink
                last_downlink = current_downlink
                last_time = current_time

            except requests.exceptions.RequestException:
                # API might not be ready yet, or sing-box stopped.
                self.log("Stats API not ready yet or stopped.", LogLevel.DEBUG)
            except Exception as e:
                self.log(f"Error polling stats: {e}", LogLevel.ERROR)

            # Check for stop signal before sleeping
            if self.stop_stats_thread.is_set():
                break

            time.sleep(1)

    def log(self, message, level=LogLevel.INFO):
        self.callbacks.get("log", lambda msg, lvl: None)(message, level)
