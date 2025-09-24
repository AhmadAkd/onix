import base64
import json
import re
import binascii
from urllib.parse import urlparse, parse_qs, unquote


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
        remarks = re.sub(r"[\U0001F1E6-\U0001F1FF]", "", remarks).strip()
        group = "Default"
        delimiters = ["|", "-", "_", " "]
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
            "port": int(parsed_url.port),
            "uuid": parsed_url.username,
            "tls_enabled": query_params.get("security", [""])[0] == "tls",
            "sni": query_params.get("sni", [""])[0],
            "flow": query_params.get("flow", [""])[0],
            "fp": query_params.get("fp", [""])[0],
            "transport": query_params.get("type", ["tcp"])[0],
            "ws_path": query_params.get("path", [""])[0],
        }
    except (ValueError, TypeError) as e:
        print(f"Error parsing VLESS link: {type(e).__name__}: {e}")
        return None


def parse_vmess_link(link):
    try:
        base64_str = link.replace("vmess://", "")
        base64_str += "=" * (-len(base64_str) % 4)
        decoded_str = base64.b64decode(base64_str).decode("utf-8")
        vmess_config = json.loads(decoded_str)

        remarks = vmess_config.get("ps", "Unnamed")
        group = "Default"
        delimiters = ["|", "-", "_", " "]
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
            "ws_host": vmess_config.get("host", ""),
        }
    except (json.JSONDecodeError, binascii.Error, ValueError):
        return None


def parse_shadowsocks_link(link):
    try:
        parsed_url = urlparse(link)
        remarks = unquote(parsed_url.fragment) if parsed_url.fragment else "Unnamed"

        group = "Default"
        delimiters = ["|", "-", "_", " "]
        for d in delimiters:
            if d in remarks:
                group = remarks.split(d)[0].strip()
                break

        user_info_b64 = parsed_url.username
        user_info_b64 += "=" * (-len(user_info_b64) % 4)
        decoded_user_info = base64.b64decode(user_info_b64).decode("utf-8")

        method, password = decoded_user_info.split(":", 1)

        return {
            "name": remarks,
            "group": group,
            "protocol": "shadowsocks",
            "server": parsed_url.hostname,
            "port": int(parsed_url.port),
            "method": method,
            "password": password,
        }
    except (binascii.Error, ValueError):
        return None
