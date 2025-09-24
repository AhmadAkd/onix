import json
import os
import socket
import time
import requests
import base64
import re
import tempfile
from urllib.parse import urlparse, parse_qs, unquote
import subprocess
import sys  # Added for PyInstaller path handling
import binascii # Added for specific error handling
import winreg
import ctypes
from constants import (
    PROXY_HOST, PROXY_PORT, PROXY_SERVER_ADDRESS, PROXY_BYPASS,
    TCP_PING_TIMEOUT, URL_TEST_TIMEOUT, GET_EXTERNAL_IP_TIMEOUT,
    WAIT_FOR_PROXY_TIMEOUT, WAIT_FOR_PROXY_INTERVAL,
    URL_TEST_DEFAULT_URL, GET_EXTERNAL_IP_URL,
    GEOIP_RULE_SET_URL, GEOSITE_RULE_SET_URL,
    IRAN_GEOIP_RULE_SET_URL, IRAN_GEOSITE_RULE_SET_URL, LogLevel
)

# --- Public Functions ---

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.getcwd(), relative_path)

def tcp_ping(host, port, timeout=TCP_PING_TIMEOUT):
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

def url_test(proxy_address, url=URL_TEST_DEFAULT_URL, timeout=URL_TEST_TIMEOUT):
    """Tests a URL through a given proxy to measure real-world latency."""
    proxies = {'http': f'http://{proxy_address}', 'https': f'http://{proxy_address}'}
    try:
        start_time = time.time()
        response = requests.get(url, proxies=proxies, timeout=timeout)
        end_time = time.time()
        if response.status_code == 204:
            return int((end_time - start_time) * 1000)
    except requests.exceptions.RequestException:
        pass
    return -1

def get_external_ip(proxy_address, timeout=GET_EXTERNAL_IP_TIMEOUT):
    """Fetches the external IP address through a given proxy."""
    proxies = {'http': f'http://{proxy_address}', 'https': f'http://{proxy_address}'}
    try:
        response = requests.get(GET_EXTERNAL_IP_URL, proxies=proxies, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException:
        return "N/A"

def wait_for_proxy(host, port, timeout=WAIT_FOR_PROXY_TIMEOUT):
    """Waits for the proxy server to become available."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=WAIT_FOR_PROXY_INTERVAL):
                return True
        except (socket.timeout, ConnectionRefusedError):
            time.sleep(WAIT_FOR_PROXY_INTERVAL)
    return False

def run_single_url_test(config, settings={}):
    """Runs a URL test for a single server configuration using a temporary config file."""
    temp_proc = None
    temp_config_file = None
    try:
        full_config = generate_config_json(config, settings)
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as f:
            json.dump(full_config, f, indent=2)
            temp_config_file = f.name

        command = [get_resource_path('sing-box.exe'), 'run', '-c', temp_config_file]
        temp_proc = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)

        if wait_for_proxy(PROXY_HOST, PROXY_PORT):
            return url_test(PROXY_SERVER_ADDRESS)
        else:
            return -1
    except Exception as e:
        # Log the specific exception for debugging
        print(f"Error in run_single_url_test: {type(e).__name__}: {e}")
        return -1
    finally:
        if temp_proc:
            temp_proc.kill()
        if temp_config_file and os.path.exists(temp_config_file):
            try:
                os.remove(temp_config_file)
            except OSError:
                pass

def set_system_proxy(enable, settings, log_callback):
    """Sets or unsets the system-wide proxy settings for Windows."""
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as internet_settings:
            if enable:
                user_domains = settings.get("bypass_domains", "")
                bypass_list = PROXY_BYPASS
                if user_domains:
                    user_domains_semicolon = ";".join(d.strip() for d in user_domains.split(','))
                    bypass_list = f"{PROXY_BYPASS};{user_domains_semicolon}"

                winreg.SetValueEx(internet_settings, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(internet_settings, "ProxyServer", 0, winreg.REG_SZ, PROXY_SERVER_ADDRESS)
                winreg.SetValueEx(internet_settings, "ProxyOverride", 0, winreg.REG_SZ, bypass_list)
            else:
                winreg.SetValueEx(internet_settings, "ProxyEnable", 0, winreg.REG_DWORD, 0)
        
        ctypes.windll.Wininet.InternetSetOptionW(0, 39, 0, 0) # INTERNET_OPTION_SETTINGS_CHANGED
        ctypes.windll.Wininet.InternetSetOptionW(0, 37, 0, 0) # INTERNET_OPTION_REFRESH
    except Exception as e:
        if log_callback:
            log_callback(f"Failed to set system proxy: {type(e).__name__}: {e}", LogLevel.ERROR)

# --- Config Generation --- (Moved from SingboxManager)

def generate_config_json(server_config, settings):
    """Generates the complete sing-box configuration JSON."""
    dns_config, _ = _build_dns_config(settings)
    route_config = _build_route_config(settings)
    outbound_config = _build_outbound_config(server_config)

    return {
        "log": {"level": "info"},
        "experimental": {
            "cache_file": {"enabled": True, "path": "cache.db", "store_fakeip": True}
        },
        "dns": dns_config,
        "inbounds": [
            {"type": "socks", "tag": "socks-in", "listen": "127.0.0.1", "listen_port": 0},
            {"type": "http", "tag": "http-in", "listen": PROXY_HOST, "listen_port": PROXY_PORT}
        ],
        "outbounds": [
            {"type": "direct", "tag": "direct"},
            {"type": "block", "tag": "block"},
            outbound_config
        ],
        "route": route_config
    }

def _build_dns_config(settings):
    user_dns_str = settings.get("dns_servers")
    user_dns_list = [s.strip() for s in user_dns_str.split(',') if s.strip()]
    
    dns_servers = []
    if user_dns_list:
        dns_servers.append({"address": user_dns_list[0], "tag": "dns_proxy"})
        dns_servers.append({"address": user_dns_list[1] if len(user_dns_list) > 1 else "8.8.8.8", "tag": "dns_direct"})
    else:
        dns_servers.extend([
            {"address": "1.1.1.1", "tag": "dns_proxy"},
            {"address": "8.8.8.8", "tag": "dns_direct"}
        ])

    bypass_domains_str = settings.get("bypass_domains")
    bypass_domains_list = [d.strip() for d in bypass_domains_str.split(',') if d.strip()]
    non_geosite_bypass_domains = [d for d in bypass_domains_list if not d.startswith("domain:geosite:")]
    
    dns_rules = []
    if non_geosite_bypass_domains:
        dns_rules.append({"domain": non_geosite_bypass_domains, "server": "dns_direct"})

    return {
        "servers": dns_servers,
        "rules": dns_rules,
        "strategy": "prefer_ipv4",
        "final": "dns_proxy"
    }, dns_rules

def _build_route_config(settings):
    bypass_domains_str = settings.get("bypass_domains")
    bypass_domains_list = [d.strip() for d in bypass_domains_str.split(',') if d.strip()]

    bypass_ips_str = settings.get("bypass_ips")
    bypass_ips_list = [i.strip() for i in bypass_ips_str.split(',') if i.strip()]

    route_rules = [{"protocol": ["dns"], "outbound": "dns_proxy"}]
    rule_sets = []

    # GeoIP handling
    geoip_codes = [i.replace("geoip:", "") for i in bypass_ips_list if i.startswith("geoip:")]
    ip_cidr_rules = [i for i in bypass_ips_list if not i.startswith("geoip:")]
    
    if "private" in geoip_codes:
        route_rules.append({"ip_is_private": True, "outbound": "direct"})
        geoip_codes.remove("private")

    if geoip_codes:
        rule_set_tags = [f"geoip-{code}" for code in geoip_codes]
        route_rules.append({"rule_set": rule_set_tags, "outbound": "direct"})
        for code in geoip_codes:
            url = GEOIP_RULE_SET_URL.format(code=code)
            if code == 'ir':
                url = IRAN_GEOIP_RULE_SET_URL
            rule_sets.append({"tag": f"geoip-{code}", "type": "remote", "format": "binary", "url": url, "download_detour": "direct"})

    if ip_cidr_rules:
        route_rules.append({"ip_cidr": ip_cidr_rules, "outbound": "direct"})

    # Geosite handling
    geosite_domains = [d.replace("domain:geosite:", "") for d in bypass_domains_list if d.startswith("domain:geosite:")]
    other_domains = [d for d in bypass_domains_list if not d.startswith("domain:geosite:")]

    if geosite_domains:
        geosite_rule_set_tags = [f"geosite-{code}" for code in geosite_domains]
        route_rules.append({"rule_set": geosite_rule_set_tags, "outbound": "direct"})
        for code in geosite_domains:
            url = GEOSITE_RULE_SET_URL.format(code=code)
            if code == 'ir' or code == 'tld-ir':
                url = IRAN_GEOSITE_RULE_SET_URL
            rule_sets.append({"tag": f"geosite-{code}", "type": "remote", "format": "binary", "url": url, "download_detour": "direct"})

    if other_domains:
        route_rules.append({"domain": other_domains, "outbound": "direct"})

    route_rules.append({"protocol": ["quic"], "outbound": "block"})

    return {
        "rules": route_rules,
        "rule_set": rule_sets,
        "final": "proxy-out"
    }

def _build_outbound_config(server_config):
    protocol = server_config.get("protocol")
    sni_value = server_config.get("sni") or server_config.get("server")

    outbound = {
        "type": protocol,
        "tag": "proxy-out",
        "server": server_config.get("server"),
        "server_port": server_config.get("port"),
    }

    if protocol == "vless":
        outbound.update({"uuid": server_config.get("uuid")})
        if server_config.get("tls_enabled"):
            tls_config = {"enabled": True, "server_name": sni_value, "insecure": True, "alpn": ["h2", "http/1.1"]}
            if fingerprint := server_config.get("fp"):
                tls_config["utls"] = {"enabled": True, "fingerprint": fingerprint}
            outbound["tls"] = tls_config
        if server_config.get("flow") and server_config.get("transport") != "ws":
            outbound["flow"] = server_config.get("flow")
        if server_config.get("transport") == "ws":
            outbound["transport"] = {"type": "ws", "path": server_config.get("ws_path", "/"), "headers": {"Host": sni_value}}

    elif protocol == "vmess":
        outbound.update({
            "uuid": server_config.get("uuid"),
            "security": server_config.get("security", "auto"),
            "alter_id": int(server_config.get("aid", 0)),
            "tls": {"enabled": server_config.get("tls_enabled"), "server_name": sni_value, "insecure": True}
        })
        if server_config.get("transport") == "ws":
            outbound["transport"] = {"type": "ws", "path": server_config.get("ws_path", "/"), "headers": {"Host": server_config.get("ws_host") or sni_value}}

    elif protocol == "shadowsocks":
        outbound.update({
            "method": server_config.get("method"),
            "password": server_config.get("password")
        })

    return outbound

# --- Link Parsers ---

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
        remarks = unquote(parsed_url.fragment) if parsed_url.fragment else "Unnamed"
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
            "ws_path": query_params.get("path", [""])[0]
        }
    except Exception as e:
        print(f"Error parsing VLESS link: {type(e).__name__}: {e}")
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
    except (json.JSONDecodeError, binascii.Error, ValueError):
        return None

def parse_shadowsocks_link(link):
    try:
        parsed_url = urlparse(link)
        remarks = unquote(parsed_url.fragment) if parsed_url.fragment else "Unnamed"

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
    except (binascii.Error, ValueError):
        return None