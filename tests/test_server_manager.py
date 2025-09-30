import requests
from constants import LogLevel
from managers.server_manager import ServerManager
import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock, call

# Add project root to path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")))


class TestServerManager(unittest.TestCase):

    def setUp(self):
        """Set up a fresh ServerManager and mocks for each test."""
        self.settings = {
            "servers": {
                "group1": [
                    {"id": "1", "name": "server1", "ping": 100,
                        "group": "group1", "server": "a", "port": 1},
                    {"id": "2", "name": "server2", "ping": 200,
                        "group": "group1", "server": "b", "port": 2},
                ]
            },
            "subscriptions": []
        }
        self.callbacks = {
            "on_servers_loaded": Mock(),
            "on_servers_updated": Mock(),
            "log": Mock(),
            "on_update_start": Mock(),
            "on_update_finished": Mock(),
        }
        self.server_manager = ServerManager(self.settings, self.callbacks)
        # Manually mock the QTimer object after instantiation
        self.server_manager._save_timer = MagicMock()

        # Manually load servers as it's usually done by the main app
        self.server_manager.load_servers()
        # Clear mocks for load_servers call
        self.callbacks["on_servers_loaded"].reset_mock()

    # --- Basic CRUD and Logic Tests (Updated) ---

    def test_load_servers_with_migration(self):
        """Test that load_servers adds unique IDs to old configs."""
        old_settings = {
            "servers": {
                "no-id-group": [
                    {"name": "server_no_id", "group": "no-id-group"}
                ]
            }
        }
        with patch('managers.server_manager.settings_manager.save_settings'):
            manager = ServerManager(old_settings, self.callbacks)
            manager._save_timer = MagicMock()  # Manually mock the timer for this instance
            manager.load_servers()
            loaded_server = manager.get_servers_by_group("no-id-group")[0]
            self.assertIn("id", loaded_server)
            self.assertTrue(loaded_server["id"])
            # Checks that the debounced save was triggered
            manager._save_timer.start.assert_called_once()

    @patch("managers.server_manager.link_parser.parse_server_link")
    def test_add_manual_server(self, mock_parse_server_link):
        """Test adding a single server manually."""
        new_server_conf = {
            "name": "server3", "server": "c.com", "port": 3, "group": "group2"
        }
        mock_parse_server_link.return_value = new_server_conf

        self.server_manager.add_manual_server(
            "vless://...", group_name="group2", update_ui=True)

        self.assertIn("group2", self.server_manager.get_groups())
        self.assertEqual(
            len(self.server_manager.get_servers_by_group("group2")), 1)
        self.callbacks["on_servers_updated"].assert_called_once()

    def test_add_duplicate_server(self):
        """Test that adding a duplicate server is skipped."""
        # server1 is already in group1 with server 'a' and port 1
        with patch("managers.server_manager.link_parser.parse_server_link") as mock_parse:
            mock_parse.return_value = {
                "name": "duplicate", "server": "a", "port": 1}
            result = self.server_manager.add_manual_server("some-link")
            self.assertFalse(result)
            self.callbacks['log'].assert_any_call(
                "Server duplicate already exists in group 'group1'. Skipping.",
                LogLevel.WARNING
            )

    def test_delete_server(self):
        """Test deleting a server."""
        server_to_delete = self.server_manager.get_servers_by_group("group1")[
            0]

        self.server_manager.delete_server(server_to_delete)

        self.assertEqual(
            len(self.server_manager.get_servers_by_group("group1")), 1)
        self.callbacks["on_servers_updated"].assert_called_once()

    def test_sort_servers_by_ping(self):
        """Test sorting servers by ping."""
        self.server_manager.server_groups["group1"].append(
            {"name": "server3", "ping": 50, "group": "group1"}
        )
        self.server_manager.sort_servers_by_ping("group1")

        sorted_names = [s["name"]
                        for s in self.server_manager.get_servers_by_group("group1")]
        self.assertEqual(sorted_names, ["server3", "server1", "server2"])

    # --- Debounced Saving Tests ---

    def test_save_settings_schedules_save(self):
        """Test that save_settings() starts the debounce timer."""
        self.server_manager.save_settings()
        self.server_manager._save_timer.start.assert_called_once()

    @patch("managers.server_manager.settings_manager.save_settings")
    def test_force_save_settings_saves_immediately(self, mock_save):
        """Test force_save_settings() stops the timer and saves."""
        # Simulate timer being active
        self.server_manager._save_timer.isActive.return_value = True

        self.server_manager.force_save_settings()

        self.server_manager._save_timer.stop.assert_called_once()
        mock_save.assert_called_once_with(self.settings, self.callbacks['log'])

    @patch("managers.server_manager.settings_manager.save_settings")
    def test_force_save_settings_does_nothing_if_timer_inactive(self, mock_save):
        """Test force_save_settings() does nothing if no save is pending."""
        self.server_manager._save_timer.isActive.return_value = False
        self.server_manager.force_save_settings()
        mock_save.assert_not_called()

    # --- Parallel Subscription Update Tests ---

    @patch("managers.server_manager.requests.get")
    def test_fetch_and_process_subscription_success(self, mock_get):
        """Test the worker function for a successful subscription fetch."""
        mock_response = Mock()
        # vless link, base64 encoded
        mock_response.content = b"dmxlc3M6Ly91dWlkQHNlcnZlcjQyOjQ0MyN0ZXN0MQ=="
        mock_get.return_value = mock_response

        sub = {"name": "TestSub", "url": "http://example.com/sub"}

        with patch.object(self.server_manager, 'add_manual_server') as mock_add:
            added_count, error = self.server_manager._fetch_and_process_subscription(
                sub)

            self.assertEqual(added_count, 1)
            self.assertIsNone(error)
            mock_get.assert_called_once_with(
                "http://example.com/sub", timeout=15)
            mock_add.assert_called_once_with(
                "vless://uuid@server42:443#test1",
                group_name="TestSub",
                update_ui=False
            )

    @patch("managers.server_manager.requests.get")
    def test_fetch_and_process_subscription_network_error(self, mock_get):
        """Test the worker function for a network error."""
        mock_get.side_effect = requests.exceptions.RequestException(
            "Network Down")
        sub = {"name": "TestSub", "url": "http://example.com/sub"}

        added_count, error = self.server_manager._fetch_and_process_subscription(
            sub)

        self.assertEqual(added_count, 0)
        self.assertIsInstance(error, requests.exceptions.RequestException)
        self.callbacks['log'].assert_any_call(
            "Failed to update subscription 'TestSub': Network Down",
            LogLevel.ERROR
        )

    @patch('managers.server_manager.ThreadPoolExecutor')
    def test_update_subscriptions_task_orchestration(self, mock_executor_cls):
        """Test that the main task orchestrates workers and callbacks correctly."""
        # This is a simplified way to test the orchestration.
        # It forces the executor to run tasks sequentially in the test.
        mock_executor = MagicMock()

        def immediate_submit(fn, *args, **kwargs):
            future = MagicMock()
            future.result.return_value = fn(*args, **kwargs)
            return future

        mock_executor.submit.side_effect = immediate_submit
        mock_executor_cls.return_value.__enter__.return_value = mock_executor

        subs = [{"name": "Sub1", "url": "url1"},
                {"name": "Sub2", "url": "url2"}]

        # Mock the worker function to return predictable results
        with patch.object(self.server_manager, '_fetch_and_process_subscription') as mock_fetch:
            mock_fetch.side_effect = [(1, None), (2, Exception("Test Error"))]

            self.server_manager._update_subscriptions_task(subs)

            # Check that the worker was called for each subscription
            self.assertEqual(mock_fetch.call_count, 2)
            mock_fetch.assert_has_calls(
                [call(subs[0]), call(subs[1])], any_order=True)

            # Check that final callbacks were called once at the end
            self.callbacks['on_servers_updated'].assert_called_once()
            self.callbacks['on_update_finished'].assert_called_once()

            # Check the error passed to on_update_finished
            final_error_arg = self.callbacks['on_update_finished'].call_args[0][0]
            self.assertIsInstance(final_error_arg, list)
            self.assertEqual(len(final_error_arg), 1)
            self.assertIsInstance(final_error_arg[0], Exception)


if __name__ == "__main__":
    unittest.main()
