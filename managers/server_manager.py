import base64
import binascii
import threading
import requests
from concurrent.futures import ThreadPoolExecutor

import link_parser
import network_tester
from constants import LogLevel
import constants


class ServerManager:
    def __init__(self, settings, callbacks):
        self.settings = settings
        self.callbacks = callbacks
        self.server_groups = {}
        self.ping_executor = ThreadPoolExecutor(max_workers=20)
        self._cancel_event = threading.Event()
        self.is_testing = False

    # --- Logging ---
    def log(self, message, level=LogLevel.INFO):
        self.callbacks.get("log", lambda msg, lvl: None)(message, level)

    # --- Server Data Management ---
    def load_servers(self):
        self.server_groups = self.settings.get("servers", {})
        if self.server_groups:
            self.log("Saved servers loaded successfully.", LogLevel.SUCCESS)
        self.callbacks.get("on_servers_loaded", lambda: None)()

    def get_all_server_groups(self):
        return self.server_groups

    def get_groups(self):
        return list(self.server_groups.keys())

    def get_servers_by_group(self, group_name):
        return self.server_groups.get(group_name, [])

    # --- Server Actions ---
    def add_manual_server(self, server_link):
        config = link_parser.parse_server_link(server_link)
        if not config:
            self.log(f"Failed to parse server link: {server_link}", LogLevel.ERROR)
            return

        server_id = f"{config.get('server')}:{config.get('port')}"
        for group in self.server_groups.values():
            for s_config in group:
                if f"{s_config.get('server')}:{s_config.get('port')}" == server_id:
                    self.log(
                        f"Server {config.get('name')} already exists. Skipping.",
                        LogLevel.WARNING,
                    )
                    return

        group_name = config.get("group", "Manual Servers")
        if group_name not in self.server_groups:
            self.server_groups[group_name] = []

        self.server_groups[group_name].append(config)
        self.log(
            f"Added server '{config.get('name')}' to group '{group_name}'.",
            LogLevel.SUCCESS,
        )

        self.callbacks.get("on_servers_updated", lambda: None)()

    def add_wireguard_config(self, config_content, filename):
        config = link_parser.parse_wireguard_config(config_content, filename)
        if not config:
            self.log(f"Failed to parse WireGuard config: {filename}", LogLevel.ERROR)
            return

        # Use a unique identifier, e.g., based on public key
        server_id = config.get("public_key")
        for group in self.server_groups.values():
            for s_config in group:
                if s_config.get("public_key") == server_id:
                    self.log(
                        f"WireGuard config {config.get('name')} already exists. Skipping.",
                        LogLevel.WARNING,
                    )
                    return

        group_name = config.get("group", "WireGuard")
        if group_name not in self.server_groups:
            self.server_groups[group_name] = []

        self.server_groups[group_name].append(config)
        self.log(
            f"Added WireGuard config '{config.get('name')}' to group '{group_name}'.",
            LogLevel.SUCCESS,
        )

        self.callbacks.get("on_servers_updated", lambda: None)()

    def delete_server(self, config_to_delete):
        group_name = config_to_delete.get("group")
        if not group_name or group_name not in self.server_groups:
            self.log(
                f"Error: Could not find group for server {config_to_delete.get('name')}.",
                LogLevel.ERROR,
            )
            return

        initial_len = len(self.server_groups[group_name])
        self.server_groups[group_name] = [
            s for s in self.server_groups[group_name] if s != config_to_delete
        ]
        final_len = len(self.server_groups[group_name])

        if final_len < initial_len:
            self.log(f"Deleted server: {config_to_delete.get('name')}", LogLevel.INFO)
            if not self.server_groups[group_name]:
                del self.server_groups[group_name]
                self.log(f"Removed empty group: {group_name}", LogLevel.INFO)

            self.callbacks.get("on_servers_updated", lambda: None)()
        else:
            self.log(
                f"Error: Could not find server {config_to_delete.get('name')} to delete.",
                LogLevel.ERROR,
            )

    def edit_server(self, config_to_edit, new_name):
        old_name = config_to_edit["name"]
        config_to_edit["name"] = new_name
        self.log(f"Renamed server '{old_name}' to '{new_name}'.", LogLevel.INFO)
        self.callbacks.get("on_servers_updated", lambda: None)()

    def get_server_link(self, config):
        """Generates a server link from a server configuration dictionary."""
        return link_parser.generate_server_link(config)

    # --- Subscription Update ---
    def update_subscriptions(self, subscriptions):
        self.callbacks.get("on_update_start", lambda: None)()
        threading.Thread(
            target=self._update_subscriptions_task,
            args=(subscriptions,),
            daemon=True,
        ).start()

    def _update_subscriptions_task(self, subscriptions):
        from concurrent.futures import as_completed

        any_error = False

        enabled_subs = [sub for sub in subscriptions if sub.get("enabled", True)]
        if not enabled_subs:
            self.callbacks.get("schedule", lambda t, c: None)(
                0, lambda: self.callbacks.get("on_update_finish")(error=False)
            )
            return

        futures = {
            self.ping_executor.submit(
                self._update_single_subscription_task, sub["url"], sub["name"]
            ): sub
            for sub in enabled_subs
        }

        for future in as_completed(futures):
            sub = futures[future]
            try:
                self.callbacks.get("on_update_progress", lambda sub_name: None)(
                    sub["name"]
                )
                future.result()  # Raise exception if one occurred in the thread
            except Exception as e:
                self.log(
                    f"Failed to update subscription '{sub['name']}': {e}",
                    LogLevel.ERROR,
                )
                any_error = True

        self.callbacks.get("schedule", lambda t, c: None)(
            0, lambda: self.callbacks.get("on_update_finish")(error=any_error)
        )

    def _update_single_subscription_task(self, sub_link, custom_group_name):
        try:
            headers = {"User-Agent": constants.DEFAULT_USER_AGENT}
            response = requests.get(sub_link, headers=headers, timeout=10)
            response.raise_for_status()

            base64_text = response.text.strip()
            decoded_content = base64.b64decode(base64_text).decode("utf-8")
            server_links = decoded_content.splitlines()

            existing_server_ids = {
                f"{s_config.get('server')}:{s_config.get('port')}"
                for group in self.server_groups.values()
                for s_config in group
            }

            temp_groups = {}
            server_count = 0
            skipped_count = 0

            for link in server_links:
                config = link_parser.parse_server_link(link)
                if config:
                    server_id = f"{config.get('server')}:{config.get('port')}"
                    if server_id in existing_server_ids:
                        skipped_count += 1
                        continue

                    existing_server_ids.add(server_id)
                    server_count += 1
                    group_name = custom_group_name
                    if group_name not in temp_groups:
                        temp_groups[group_name] = []
                    config["group"] = group_name
                    temp_groups[group_name].append(config)

            self.server_groups.update(temp_groups)

            log_message = f"Finished processing '{custom_group_name}'. Added {server_count} new server(s)."
            if skipped_count > 0:
                log_message += f" Skipped {skipped_count} duplicate(s)."
            self.log(log_message, LogLevel.SUCCESS)

        except requests.exceptions.Timeout as e:
            raise Exception(f"Request timed out for {custom_group_name}") from e
        except requests.exceptions.HTTPError as e:
            raise Exception(
                f"Invalid response from server for {custom_group_name} ({e.response.status_code})"
            ) from e
        except requests.exceptions.RequestException as e:
            raise Exception(f"A network error occurred for {custom_group_name}") from e
        except (binascii.Error, UnicodeDecodeError) as e:
            raise Exception(
                f"Failed to decode subscription content for {custom_group_name}"
            ) from e
        except Exception as e:
            raise Exception(
                f"An unexpected error occurred for {custom_group_name}: {e}"
            ) from e

    # --- Ping & URL Tests ---
    def test_all_pings(self, servers_to_test):
        if self.is_testing:
            self.log("A test is already in progress.", LogLevel.WARNING)
            return
        self.is_testing = True
        self._cancel_event.clear()
        self.callbacks.get("on_testing_start", lambda: None)()
        self.log(
            f"Starting TCP ping for {len(servers_to_test)} servers...", LogLevel.INFO
        )

        futures = [
            self.ping_executor.submit(self._ping_task, config, is_url_test=False)
            for config in servers_to_test
        ]

        def wait_for_pings():
            try:
                from concurrent.futures import as_completed

                for future in as_completed(futures):
                    if self._cancel_event.is_set():
                        break
                    try:
                        future.result()
                    except Exception:
                        pass  # Ignore exceptions from individual pings
            finally:
                self.is_testing = False
                for f in futures:  # Cancel any remaining
                    f.cancel()
                if not self._cancel_event.is_set():
                    self.log("All ping tests finished.", LogLevel.INFO)
                self.callbacks.get("schedule", lambda t, c: None)(
                    0, self.callbacks.get("on_testing_finish")
                )

        threading.Thread(target=wait_for_pings, daemon=True).start()

    def test_all_urls(self, servers_to_test):
        if self.is_testing:
            self.log("A test is already in progress.", LogLevel.WARNING)
            return
        self.is_testing = True
        self._cancel_event.clear()
        self.callbacks.get("on_testing_start", lambda: None)()
        self.log("Starting URL test. This may take some time.", LogLevel.INFO)
        threading.Thread(
            target=self._sequential_url_test, args=(servers_to_test,), daemon=True
        ).start()

    def _sequential_url_test(self, servers):
        try:
            for config in servers:
                if self._cancel_event.is_set():
                    self.log("URL test cancelled.", LogLevel.INFO)
                    break
                self._ping_task(config, is_url_test=True)
                import time

                time.sleep(0.2)
        finally:
            self.is_testing = False
            if not self._cancel_event.is_set():
                self.log("URL testing finished.", LogLevel.INFO)
            self.callbacks.get("schedule", lambda t, c: None)(
                0, self.callbacks.get("on_testing_finish")
            )

    def _ping_task(self, config, is_url_test):
        if self._cancel_event.is_set():
            return

        if is_url_test:
            ping_result = network_tester.run_single_url_test(config, self.settings)
        else:
            ping_result = network_tester.tcp_ping(config["server"], config["port"])

        if self._cancel_event.is_set():
            return

        config["ping"] = ping_result
        self.callbacks.get("schedule", lambda t, c: None)(
            0,
            lambda: self.callbacks.get("on_ping_result")(
                config, ping_result, is_url_test
            ),
        )

    def cancel_tests(self):
        """Cancels any ongoing ping or URL tests."""
        if not self.is_testing:
            return
        self.log("Cancelling tests...", LogLevel.INFO)
        self._cancel_event.set()

    def sort_servers_by_ping(self, group_name):
        if group_name not in self.server_groups:
            return

        configs = self.server_groups.get(group_name, [])
        configs.sort(
            key=lambda c: c.get("ping", 9999) if c.get("ping", 9999) != -1 else 99999
        )

        self.log("Servers sorted by ping (fastest first).", LogLevel.INFO)
        self.callbacks.get("on_servers_updated", lambda: None)()
