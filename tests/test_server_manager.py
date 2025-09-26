import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import Mock, patch
from managers.server_manager import ServerManager
import requests


class TestServerManager(unittest.TestCase):
    def setUp(self):
        self.settings = {
            "servers": {
                "group1": [
                    {"name": "server1", "ping": 100, "group": "group1"},
                    {"name": "server2", "ping": 200, "group": "group1"},
                ]
            }
        }
        self.callbacks = {
            "on_servers_loaded": Mock(),
            "on_servers_updated": Mock(),
            "log": Mock(),
            "on_error": Mock(),
            "schedule": Mock(),
            "on_update_finish": Mock(),
        }
        self.server_manager = ServerManager(self.settings, self.callbacks)

    def test_load_servers(self):
        self.server_manager.load_servers()
        self.assertEqual(self.server_manager.get_groups(), ["group1"])
        self.assertEqual(len(self.server_manager.get_servers_by_group("group1")), 2)
        self.callbacks["on_servers_loaded"].assert_called_once()

    @patch("managers.server_manager.link_parser.parse_server_link")
    def test_add_manual_server(self, mock_parse_server_link):
        new_server = {
            "name": "server3",
            "server": "server3.com",
            "port": 443,
            "group": "group2",
        }
        mock_parse_server_link.return_value = new_server

        self.server_manager.add_manual_server("vless://...")

        self.assertIn("group2", self.server_manager.get_groups())
        self.assertEqual(len(self.server_manager.get_servers_by_group("group2")), 1)
        self.callbacks["on_servers_updated"].assert_called_once()

    def test_delete_server(self):
        server_to_delete = self.settings["servers"]["group1"][0]
        self.server_manager.load_servers()

        self.server_manager.delete_server(server_to_delete)

        self.assertEqual(len(self.server_manager.get_servers_by_group("group1")), 1)
        self.callbacks["on_servers_updated"].assert_called_once()

    def test_edit_server(self):
        server_to_edit = self.settings["servers"]["group1"][0]
        self.server_manager.load_servers()

        self.server_manager.edit_server(server_to_edit, "new_name")

        self.assertEqual(
            self.server_manager.get_servers_by_group("group1")[0]["name"], "new_name"
        )
        self.callbacks["on_servers_updated"].assert_called_once()

    def test_sort_servers_by_ping(self):
        self.server_manager.load_servers()
        self.server_manager.server_groups["group1"].append(
            {"name": "server3", "ping": 50, "group": "group1"}
        )

        self.server_manager.sort_servers_by_ping("group1")

        sorted_servers = self.server_manager.get_servers_by_group("group1")
        self.assertEqual(sorted_servers[0]["name"], "server3")
        self.assertEqual(sorted_servers[1]["name"], "server1")
        self.assertEqual(sorted_servers[2]["name"], "server2")
        self.callbacks["on_servers_updated"].assert_called_once()

    @patch("requests.get")
    def test_update_subscription_network_error(self, mock_requests_get):
        mock_requests_get.side_effect = requests.exceptions.RequestException(
            "Test Error"
        )

        self.server_manager._update_subscription_task("http://example.com", None)

        self.callbacks["on_error"].assert_called_once()
        self.callbacks["on_update_finish"].assert_called_once_with(error=True)

    @patch("requests.get")
    def test_update_subscription_empty_content(self, mock_requests_get):
        mock_response = Mock()
        mock_response.text = ""
        mock_requests_get.return_value = mock_response

        self.server_manager._update_subscription_task("http://example.com", None)

        self.callbacks["log"].assert_any_call(
            "Subscription content is empty.", "warning"
        )
        self.callbacks["on_update_finish"].assert_called_once_with(error=False)

    @patch("requests.get")
    def test_update_subscription_malformed_content(self, mock_requests_get):
        mock_response = Mock()
        mock_response.text = "This is not a valid subscription content."
        mock_requests_get.return_value = mock_response

        self.server_manager._update_subscription_task("http://example.com", None)

        self.callbacks["log"].assert_any_call(
            "No valid server links found in subscription.", "warning"
        )
        self.callbacks["on_update_finish"].assert_called_once_with(error=False)

    @patch("requests.get")
    @patch("managers.server_manager.link_parser.parse_server_link")
    def test_update_subscription_mixed_valid_invalid_links(
        self, mock_parse_server_link, mock_requests_get
    ):
        # Simulate subscription content with one valid and one invalid link
        mock_response = Mock()
        mock_response.text = "vless://valid@server:443\ninvalid-link"
        mock_requests_get.return_value = mock_response

        # Configure mock_parse_server_link to return a valid server for the first call
        # and None for the second (invalid) call
        mock_parse_server_link.side_effect = [
            {
                "name": "valid_server",
                "protocol": "vless",
                "server": "valid",
                "port": 443,
                "uuid": "valid",
            },
            None,
        ]

        self.server_manager._update_subscription_task("http://example.com", None)

        # Verify that only the valid server was added
        self.assertEqual(len(self.server_manager.get_all_servers()), 1)
        self.assertEqual(
            self.server_manager.get_all_servers()[0]["name"], "valid_server"
        )
        self.callbacks["log"].assert_any_call(
            "Found 1 new server(s) and 1 invalid link(s).", "info"
        )
        self.callbacks["on_update_finish"].assert_called_once_with(error=False)


if __name__ == "__main__":
    unittest.main()
