from config_generator import generate_config_json
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")))


class TestConfigGenerator(unittest.TestCase):
    def test_generate_config_json(self):
        server_config = {
            "protocol": "vless",
            "server": "server",
            "port": 443,
            "uuid": "uuid",
            "tls_enabled": True,
            "sni": "sni.com",
            "flow": "flow",
            "fp": "fp",
            "transport": "ws",
            "ws_path": "/path",
        }
        settings = {
            "dns_servers": "1.1.1.1,8.8.8.8",
            "bypass_domains": "domain.com,domain:geosite:google",
            "bypass_ips": "1.1.1.1,geoip:ir",
        }
        config = generate_config_json(server_config, settings)

        self.assertEqual(config["outbounds"][1]["type"], "vless")
        self.assertEqual(config["dns"]["servers"][0]["address"], "1.1.1.1")
        self.assertIn(
            {"domain": ["domain.com"],
                "server": "dns_direct"}, config["dns"]["rules"]
        )
        self.assertIn(
            {"rule_set": ["geosite-google"], "outbound": "direct"},
            config["route"]["rules"],
        )
        self.assertIn(
            {"ip_cidr": ["1.1.1.1"],
                "outbound": "direct"}, config["route"]["rules"]
        )
        self.assertIn(
            {"rule_set": ["geoip-ir"],
                "outbound": "direct"}, config["route"]["rules"]
        )


if __name__ == "__main__":
    unittest.main()
