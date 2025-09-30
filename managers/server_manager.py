import base64
import binascii
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Any, Protocol

import requests

import link_parser
import settings_manager
from constants import (
    LogLevel,
    MAX_CONCURRENT_TESTS,
    HEALTH_CHECK_INTERVAL,
    TEST_ENDPOINTS,
)

# Removed unused import: constants
from managers.singbox_generator import SingboxConfigGenerator
from managers.xray_generator import XrayConfigGenerator
from managers.test_core_manager import TestCoreManager
from services.health_checker import HealthChecker
from services.ping_service import proxy_tcp_connect, url_latency_via_proxy


# --- Callback Protocol ---
class ServerManagerCallbacks(Protocol):
    def log(self, message: str, level: LogLevel = LogLevel.INFO) -> None: ...
    def on_servers_loaded(self) -> None: ...
    def on_servers_updated(self) -> None: ...
    def on_ping_result(
        self, server: Dict[str, Any], ping_result: int, test_type: str
    ) -> None: ...

    def on_ping_started(self, config: Dict[str, Any]) -> None: ...
    def on_update_start(self) -> None: ...
    def on_update_finish(self, errors: Optional[List[Exception]] = None) -> None: ...

    def request_save(self) -> None: ...
    def show_warning(self, title: str, message: str) -> None: ...
    def show_info(self, title: str, message: str) -> None: ...
    def show_error(self, title: str, message: str) -> None: ...


# --- Core Generator Factory ---
CORE_GENERATORS = {
    "sing-box": SingboxConfigGenerator,
    "Xray": XrayConfigGenerator,
}


def get_core_generator(core_name: str):
    """Factory function to get a config generator instance based on core name."""
    generator_class = CORE_GENERATORS.get(core_name)
    if generator_class:
        return generator_class()
    # Fallback to default generator if the requested one is not found
    return SingboxConfigGenerator()


class ServerManager:
    def __init__(self, settings: Dict[str, Any], callbacks: ServerManagerCallbacks):
        self.settings = settings
        self.callbacks = callbacks
        self.server_groups: Dict[str, List[Dict[str, Any]]] = {}
        # Use a single ThreadPoolExecutor for all background tasks
        self.thread_pool = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_TESTS)
        self._cancel_event = threading.Event()
        self.is_testing = False
        self._test_lock = threading.Lock()
        self._server_lock = threading.Lock()
        # Persistent test core manager (initialized lazily on first use)
        self._test_core_manager = None
        # Health checker for periodic testing
        self._health_checker = HealthChecker(settings, self.log)
        self._health_checker.set_test_callback(self._on_health_check_result)

    def shutdown(self):
        """Shuts down the thread pool. Should be called on application exit."""
        self.log("Shutting down server manager thread pool.", LogLevel.DEBUG)
        self._health_checker.stop()
        self.thread_pool.shutdown(wait=False)

    # --- Logging ---
    def log(self, message: str, level: LogLevel = LogLevel.INFO) -> None:
        self.callbacks.get("log", lambda msg, lvl: None)(message, level)

    # --- Settings Management ---
    def save_settings_to_disk(self) -> None:
        """Saves the current settings dictionary to the settings file on disk."""
        self.log("Debounced save: writing settings to disk.", LogLevel.DEBUG)
        settings_manager.save_settings(
            self.settings, self.callbacks.get("log", lambda msg, lvl: None)
        )

    def save_settings(self) -> None:
        """Requests a save of the settings. The UI will handle debouncing."""
        self.callbacks.get("request_save", lambda: None)()

    def force_save_settings(self) -> None:
        """Saves settings to disk immediately. Called on application exit."""
        self.log("Force saving settings on exit.", LogLevel.DEBUG)
        self.save_settings_to_disk()

    # --- Server Data Management ---
    def load_servers(self) -> None:
        """Loads servers from settings and migrates old configs by adding unique IDs if missing."""
        self.server_groups = self.settings.get("servers", {})

        settings_modified = False
        if self.server_groups:
            self.log("Checking server configurations for unique IDs...", LogLevel.DEBUG)
            for _, server_list in self.server_groups.items():
                for server_config in server_list:
                    if "id" not in server_config or not server_config.get("id"):
                        server_config["id"] = str(uuid.uuid4())
                        settings_modified = True

        if settings_modified:
            self.log(
                "Migrating old server configs by adding unique IDs.", LogLevel.INFO
            )
            self.save_settings()  # This will now be a debounced save

        self.log("Saved servers loaded successfully.", LogLevel.SUCCESS)
        self.callbacks.get("on_servers_loaded", lambda: None)()

    def get_groups(self) -> List[str]:
        return list(self.server_groups.keys())

    def get_servers_by_group(self, group_name: str) -> List[Dict[str, Any]]:
        return self.server_groups.get(group_name, [])

    def get_all_servers(self) -> List[Dict[str, Any]]:
        """Returns a flat list of all server configurations from all groups."""
        all_servers = []
        for server_list in self.server_groups.values():
            all_servers.extend(server_list)
        return all_servers

    # --- Server Actions ---
    def add_manual_server(
        self,
        server_link: str,
        group_name: Optional[str] = None,
        update_ui: bool = True,
        callbacks: Optional[ServerManagerCallbacks] = None,
    ) -> bool:
        config: Optional[Dict[str, Any]] = link_parser.parse_server_link(server_link)
        if not config:
            self.log(f"Failed to parse server link: {server_link}", LogLevel.ERROR)
            return False

        with self._server_lock:
            # Generate unique ID for the server
            if "id" not in config or not config.get("id"):
                config["id"] = str(uuid.uuid4())

            # Check for duplicates based on content, not just ID
            if self._is_duplicate_server(
                config, group_name or config.get("group", "Manual Servers")
            ):
                # Use callback if available (from subscription update), otherwise log directly
                if callbacks:
                    callbacks.show_warning(
                        "Duplicate Server",
                        f"Server with same configuration already exists. Skipping '{config.get('name')}'.",
                    )
                else:
                    self.log(
                        f"Server with same configuration already exists. Skipping '{config.get('name')}'.",
                        LogLevel.WARNING,
                    )
                return False

            # Use provided group_name, else fallback to parsed group, else default
            final_group_name: str = group_name or config.get("group", "Manual Servers")
            # Ensure the config itself has the correct group
            config["group"] = final_group_name

            if final_group_name not in self.server_groups:
                self.server_groups[final_group_name] = []

            self.server_groups[final_group_name].append(config)
            self.log(
                f"Added server '{config.get('name')}' to group '{final_group_name}'.",
                LogLevel.SUCCESS,
            )

            # Auto-start health check if enabled
            if self.settings.get("health_check_auto_start", False):
                self.start_health_check(final_group_name, ["tcp", "url"])

        return True

    def delete_group(self, group_name: str) -> None:
        if group_name in self.server_groups:
            del self.server_groups[group_name]
            self.log(f"Deleted group: {group_name}", LogLevel.INFO)
            self.callbacks.get("on_servers_loaded", lambda: None)()
        else:
            self.log(f"Could not find group '{group_name}' to delete.", LogLevel.ERROR)

    def delete_server(self, config_to_delete: Dict[str, Any]) -> None:
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

        if len(self.server_groups[group_name]) < initial_len:
            self.log(f"Deleted server: {config_to_delete.get('name')}", LogLevel.INFO)
            if not self.server_groups[group_name]:
                del self.server_groups[group_name]
                self.log(f"Removed empty group: {group_name}", LogLevel.INFO)
        else:
            self.log(
                f"Error: Could not find server {config_to_delete.get('name')} to delete.",
                LogLevel.ERROR,
            )

    def get_server_link(self, config: Dict[str, Any]) -> Optional[str]:
        return link_parser.generate_server_link(config)

    def _get_server_fingerprint(self, config: Dict[str, Any]) -> str:
        """Generate a unique fingerprint for a server based on its content."""
        # Create a fingerprint based on server properties that should be unique
        key_props = [
            config.get("server", ""),
            str(config.get("port", "")),
            config.get("protocol", ""),
            config.get("uuid", ""),
            config.get("password", ""),
            config.get("sni", ""),
            config.get("transport", ""),
            config.get("ws_path", ""),
            config.get("flow", ""),
            config.get("fp", ""),
        ]
        return "|".join(key_props)

    def _is_duplicate_server(self, config: Dict[str, Any], group_name: str) -> bool:
        """Check if a server is a duplicate based on content, not just ID."""
        new_fingerprint = self._get_server_fingerprint(config)

        # Check all groups for duplicates
        for grp, servers in self.server_groups.items():
            for existing_server in servers:
                if self._get_server_fingerprint(existing_server) == new_fingerprint:
                    return True
        return False

    def remove_duplicate_servers(self) -> int:
        """Remove duplicate servers based on content fingerprint. Returns count of removed duplicates."""
        removed_count = 0
        seen_fingerprints = set()

        with self._server_lock:
            for group_name, servers in self.server_groups.items():
                # Process servers in reverse order to avoid index issues when removing
                for i in range(len(servers) - 1, -1, -1):
                    server = servers[i]
                    fingerprint = self._get_server_fingerprint(server)

                    if fingerprint in seen_fingerprints:
                        # This is a duplicate, remove it
                        removed_count += 1
                        self.log(
                            f"Removing duplicate server: {server.get('name', 'Unknown')} from group '{group_name}'",
                            LogLevel.INFO,
                        )
                        servers.pop(i)
                    else:
                        seen_fingerprints.add(fingerprint)

        if removed_count > 0:
            self.log(f"Removed {removed_count} duplicate server(s)", LogLevel.SUCCESS)
            self.save_settings()
            self.callbacks.get("on_servers_updated", lambda: None)()

        return removed_count

    # --- Subscription Update ---
    def update_subscriptions(
        self,
        subscriptions: List[Dict[str, Any]],
        callbacks: Optional[ServerManagerCallbacks] = None,
    ) -> None:
        self.callbacks.get("on_update_start", lambda: None)()
        # Submit the main task to the thread pool
        self.thread_pool.submit(
            self._update_subscriptions_task, subscriptions, callbacks or self.callbacks
        )

    def _fetch_and_process_subscription(
        self, sub: Dict[str, Any], callbacks: ServerManagerCallbacks
    ) -> tuple[int, Optional[Exception]]:
        """Fetches and processes a single subscription."""
        sub_name = sub.get("name")
        sub_url = sub.get("url")
        if not sub_url:
            callbacks.show_warning(
                "Missing URL", f"Subscription '{sub_name}' has no URL, skipping."
            )
            return 0, None

        callbacks.show_info(
            "Subscription Update", f"Updating subscription: {sub_name}..."
        )
        try:
            response = requests.get(sub_url, timeout=15)
            response.raise_for_status()

            try:
                decoded_content = base64.b64decode(response.content).decode("utf-8")
            except (binascii.Error, UnicodeDecodeError):
                decoded_content = response.text

            links = decoded_content.strip().splitlines()
            added_for_sub = 0
            for link in links:
                link = link.strip()
                if not link:
                    continue

                # Pass callbacks down to handle potential duplicate server warnings safely
                if self.add_manual_server(
                    link, group_name=sub_name, update_ui=True, callbacks=callbacks
                ):
                    added_for_sub += 1

            if added_for_sub > 0:
                callbacks.show_info(
                    "Subscription Update",
                    f"Added {added_for_sub} new server(s) from subscription '{sub_name}'.",
                )
            else:
                callbacks.show_info(
                    "Subscription Update",
                    f"No new servers found for subscription '{sub_name}'.",
                )

            return added_for_sub, None

        except requests.exceptions.RequestException as e:
            callbacks.show_error(
                f"Update Failed for '{sub_name}'",
                f"Could not fetch subscription data: {e}",
            )
            return 0, e

    def _update_subscriptions_task(
        self, subscriptions: List[Dict[str, Any]], callbacks: ServerManagerCallbacks
    ) -> None:
        """Task to update multiple subscriptions in parallel."""
        errors: List[Exception] = []

        future_to_sub = {
            self.thread_pool.submit(
                self._fetch_and_process_subscription, sub, callbacks
            ): sub
            for sub in subscriptions
        }

        for future in as_completed(future_to_sub):
            sub_name = future_to_sub[future].get("name")
            try:
                _, error = future.result()
                if error:
                    errors.append(error)
            except Exception as exc:
                callbacks.show_error(
                    f"Error processing '{sub_name}'",
                    f"An unexpected error occurred: {exc}",
                )
                errors.append(exc)

        self.save_settings()  # Save all newly added servers to settings
        self.log("Subscription update finished.")
        self.callbacks.get("on_servers_updated", lambda: None)()
        self.callbacks.get("on_update_finish", lambda x: None)(
            errors if errors else None
        )

    # --- Ping & URL Tests ---

    # --- Health Check Methods ---

    def _on_health_check_result(
        self, server: Dict[str, Any], ping_result: int, test_type: str
    ) -> None:
        """Callback for health check results."""
        if self._cancel_event.is_set():
            return

        # Update server data
        if test_type == "tcp":
            server["tcp_ping"] = ping_result
        elif test_type == "url":
            server["url_ping"] = ping_result

        server["ping"] = ping_result  # Keep for sorting

        # Notify UI
        self.callbacks.get("on_ping_result", lambda s, p, t: None)(
            server, ping_result, test_type
        )

    def start_health_check(
        self, group_name: Optional[str] = None, test_types: Optional[List[str]] = None
    ) -> None:
        """Start periodic health checking for servers."""
        if group_name:
            servers = self.server_groups.get(group_name, [])
        else:
            # Get all servers from all groups
            servers = []
            for group_servers in self.server_groups.values():
                servers.extend(group_servers)

        if not servers:
            self.log("No servers to health check", LogLevel.WARNING)
            return

        # Set up test core manager for health checker
        if self._test_core_manager is None:
            active_core_name = self.settings.get("active_core", "sing-box")
            generator = get_core_generator(active_core_name)
            self._test_core_manager = TestCoreManager(
                self.settings, self.log, generator
            )

        self._health_checker.set_test_core_manager(self._test_core_manager)
        self._health_checker.set_progress_callback(self._on_health_check_progress)
        self._health_checker.start(servers, test_types or [], HEALTH_CHECK_INTERVAL)
        self.log(f"Started health checking for {len(servers)} servers", LogLevel.INFO)

    def stop_health_check(self) -> None:
        """Stop periodic health checking."""
        self._health_checker.stop()
        self.log("Stopped health checking", LogLevel.INFO)

    def _on_health_check_progress(self, current: int, total: int):
        """Callback for health check progress updates."""
        self.callbacks.get("on_health_check_progress", lambda c, t: None)(
            current, total
        )

    def test_all_urls(self, servers: List[dict]) -> None:
        """Test URL latency for specific servers."""
        if not servers:
            return

        self.log(f"Starting URL test for {len(servers)} servers", LogLevel.INFO)

        # Use persistent test core manager
        if self._test_core_manager is None:
            active_core_name = self.settings.get("active_core", "sing-box")
            generator = get_core_generator(active_core_name)
            self._test_core_manager = TestCoreManager(
                self.settings, self.log, generator
            )

        if self._test_core_manager.start(servers):
            # Test each server
            for server in servers:
                if self._cancel_event.is_set():
                    break

                server_id = server.get("id")
                if not server_id:
                    continue

                proxy_address = self._test_core_manager.get_proxy_address(server_id)
                if proxy_address:
                    result = url_latency_via_proxy(proxy_address)
                    self._process_ping_result(server, result, "url")
                else:
                    self.log(
                        f"No proxy address for server {server.get('name')}",
                        LogLevel.WARNING,
                    )

            self._test_core_manager.stop()
        else:
            self.log("Failed to start test core", LogLevel.ERROR)

    def test_all_tcp(self, servers: List[dict]) -> None:
        """Test TCP latency for specific servers."""
        if not servers:
            return

        self.log(f"Starting TCP test for {len(servers)} servers", LogLevel.INFO)

        # Use persistent test core manager
        if self._test_core_manager is None:
            active_core_name = self.settings.get("active_core", "sing-box")
            generator = get_core_generator(active_core_name)
            self._test_core_manager = TestCoreManager(
                self.settings, self.log, generator
            )

        if self._test_core_manager.start(servers):
            # Test each server
            for server in servers:
                if self._cancel_event.is_set():
                    break

                server_id = server.get("id")
                if not server_id:
                    continue

                proxy_address = self._test_core_manager.get_proxy_address(server_id)
                if proxy_address:
                    tcp_config = TEST_ENDPOINTS["tcp"]
                    result = proxy_tcp_connect(
                        proxy_address, tcp_config["host"], tcp_config["port"]
                    )
                    self._process_ping_result(server, result, "tcp")
                else:
                    self.log(
                        f"No proxy address for server {server.get('name')}",
                        LogLevel.WARNING,
                    )

            self._test_core_manager.stop()
        else:
            self.log("Failed to start test core", LogLevel.ERROR)

    def _process_ping_result(
        self, server: dict, ping_result: int, test_type: str
    ) -> None:
        """Process ping result and update UI."""
        server_id = server.get("id")
        if not server_id:
            return

        # Update server data
        if test_type == "tcp":
            server["tcp_ping"] = ping_result
        elif test_type == "url":
            server["url_ping"] = ping_result

        server["ping"] = ping_result  # Keep for sorting

        # Notify UI
        self.callbacks.get("on_ping_result", lambda s, p, t: None)(
            server, ping_result, test_type
        )
