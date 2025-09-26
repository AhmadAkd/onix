import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import patch, mock_open
from main import SingboxApp


class TestSingboxApp(unittest.TestCase):
    @patch("main.utils.get_resource_path")
    @patch("builtins.open", new_callable=mock_open, read_data="1.0.0")
    def test_get_app_version(self, mock_file, mock_get_resource_path):
        mock_get_resource_path.return_value = "version.txt"

        # Since SingboxApp.__init__ does a lot, we can't easily instantiate it.
        # We can call the method directly if it were static, but it's not.
        # So, we need to mock the app instance.
        app = unittest.mock.Mock()
        app._get_app_version.side_effect = SingboxApp._get_app_version.__get__(app)

        version = app._get_app_version()

        self.assertEqual(version, "1.0.0")


if __name__ == "__main__":
    unittest.main()
