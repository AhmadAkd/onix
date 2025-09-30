"""
Professional Subscription Manager for Onix
Handles subscription fetching, parsing, and server management
"""

import requests
import base64
import binascii
import threading
import time
from typing import Dict, List, Any, Optional, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from constants import LogLevel
import link_parser


class SubscriptionManager:
    """Professional subscription manager with proper error handling and UI updates."""

    def __init__(self, server_manager, settings: Dict[str, Any], callbacks: Dict[str, Callable]):
        self.server_manager = server_manager
        self.settings = settings
        self.callbacks = callbacks
        self.thread_pool = ThreadPoolExecutor(max_workers=3)
        self._update_in_progress = False
        self._cancel_event = threading.Event()

    def is_update_in_progress(self) -> bool:
        """Check if subscription update is currently in progress."""
        return self._update_in_progress

    def cancel_update(self):
        """Cancel ongoing subscription update."""
        self._cancel_event.set()

    def update_subscriptions(self, subscriptions: List[Dict[str, Any]]) -> None:
        """Update multiple subscriptions with proper error handling and UI feedback."""
        if self._update_in_progress:
            self.callbacks.get("show_warning", lambda t, m: None)(
                "Update In Progress", "Another subscription update is already running. Please wait.")
            return

        if not subscriptions:
            self.callbacks.get("show_warning", lambda t, m: None)(
                "No Subscriptions", "No subscriptions to update.")
            return

        self._update_in_progress = True
        self._cancel_event.clear()

        # Start update in background thread
        self.thread_pool.submit(self._update_subscriptions_task, subscriptions)

    def _update_subscriptions_task(self, subscriptions: List[Dict[str, Any]]) -> None:
        """Background task to update subscriptions."""
        try:
            self.callbacks.get("on_update_start", lambda: None)()

            enabled_subs = [
                sub for sub in subscriptions if sub.get("enabled", True)]
            if not enabled_subs:
                self.callbacks.get("show_warning", lambda t, m: None)(
                    "No Enabled Subscriptions", "No enabled subscriptions to update.")
                return

            self.log(
                f"Starting update of {len(enabled_subs)} subscription(s)...", LogLevel.INFO)

            # Process subscriptions in parallel
            future_to_sub = {
                self.thread_pool.submit(self._process_single_subscription, sub): sub
                for sub in enabled_subs
            }

            total_added = 0
            errors = []

            for future in as_completed(future_to_sub):
                if self._cancel_event.is_set():
                    self.log("Subscription update cancelled by user.",
                             LogLevel.WARNING)
                    break

                sub = future_to_sub[future]
                try:
                    added_count, error = future.result()
                    if error:
                        errors.append(
                            f"Error updating '{sub.get('name', 'Unknown')}': {error}")
                    else:
                        total_added += added_count
                        self.log(
                            f"Updated '{sub.get('name', 'Unknown')}': {added_count} servers added", LogLevel.SUCCESS)

                except Exception as e:
                    errors.append(
                        f"Unexpected error updating '{sub.get('name', 'Unknown')}': {e}")

            # Save all changes
            if total_added > 0:
                self.server_manager.save_settings()
                self.log(
                    f"Subscription update completed: {total_added} total servers added", LogLevel.SUCCESS)
            else:
                self.log(
                    "Subscription update completed: No new servers found", LogLevel.INFO)

            # Show errors if any
            if errors:
                error_msg = "\n".join(errors)
                self.callbacks.get("show_error", lambda t, m: None)(
                    "Subscription Update Errors", error_msg)

        except Exception as e:
            self.log(
                f"Critical error during subscription update: {e}", LogLevel.ERROR)
            self.callbacks.get("show_error", lambda t, m: None)(
                "Critical Error", f"Subscription update failed: {e}")
        finally:
            self._update_in_progress = False
            self.callbacks.get("on_update_finish", lambda x: None)(None)

    def _process_single_subscription(self, sub: Dict[str, Any]) -> Tuple[int, Optional[str]]:
        """Process a single subscription and return (added_count, error)."""
        sub_name = sub.get("name", "Unknown")
        sub_url = sub.get("url", "")

        if not sub_url:
            return 0, "No URL provided"

        try:
            self.log(f"Fetching subscription: {sub_name}", LogLevel.INFO)

            # Fetch subscription data
            response = requests.get(sub_url, timeout=30, headers={
                'User-Agent': 'Onix/1.0 (Subscription Manager)'
            })
            response.raise_for_status()

            # Decode content
            try:
                content = base64.b64decode(response.content).decode('utf-8')
            except (binascii.Error, UnicodeDecodeError):
                content = response.text

            # Parse links
            links = [line.strip()
                     for line in content.splitlines() if line.strip()]

            if not links:
                return 0, "No valid links found in subscription"

            self.log(f"Found {len(links)} links in {sub_name}", LogLevel.INFO)

            # Create callbacks object once outside the loop
            server_callbacks = {
                'show_info': lambda title, msg: self.callbacks.get("show_info", lambda t, m: None)(title, msg),
                'show_warning': lambda title, msg: self.callbacks.get("show_warning", lambda t, m: None)(title, msg),
                'show_error': lambda title, msg: self.callbacks.get("show_error", lambda t, m: None)(title, msg),
                # Default to yes for subscription updates
                'ask_yes_no': lambda title, question: True,
            }

            # Add servers
            added_count = 0
            for link in links:
                if self._cancel_event.is_set():
                    break

                try:
                    if self.server_manager.add_manual_server(
                        link,
                        group_name=sub_name,
                        update_ui=False,  # We'll update UI at the end
                        callbacks=server_callbacks
                    ):
                        added_count += 1

                except Exception as e:
                    self.log(
                        f"Error adding server from {sub_name}: {e}", LogLevel.WARNING)
                    continue

            return added_count, None

        except requests.exceptions.RequestException as e:
            return 0, f"Network error: {e}"
        except Exception as e:
            return 0, f"Processing error: {e}"

    def log(self, message: str, level: LogLevel = LogLevel.INFO):
        """Log a message with proper level."""
        self.callbacks.get("log", lambda m, l: None)(message, level)

    def get_subscription_status(self) -> Dict[str, Any]:
        """Get current subscription status."""
        return {
            "update_in_progress": self._update_in_progress,
            "total_subscriptions": len(self.settings.get("subscriptions", [])),
            "enabled_subscriptions": len([s for s in self.settings.get("subscriptions", []) if s.get("enabled", True)])
        }

    def cleanup(self):
        """Cleanup resources."""
        self._cancel_event.set()
        self.thread_pool.shutdown(wait=True)
