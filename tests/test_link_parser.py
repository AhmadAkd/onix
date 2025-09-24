import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from link_parser import parse_vless_link, parse_vmess_link, parse_shadowsocks_link

class TestLinkParser(unittest.TestCase):

    def test_parse_vless_link(self):
        link = "vless://uuid@server:443?security=tls&sni=sni.com&flow=flow&fp=fp&type=ws&path=/path#remarks"
        expected = {
            'name': 'remarks',
            'group': 'Default',
            'protocol': 'vless',
            'server': 'server',
            'port': 443,
            'uuid': 'uuid',
            'tls_enabled': True,
            'sni': 'sni.com',
            'flow': 'flow',
            'fp': 'fp',
            'transport': 'ws',
            'ws_path': '/path'
        }
        self.assertEqual(parse_vless_link(link), expected)

    def test_parse_vmess_link(self):
        vmess_json = '{"v": "2", "ps": "remarks", "add": "server", "port": 443, "id": "uuid", "aid": 0, "net": "ws", "type": "none", "host": "host.com", "path": "/path", "tls": "tls", "sni": "sni.com"}'
        encoded_vmess = 'vmess://' + __import__('base64').b64encode(vmess_json.encode('utf-8')).decode('utf-8')
        expected = {
            'name': 'remarks',
            'group': 'Default',
            'protocol': 'vmess',
            'server': 'server',
            'port': 443,
            'uuid': 'uuid',
            'alter_id': 0,
            'security': 'auto',
            'tls_enabled': True,
            'sni': 'sni.com',
            'transport': 'ws',
            'ws_path': '/path',
            'ws_host': 'host.com'
        }
        self.assertEqual(parse_vmess_link(encoded_vmess), expected)

    def test_parse_shadowsocks_link(self):
        link = "ss://bWV0aG9kOnBhc3N3b3Jk@server:8443#remarks"
        expected = {
            'name': 'remarks',
            'group': 'Default',
            'protocol': 'shadowsocks',
            'server': 'server',
            'port': 8443,
            'method': 'method',
            'password': 'password'
        }
        self.assertEqual(parse_shadowsocks_link(link), expected)

if __name__ == '__main__':
    unittest.main()
