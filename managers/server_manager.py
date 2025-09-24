import base64
import json
import threading
import requests
from concurrent.futures import ThreadPoolExecutor

import link_parser
import network_tester
from constants import LogLevel, NA

class ServerManager:
    def __init__(self, settings, callbacks):
        self.settings = settings
        self.callbacks = callbacks
        self.server_groups = {}
        self.ping_executor = ThreadPoolExecutor(max_workers=20)

    # --- Logging ---
    def log(self, message, level=LogLevel.INFO):
        self.callbacks.get('log', lambda msg, lvl: None)(message, level)

    # --- Server Data Management ---
    def load_servers(self):
        self.server_groups = self.settings.get("servers", {})
        if self.server_groups:
            self.log("Saved servers loaded successfully.", LogLevel.SUCCESS)
        self.callbacks.get('on_servers_loaded', lambda: None)()

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
                    self.log(f"Server {config.get('name')} already exists. Skipping.", LogLevel.WARNING)
                    return

        group_name = config.get("group", "Manual Servers")
        if group_name not in self.server_groups:
            self.server_groups[group_name] = []

        self.server_groups[group_name].append(config)
        self.log(f"Added server '{config.get('name')}' to group '{group_name}'.", LogLevel.SUCCESS)
        
        self.callbacks.get('on_servers_updated', lambda: None)()

    def delete_server(self, config_to_delete):
        group_name = config_to_delete.get("group")
        if not group_name or group_name not in self.server_groups:
            self.log(f"Error: Could not find group for server {config_to_delete.get('name')}.", LogLevel.ERROR)
            return

        initial_len = len(self.server_groups[group_name])
        self.server_groups[group_name] = [s for s in self.server_groups[group_name] if s != config_to_delete]
        final_len = len(self.server_groups[group_name])

        if final_len < initial_len:
            self.log(f"Deleted server: {config_to_delete.get('name')}", LogLevel.INFO)
            if not self.server_groups[group_name]:
                del self.server_groups[group_name]
                self.log(f"Removed empty group: {group_name}", LogLevel.INFO)
            
            self.callbacks.get('on_servers_updated', lambda: None)()
        else:
            self.log(f"Error: Could not find server {config_to_delete.get('name')} to delete.", LogLevel.ERROR)

    def edit_server(self, config_to_edit, new_name):
        old_name = config_to_edit['name']
        config_to_edit['name'] = new_name
        self.log(f"Renamed server '{old_name}' to '{new_name}'.", LogLevel.INFO)
        self.callbacks.get('on_servers_updated', lambda: None)()

    # --- Subscription Update ---
    def update_subscription(self, sub_link, custom_group_name):
        self.callbacks.get('on_update_start', lambda: None)()
        threading.Thread(target=self._update_subscription_task, args=(sub_link, custom_group_name), daemon=True).start()

    def _update_subscription_task(self, sub_link, custom_group_name):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(sub_link, headers=headers, timeout=10)
            response.raise_for_status()

            base64_text = response.text.strip()
            decoded_content = base64.b64decode(base64_text).decode('utf-8')
            server_links = decoded_content.splitlines()

            existing_server_ids = {
                f"{s_config.get('server')}:{s_config.get('port')}"
                for group in self.server_groups.values() for s_config in group
            }

            temp_groups = {}
            server_count = 0
            skipped_count = 0

            for link in server_links:
                config = utils.parse_server_link(link)
                if config:
                    server_id = f"{config.get('server')}:{config.get('port')}"
                    if server_id in existing_server_ids:
                        skipped_count += 1
                        continue
                    
                    existing_server_ids.add(server_id)
                    server_count += 1
                    group_name = custom_group_name if custom_group_name else config["group"]
                    if group_name not in temp_groups:
                        temp_groups[group_name] = []
                    config["group"] = group_name
                    temp_groups[group_name].append(config)

            self.server_groups.update(temp_groups)
            
            log_message = f"Successfully loaded {server_count} new servers."
            if skipped_count > 0:
                log_message += f" Skipped {skipped_count} duplicate(s)."
            self.log(log_message, LogLevel.SUCCESS)
            
            self.callbacks.get('schedule', lambda t, c: None)(0, self.callbacks.get('on_update_finish'))

        except Exception as e:
            self.log(f"Failed to update subscription: {e}", LogLevel.ERROR)
            self.callbacks.get('schedule', lambda t, c: None)(0, lambda: self.callbacks.get('on_update_finish')(error=True))

    # --- Ping & URL Tests ---
    def test_all_pings(self, servers_to_test):
        self.log(f"Starting TCP ping for {len(servers_to_test)} servers...", LogLevel.INFO)
        for config in servers_to_test:
            self.ping_executor.submit(self._ping_task, config, is_url_test=False)

    def test_all_urls(self, servers_to_test):
        self.log("Starting URL test. This may take some time.", LogLevel.INFO)
        # Run URL tests sequentially to avoid overwhelming the system
        threading.Thread(target=self._sequential_url_test, args=(servers_to_test,), daemon=True).start()

    def _sequential_url_test(self, servers):
        for config in servers:
            self._ping_task(config, is_url_test=True)
            # Small delay between tests
            import time
            time.sleep(0.2)

    def _ping_task(self, config, is_url_test):
        if is_url_test:
            ping_result = network_tester.run_single_url_test(config, self.settings)
        else:
            ping_result = network_tester.tcp_ping(config["server"], config["port"])
        
        config["ping"] = ping_result
        self.callbacks.get('schedule', lambda t, c: None)(0, lambda: self.callbacks.get('on_ping_result')(config, ping_result, is_url_test))

    def sort_servers_by_ping(self, group_name):
        if group_name not in self.server_groups:
            return
        
        configs = self.server_groups.get(group_name, [])
        configs.sort(key=lambda c: c.get("ping", 9999) if c.get("ping", 9999) != -1 else 99999)
        
        self.log("Servers sorted by ping (fastest first).", LogLevel.INFO)
        self.callbacks.get('on_servers_updated', lambda: None)()