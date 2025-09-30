from link_parser import (
    parse_vless_link,
    parse_vmess_link,
    parse_shadowsocks_link,
    parse_trojan_link,
    parse_tuic_link,
    parse_hysteria2_link,
    parse_wireguard_config,
    parse_ssh_link,
)
import unittest
import sys
import os
import unittest.mock
import base64

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")))


class TestLinkParser(unittest.TestCase):
    def test_parse_vless_link(self):
        link = "vless://uuid@server:443?security=tls&sni=sni.com&flow=flow&fp=fp&type=ws&path=/path#remarks"
        result = parse_vless_link(link)
        # Check individual fields instead of exact match due to ID generation
        self.assertEqual(result["name"], "remarks")
        self.assertEqual(result["group"], "Default")
        self.assertEqual(result["protocol"], "vless")
        self.assertEqual(result["server"], "server")
        self.assertEqual(result["port"], 443)
        self.assertEqual(result["uuid"], "uuid")
        self.assertEqual(result["tls_enabled"], True)
        self.assertEqual(result["sni"], "sni.com")
        self.assertEqual(result["flow"], "flow")
        self.assertEqual(result["fp"], "fp")
        self.assertEqual(result["transport"], "ws")
        self.assertEqual(result["ws_path"], "/path")

    def test_parse_vmess_link(self):
        vmess_json = '{"v": "2", "ps": "remarks", "add": "server", "port": 443, "id": "uuid", "aid": 0, "net": "ws", "type": "none", "host": "host.com", "path": "/path", "tls": "tls", "sni": "sni.com"}'
        encoded_vmess = "vmess://" + base64.b64encode(
            vmess_json.encode("utf-8")
        ).decode("utf-8")
        expected = {
            "id": unittest.mock.ANY,
            "name": "remarks",
            "group": "Default",
            "protocol": "vmess",
            "server": "server",
            "port": 443,
            "uuid": "uuid",
            "alter_id": 0,
            "security": "auto",
            "tls_enabled": True,
            "sni": "sni.com",
            "transport": "ws",
            "ws_path": "/path",
            "ws_host": "host.com",
        }
        self.assertEqual(parse_vmess_link(encoded_vmess), expected)

    def test_parse_shadowsocks_link(self):
        link = "ss://bWV0aG9kOnBhc3N3b3Jk@server:8443#remarks"
        expected = {
            "id": unittest.mock.ANY,
            "name": "remarks",
            "group": "Default",
            "protocol": "shadowsocks",
            "server": "server",
            "port": 8443,
            "method": "method",
            "password": "password",
        }
        self.assertEqual(parse_shadowsocks_link(link), expected)

    def test_parse_trojan_link(self):
        link = "trojan://password@server:443?sni=sni.com&fp=fp#remarks"
        expected = {
            "id": unittest.mock.ANY,
            "name": "remarks",
            "group": "Default",
            "protocol": "trojan",
            "server": "server",
            "port": 443,
            "password": "password",
            "sni": "sni.com",
            "fp": "fp",
        }
        self.assertEqual(parse_trojan_link(link), expected)

    def test_parse_tuic_link(self):
        link = "tuic://uuid:password@server:443?sni=sni.com&congestion_control=bbr&udp_relay_mode=native&alpn=h3&allow_insecure=1#remarks"
        result = parse_tuic_link(link)
        expected = {
            "id": unittest.mock.ANY,
            "name": "remarks",
            "group": "Default",
            "protocol": "tuic",
            "server": "server",
            "port": 443,
            "uuid": "uuid",
            "password": "password",
            "sni": "sni.com",
            "congestion_control": "bbr",
            "udp_relay_mode": "native",
            "alpn": "h3",
            "allow_insecure": True,
        }
        self.assertEqual(result, expected)

    def test_parse_hysteria2_link(self):
        link = "hysteria2://password@server:443?sni=sni.com&insecure=1&obfs=salamander&obfs-password=obfs-pass#remarks"
        result = parse_hysteria2_link(link)
        expected = {
            "id": unittest.mock.ANY,
            "name": "remarks",
            "group": "Default",
            "protocol": "hysteria2",
            "server": "server",
            "port": 443,
            "password": "password",
            "sni": "sni.com",
            "insecure": True,
            "obfs": "salamander",
            "obfs_password": "obfs-pass",
        }
        self.assertEqual(result, expected)

    def test_parse_wireguard_config(self):
        config_content = """
[Interface]
PrivateKey = private_key_here
Address = 10.0.0.2/32
DNS = 1.1.1.1

[Peer]
PublicKey = public_key_here
PresharedKey = preshared_key_here
AllowedIPs = 0.0.0.0/0
Endpoint = server.com:51820
"""
        result = parse_wireguard_config(config_content, "MyWG")
        self.assertEqual(result["name"], "MyWG")
        self.assertEqual(result["protocol"], "wireguard")
        self.assertEqual(result["server"], "server.com")
        self.assertEqual(result["port"], 51820)
        self.assertEqual(result["private_key"], "private_key_here")
        self.assertEqual(result["public_key"], "public_key_here")

    def test_parse_reality_link(self):
        link = "vless://uuid@server:443?security=reality&publicKey=pubkey&shortId=shortid&sni=sni.com&flow=flow&fp=fp&type=ws&path=/path#My-Reality"
        result = parse_vless_link(link)
        # Check individual fields instead of exact match due to ID generation
        self.assertEqual(result["name"], "My-Reality")
        self.assertEqual(result["group"], "My")
        self.assertEqual(result["protocol"], "vless")
        self.assertEqual(result["server"], "server")
        self.assertEqual(result["port"], 443)
        self.assertEqual(result["uuid"], "uuid")
        self.assertEqual(result["tls_enabled"], True)
        self.assertEqual(result["tls_type"], "reality")
        self.assertEqual(result["public_key"], "pubkey")
        self.assertEqual(result["short_id"], "shortid")
        self.assertEqual(result["sni"], "sni.com")
        self.assertEqual(result["flow"], "flow")
        self.assertEqual(result["fp"], "fp")
        self.assertEqual(result["transport"], "ws")
        self.assertEqual(result["ws_path"], "/path")

    def test_parse_ssh_link(self):
        link = "ssh://user:password@server:22#My-SSH"
        result = parse_ssh_link(link)
        # Check individual fields instead of exact match due to ID generation
        self.assertEqual(result["name"], "My-SSH")
        self.assertEqual(result["group"], "My")
        self.assertEqual(result["protocol"], "ssh")
        self.assertEqual(result["server"], "server")
        self.assertEqual(result["port"], 22)
        self.assertEqual(result["user"], "user")
        self.assertEqual(result["password"], "password")

    # --- Invalid VLESS Links ---
    def test_parse_vless_link_invalid_format(self):
        self.assertIsNone(parse_vless_link("invalid-vless-link"))
        self.assertIsNone(
            parse_vless_link("vless://uuid@server")
        )  # Incomplete (missing port)
        self.assertIsNone(
            parse_vless_link("vless://uuid@server:invalid_port")
        )  # Invalid port
        self.assertIsNone(parse_vless_link(
            "vless://@server:443"))  # Missing UUID
        self.assertIsNone(parse_vless_link(
            "vless://uuid@:443"))  # Missing server

    # --- Invalid VMESS Links ---
    def test_parse_vmess_link_invalid_format(self):
        self.assertIsNone(parse_vmess_link("invalid-vmess-link"))
        self.assertIsNone(
            parse_vmess_link("vmess://invalid_base64")
        )  # Malformed base64
        # Malformed JSON in base64
        malformed_json = base64.b64encode(
            b'{ "v": "2", "ps": "remarks", "add": "server" }'
        ).decode("utf-8")
        self.assertIsNone(
            parse_vmess_link(f"vmess://{malformed_json}")
        )  # Missing port and id

    # --- Invalid Shadowsocks Links ---
    def test_parse_shadowsocks_link_invalid_format(self):
        self.assertIsNone(parse_shadowsocks_link("invalid-ss-link"))
        self.assertIsNone(
            parse_shadowsocks_link("ss://server:port")
        )  # Missing method/password
        self.assertIsNone(
            parse_shadowsocks_link("ss://invalid_base64@server:8443")
        )  # Malformed base64
        self.assertIsNone(
            parse_shadowsocks_link(
                "ss://bWV0aG9kOnBhc3N3b3Jk@server:invalid_port")
        )  # Invalid port

    # --- Invalid/Edge Case Links for Newer Protocols ---

    def test_parse_link_with_ipv6_and_unusual_chars(self):
        """Test parsing a link with an IPv6 address and special characters in the name."""
        link = "vless://uuid@[::1]:443?security=tls&sni=sni.com#Test Server 🤪"
        parsed = parse_vless_link(link)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["server"], "[::1]")
        self.assertEqual(parsed["name"], "Test Server 🤪")

    def test_parse_reality_link_invalid(self):
        """Test invalid REALITY links."""
        # Missing public key
        self.assertIsNone(
            parse_vless_link(
                "vless://uuid@server:443?security=reality&shortId=shortid&sni=sni.com#test"
            )
        )
        # Missing SNI
        self.assertIsNone(
            parse_vless_link(
                "vless://uuid@server:443?security=reality&publicKey=pubkey&shortId=shortid#test"
            )
        )

    def test_parse_hysteria2_link_invalid(self):
        """Test invalid Hysteria2 links."""
        # Missing hostname
        self.assertIsNone(
            parse_hysteria2_link("hysteria2://@:443?sni=sni.com#test")
        )

    def test_parse_wireguard_config_invalid(self):
        """Test invalid WireGuard configurations."""
        # Missing PrivateKey
        invalid_conf_1 = """
[Interface]
Address = 10.0.0.2/32
[Peer]
PublicKey = public_key_here
Endpoint = server.com:51820
"""
        self.assertIsNone(parse_wireguard_config(invalid_conf_1, "bad1"))

        # Missing [Peer] section
        invalid_conf_2 = """
[Interface]
PrivateKey = private_key_here
Address = 10.0.0.2/32
"""
        self.assertIsNone(parse_wireguard_config(invalid_conf_2, "bad2"))

        # Missing Peer PublicKey
        invalid_conf_3 = """
[Interface]
PrivateKey = private_key_here
[Peer]
Endpoint = server.com:51820
"""
        self.assertIsNone(parse_wireguard_config(invalid_conf_3, "bad3"))


if __name__ == "__main__":
    unittest.main()
