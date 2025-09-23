import json
import os
import socket
import time
import requests
import base64
import re
from urllib.parse import urlparse, parse_qs, unquote
import subprocess
import sys  # Added for PyInstaller path handling
from constants import PROXY_HOST, PROXY_PORT, PROXY_SERVER_ADDRESS


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.getcwd(), relative_path)


def tcp_ping(host, port, timeout=2):
    """Pings a TCP host and port to measure latency."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        start_time = time.time()
        sock.connect((host, port))
        end_time = time.time()
        sock.close()
        return int((end_time - start_time) * 1000)
    except (socket.timeout, ConnectionRefusedError, OSError):
        return -1


def url_test(proxy_address, url="http://www.gstatic.com/generate_204", timeout=5):
    """Tests a URL through a given proxy to measure real-world latency."""
    proxies = {'http': f'http://{proxy_address}',
               'https': f'http://{proxy_address}'}
    try:
        start_time = time.time()
        response = requests.get(url, proxies=proxies, timeout=timeout)
        end_time = time.time()
        if response.status_code == 204:
            return int((end_time - start_time) * 1000)
    except requests.exceptions.RequestException:
        pass
    return -1


def get_external_ip(proxy_address, timeout=5):
    """Fetches the external IP address through a given proxy."""
    proxies = {'http': f'http://{proxy_address}',
               'https': f'http://{proxy_address}'}
    try:
        response = requests.get("https://api.ipify.org",
                                proxies=proxies, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException:
        return "N/A"


def wait_for_proxy(host, port, timeout=5):
    """Waits for the proxy server to become available."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=0.1):
                return True
        except (socket.timeout, ConnectionRefusedError):
            time.sleep(0.1)
    return False


def run_single_url_test(config):
    """Runs a URL test for a single server configuration."""
    temp_proc = None
    temp_config_file = "temp_url_test_config.json"
    try:
        # Pass empty settings to avoid using custom rules during URL test
        full_config = generate_config_json(config, settings={})
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            json.dump(full_config, f, indent=2)

        command = [get_resource_path('sing-box.exe'),
                   'run', '-c', temp_config_file]
        temp_proc = subprocess.Popen(command, stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)

        if wait_for_proxy(PROXY_HOST, PROXY_PORT):
            return url_test(PROXY_SERVER_ADDRESS)
        else:
            return -1
    except Exception:
        return -1
    finally:
        if temp_proc:
            temp_proc.kill()
        try:
            if os.path.exists(temp_config_file):
                os.remove(temp_config_file)
        except OSError:
            pass


def parse_server_link(link):
    """Parses VLESS, Vmess, or Shadowsocks subscription links."""
    if link.startswith("vless://"):
        return parse_vless_link(link)
    elif link.startswith("vmess://"):
        return parse_vmess_link(link)
    elif link.startswith("ss://"):
        return parse_shadowsocks_link(link)
    return None


def parse_vless_link(link):
    try:
        parsed_url = urlparse(link)
        remarks = unquote(
            parsed_url.fragment) if parsed_url.fragment else "Unnamed"
        remarks = re.sub(r'[\U0001F1E6-\U0001F1FF]', '', remarks).strip()
        group = "Default"
        delimiters = ['|', '-', '_', ' ']
        for d in delimiters:
            if d in remarks:
                group = remarks.split(d)[0].strip()
                break
        query_params = parse_qs(parsed_url.query)
        return {
            "name": remarks,
            "group": group,
            "protocol": "vless",
            "server": parsed_url.hostname,
            "port": parsed_url.port,
            "uuid": parsed_url.username,
            "tls_enabled": query_params.get("security", [""])[0] == "tls",
            "sni": query_params.get("sni", [""])[0],
            "flow": query_params.get("flow", [""])[0],
            "fp": query_params.get("fp", [""])[0],
            "transport": query_params.get("type", ["tcp"])[0],
            "ws_path": query_params.get("path", ["/"])[0]
        }
    except Exception:
        return None


def parse_vmess_link(link):
    try:
        base64_str = link.replace("vmess://", "")
        base64_str += '=' * (-len(base64_str) % 4)
        decoded_str = base64.b64decode(base64_str).decode('utf-8')
        vmess_config = json.loads(decoded_str)

        remarks = vmess_config.get("ps", "Unnamed")
        group = "Default"
        delimiters = ['|', '-', '_', ' ']
        for d in delimiters:
            if d in remarks:
                group = remarks.split(d)[0].strip()
                break

        return {
            "name": remarks,
            "group": group,
            "protocol": "vmess",
            "server": vmess_config.get("add"),
            "port": int(vmess_config.get("port", 0)),
            "uuid": vmess_config.get("id"),
            "alter_id": int(vmess_config.get("aid", 0)),
            "security": vmess_config.get("scy", "auto"),
            "tls_enabled": vmess_config.get("tls", "") == "tls",
            "sni": vmess_config.get("sni", ""),
            "transport": vmess_config.get("net", "tcp"),
            "ws_path": vmess_config.get("path", "/"),
            "ws_host": vmess_config.get("host", "")
        }
    except Exception:
        return None


def parse_shadowsocks_link(link):
    try:
        parsed_url = urlparse(link)
        remarks = unquote(
            parsed_url.fragment) if parsed_url.fragment else "Unnamed"

        group = "Default"
        delimiters = ['|', '-', '_', ' ']
        for d in delimiters:
            if d in remarks:
                group = remarks.split(d)[0].strip()
                break

        user_info_b64 = parsed_url.username
        user_info_b64 += '=' * (-len(user_info_b64) % 4)
        decoded_user_info = base64.b64decode(user_info_b64).decode('utf-8')

        method, password = decoded_user_info.split(':', 1)

        return {
            "name": remarks,
            "group": group,
            "protocol": "shadowsocks",
            "server": parsed_url.hostname,
            "port": parsed_url.port,
            "method": method,
            "password": password
        }
    except Exception:
        return None


def generate_config_json(server_config, settings={}):
    """Generates a sing-box configuration JSON from a server config dict and app settings."""
    sni_value = server_config.get("sni") or server_config.get("server")

    # --- DNS Configuration ---
    user_dns_str = settings.get("dns_servers", "1.1.1.1,8.8.8.8")
    user_dns_list = [s.strip() for s in user_dns_str.split(',') if s.strip()]

    # Define DNS outbounds (without address field for type "dns")
    dns_outbounds = []
    dns_outbounds.append({"type": "dns", "tag": "dns_proxy"})
    dns_outbounds.append({"type": "dns", "tag": "dns_direct"})

    # DNS servers for the dns section
    dns_servers_config = []
    if user_dns_list:
        dns_servers_config.append(
            {"address": user_dns_list[0], "tag": "dns_proxy"})
    else:
        dns_servers_config.append({"address": "1.1.1.1", "tag": "dns_proxy"})
    dns_servers_config.append({"address": "8.8.8.8", "tag": "dns_direct"})

    # --- Route & DNS Rules ---
    bypass_domains_str = settings.get(
        "bypass_domains", "geosite:ir,*.ir,*.local")
    bypass_domains_list = [d.strip()
                           for d in bypass_domains_str.split(',') if d.strip()]

    bypass_ips_str = settings.get(
        "bypass_ips", "geoip:ir,192.168.0.0/16,127.0.0.1,10.0.0.0/8")
    bypass_ips_list = [i.strip()
                       for i in bypass_ips_str.split(',') if i.strip()]

    # Separate geosite/geoip from normal domains/ips for correct rule generation
    geosite_rules = [d.replace("geosite:", "")
                     for d in bypass_domains_list if d.startswith("geosite:")]
    domain_suffix_rules = [
        d for d in bypass_domains_list if not d.startswith("geosite:")]
    geoip_rules = [i.replace("geoip:", "")
                   for i in bypass_ips_list if i.startswith("geoip:")]
    ip_cidr_rules = [i for i in bypass_ips_list if not i.startswith("geoip:")]

    route_rules = [{"protocol": ["dns"], "outbound": "dns"}]

    if geosite_rules:
        route_rules.append({"geosite": geosite_rules, "outbound": "direct"})
    if domain_suffix_rules:
        route_rules.append(
            {"domain_suffix": domain_suffix_rules, "outbound": "direct"})
    if geoip_rules:
        route_rules.append({"geoip": geoip_rules, "outbound": "direct"})
    if ip_cidr_rules:
        route_rules.append({"ip_cidr": ip_cidr_rules, "outbound": "direct"})

    route_rules.append({"protocol": ["quic"], "outbound": "block"})

    dns_rules = []
    if geosite_rules:
        dns_rules.append({"geosite": geosite_rules, "server": "dns_direct"})
    if domain_suffix_rules:
        dns_rules.append(
            {"domain_suffix": domain_suffix_rules, "server": "dns_direct"})

    config_template = {
        "log": {"level": "info"},
        "dns": {
            "servers": dns_servers_config,
            "rules": dns_rules,
            "strategy": "prefer_ipv4",
            "final": "dns_proxy"
        },
        "inbounds": [
            {"type": "socks", "tag": "socks-in",
                "listen": "127.0.0.1", "listen_port": 0},
            {"type": "http", "tag": "http-in",
                "listen": PROXY_HOST, "listen_port": PROXY_PORT}
        ],
        "outbounds": [
            {"type": "direct", "tag": "direct"},
            {"type": "block", "tag": "block"}
        ] + dns_outbounds,
        "route": {
            "rules": route_rules,
            "final": "proxy-out"
        }
    }

    if server_config["protocol"] == "vless":
        outbound = {
            "type": "vless",
            "tag": "proxy-out",
            "server": server_config["server"],
            "server_port": server_config["port"],
            "uuid": server_config["uuid"],
        }

        if server_config["tls_enabled"]:
            tls_config = {
                "enabled": True,
                "server_name": sni_value,
                "insecure": True,
                "alpn": ["h2", "http/1.1"]
            }
            if fingerprint := server_config.get("fp"):
                tls_config["utls"] = {
                    "enabled": True, "fingerprint": fingerprint}
            outbound["tls"] = tls_config

        if server_config.get("flow") and server_config.get("transport") != "ws":
            outbound["flow"] = server_config.get("flow")

        if server_config.get("transport") == "ws":
            host_header = server_config.get(
                "sni") or server_config.get("server")
            outbound["transport"] = {
                "type": "ws",
                "path": server_config.get("ws_path", "/"),
                "headers": {"Host": host_header}
            }

        config_template["outbounds"].append(outbound)

    elif server_config["protocol"] == "vmess":
        tls_config = {
            "enabled": server_config["tls_enabled"],
            "server_name": server_config.get("sni") or server_config.get("server"),
            "insecure": True
        }

        outbound = {
            "type": "vmess",
            "tag": "proxy-out",
            "server": server_config["server"],
            "server_port": server_config["port"],
            "uuid": server_config["uuid"],
            "security": server_config.get("security", "auto"),
            "alter_id": server_config.get("alter_id", 0),
            "network": server_config.get("transport", "tcp"), # Add network field
            "tls": tls_config
        }

        if server_config.get("transport") == "ws":
            host_header = server_config.get(
                "ws_host") or server_config.get("server")
            outbound["transport"] = {
                "type": "ws",
                "path": server_config.get("ws_path", "/"),
                "headers": {"Host": host_header}
            }

        config_template["outbounds"].append(outbound)

    elif server_config["protocol"] == "shadowsocks":
        outbound = {
            "type": "shadowsocks",
            "tag": "proxy-out",
            "server": server_config["server"],
            "server_port": server_config["port"],
            "method": server_config["method"],
            "password": server_config["password"]
        }
        config_template["outbounds"].append(outbound)

    return config_template
