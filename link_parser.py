import base64
import json
import re
import binascii
import configparser
from urllib.parse import urlparse, parse_qs, unquote
import uuid


def parse_server_link(link):
    """Parses VLESS, Vmess, Shadowsocks, Trojan, TUIC, or Hysteria2 subscription links."""
    if link.startswith("vless://"):
        return parse_vless_link(link)
    elif link.startswith("vmess://"):
        return parse_vmess_link(link)
    elif link.startswith("ss://"):
        return parse_shadowsocks_link(link)
    elif link.startswith("trojan://"):
        return parse_trojan_link(link)
    elif link.startswith("tuic://"):
        return parse_tuic_link(link)
    elif link.startswith("hysteria2://") or link.startswith("hy2://"):
        return parse_hysteria2_link(link)
    elif link.startswith("ssh://"):
        return parse_ssh_link(link)
    return None


def parse_wireguard_config(config_content, filename="WireGuard-Config"):
    try:
        config = configparser.ConfigParser()
        config.read_string(config_content)

        interface = config["Interface"]
        peer = config["Peer"]

        # Extract endpoint and separate server/port
        endpoint = peer.get("Endpoint", "").strip()
        server, port_str = (endpoint.rsplit(":", 1) + ["51820"])[:2]
        port = int(port_str)

        # Take the first address from the list
        local_address = interface.get("Address", "").split(",")[0].strip()

        return {
            "id": str(uuid.uuid4()),
            "name": filename,  # Use filename as the default name
            "group": "WireGuard",
            "protocol": "wireguard",
            "server": server,
            "port": port,
            "private_key": interface.get("PrivateKey", "").strip(),
            "local_address": local_address,
            "public_key": peer.get("PublicKey", "").strip(),
            "preshared_key": peer.get("PresharedKey", "").strip(),
            # For simplicity, use peer AllowedIPs, default to full tunnel
            "allowed_ips": peer.get("AllowedIPs", "0.0.0.0/0, ::/0").strip()
        }
    except (configparser.Error, ValueError, KeyError) as e:
        print(f"Error parsing WireGuard config: {type(e).__name__}: {e}")
        return None


def parse_vless_link(link):
    try:
        parsed_url = urlparse(link)

        if not parsed_url.username or not parsed_url.hostname:
            return None

        remarks = unquote(
            parsed_url.fragment) if parsed_url.fragment else "Unnamed"
        remarks = re.sub(r"[\U0001F1E6-\U0001F1FF]", "", remarks).strip()
        group = "Default"
        delimiters = ["|", "-", "_", " "]
        for d in delimiters:
            if d in remarks:
                group = remarks.split(d)[0].strip()
                break
        query_params = parse_qs(parsed_url.query)

        security = query_params.get("security", [""])[0]
        is_tls_enabled = security in ("tls", "reality")
        tls_type = "reality" if security == "reality" else (
            "tls" if security == "tls" else "")

        # For REALITY, enforce required params (publicKey and sni)
        public_key = query_params.get("publicKey", [""])[0]
        short_id = query_params.get("shortId", [""])[0]
        sni = query_params.get("sni", [""])[0]

        if security == "reality":
            if not public_key or not sni:
                return None

        result = {
            "id": str(uuid.uuid4()),
            "name": remarks,
            "group": group,
            "protocol": "vless",
            "server": parsed_url.hostname,
            "port": int(parsed_url.port),
            "uuid": parsed_url.username,
            "tls_enabled": is_tls_enabled,
            "sni": sni,
            "flow": query_params.get("flow", [""])[0],
            "fp": query_params.get("fp", [""])[0],
            "transport": query_params.get("type", ["tcp"])[0],
            "ws_path": query_params.get("path", [""])[0],
        }

        if tls_type:
            result["tls_type"] = tls_type
        if security == "reality":
            result["public_key"] = public_key
            if short_id:
                result["short_id"] = short_id

        return result
    except (ValueError, TypeError) as e:
        print(f"Error parsing VLESS link: {type(e).__name__}: {e}")
        return None


def parse_vmess_link(link):
    try:
        base64_str = link.replace("vmess://", "")
        base64_str += "=" * (-len(base64_str) % 4)
        decoded_str = base64.b64decode(base64_str).decode("utf-8")
        vmess_config = json.loads(decoded_str)

        if not vmess_config.get("add") or not vmess_config.get("id"):
            return None

        remarks = vmess_config.get("ps", "Unnamed")
        group = "Default"
        delimiters = ["|", "-", "_", " "]
        for d in delimiters:
            if d in remarks:
                group = remarks.split(d)[0].strip()
                break

        return {
            "id": str(uuid.uuid4()),
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
        remarks = unquote(
            parsed_url.fragment) if parsed_url.fragment else "Unnamed"

        group = "Default"
        delimiters = ["|", "-", "_", " "]
        for d in delimiters:
            if d in remarks:
                group = remarks.split(d)[0].strip()
                break

        if not parsed_url.username:
            return None

        user_info_b64 = parsed_url.username
        user_info_b64 += "=" * (-len(user_info_b64) % 4)
        decoded_user_info = base64.b64decode(user_info_b64).decode("utf-8")

        method, password = decoded_user_info.split(":", 1)

        return {
            "id": str(uuid.uuid4()),
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


def parse_trojan_link(link):
    try:
        parsed_url = urlparse(link)
        remarks = unquote(
            parsed_url.fragment) if parsed_url.fragment else "Unnamed"
        remarks = re.sub(r"[\U0001F1E6-\U0001F1FF]", "", remarks).strip()
        group = "Default"
        delimiters = ["|", "-", "_", " "]
        for d in delimiters:
            if d in remarks:
                group = remarks.split(d)[0].strip()
                break
        query_params = parse_qs(parsed_url.query)
        return {
            "id": str(uuid.uuid4()),
            "name": remarks,
            "group": group,
            "protocol": "trojan",
            "server": parsed_url.hostname,
            "port": int(parsed_url.port),
            "password": parsed_url.username,
            "sni": query_params.get("sni", [""])[0],
            "fp": query_params.get("fp", [""])[0],
        }
    except (ValueError, TypeError) as e:
        print(f"Error parsing Trojan link: {type(e).__name__}: {e}")
        return None


def parse_reality_link(link):
    """Parses a VLESS link that uses security=reality.

    Returns the same schema as parse_vless_link when security=reality,
    otherwise returns None.
    """
    try:
        parsed_url = urlparse(link)
        query_params = parse_qs(parsed_url.query)
        if query_params.get("security", [""])[0] != "reality":
            return None
        return parse_vless_link(link)
    except Exception:
        return None


def parse_tuic_link(link):
    try:
        parsed_url = urlparse(link)
        remarks = unquote(
            parsed_url.fragment) if parsed_url.fragment else "Unnamed"
        remarks = re.sub(r"[\U0001F1E6-\U0001F1FF]", "", remarks).strip()
        group = "Default"
        delimiters = ["|", "-", "_", " "]
        for d in delimiters:
            if d in remarks:
                group = remarks.split(d)[0].strip()
                break

        query_params = parse_qs(parsed_url.query)
        return {
            "id": str(uuid.uuid4()),
            "name": remarks,
            "group": group,
            "protocol": "tuic",
            "server": parsed_url.hostname,
            "port": int(parsed_url.port),
            "uuid": parsed_url.username,
            "password": parsed_url.password,
            "sni": query_params.get("sni", [None])[0],
            "congestion_control": query_params.get("congestion_control", ["bbr"])[0],
            "udp_relay_mode": query_params.get("udp_relay_mode", ["native"])[0],
            "alpn": query_params.get("alpn", [None])[0],
            "allow_insecure": query_params.get("allow_insecure", ["0"])[0] == "1",
        }
    except (ValueError, TypeError) as e:
        print(f"Error parsing TUIC link: {type(e).__name__}: {e}")
        return None


def parse_hysteria2_link(link):
    try:
        parsed_url = urlparse(link)
        remarks = unquote(
            parsed_url.fragment) if parsed_url.fragment else "Unnamed"
        remarks = re.sub(r"[\U0001F1E6-\U0001F1FF]", "", remarks).strip()
        group = "Default"
        delimiters = ["|", "-", "_", " "]
        for d in delimiters:
            if d in remarks:
                group = remarks.split(d)[0].strip()
                break

        query_params = parse_qs(parsed_url.query)
        return {
            "id": str(uuid.uuid4()),
            "name": remarks,
            "group": group,
            "protocol": "hysteria2",
            "server": parsed_url.hostname,
            "port": int(parsed_url.port or 443),
            "password": parsed_url.username or "",
            "sni": query_params.get("sni", [None])[0],
            "insecure": query_params.get("insecure", ["0"])[0] == "1",
            "obfs": query_params.get("obfs", [None])[0],
            "obfs_password": query_params.get("obfs-password", [None])[0],
        }
    except (ValueError, TypeError) as e:
        print(f"Error parsing Hysteria2 link: {type(e).__name__}: {e}")
        return None


def parse_ssh_link(link):
    """Parses an SSH protocol link."""
    try:
        parsed_url = urlparse(link)
        remarks = unquote(
            parsed_url.fragment) if parsed_url.fragment else "Unnamed"
        remarks = re.sub(r"[\U0001F1E6-\U0001F1FF]", "", remarks).strip()
        group = "Default"
        delimiters = ["|", "-", "_", " "]
        for d in delimiters:
            if d in remarks:
                group = remarks.split(d)[0].strip()
                break

        return {
            "id": str(uuid.uuid4()),
            "name": remarks,
            "group": group,
            "protocol": "ssh",
            "server": parsed_url.hostname,
            "port": int(parsed_url.port or 22),
            "user": parsed_url.username,
            "password": parsed_url.password,
        }
    except (ValueError, TypeError) as e:
        print(f"Error parsing SSH link: {type(e).__name__}: {e}")
        return None


def generate_server_link(config):
    """Generates a server link from a server configuration dictionary."""
    protocol = config.get("protocol")
    if protocol == "vless":
        return _generate_vless_link(config)
    elif protocol == "vmess":
        return _generate_vmess_link(config)
    elif protocol == "shadowsocks":
        return _generate_shadowsocks_link(config)
    elif protocol == "trojan":
        return _generate_trojan_link(config)
    elif protocol == "tuic":
        return _generate_tuic_link(config)
    elif protocol == "hysteria2":
        return _generate_hysteria2_link(config)
    elif protocol == "ssh":
        return _generate_ssh_link(config)
    return None


def _generate_vless_link(config):
    uuid = config.get("uuid", "")
    server = config.get("server", "")
    port = config.get("port", "")
    name = config.get("name", "Unnamed")

    query_params = {}
    if config.get("tls_enabled"):
        query_params["security"] = "tls"
    if config.get("sni"):
        query_params["sni"] = config["sni"]
    if config.get("flow"):
        query_params["flow"] = config["flow"]
    if config.get("fp"):
        query_params["fp"] = config["fp"]
    if config.get("transport") and config["transport"] != "tcp":
        query_params["type"] = config["transport"]
    if config.get("ws_path"):
        query_params["path"] = config["ws_path"]

    query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])

    link = f"vless://{uuid}@{server}:{port}"
    if query_string:
        link += f"?{query_string}"
    link += f"#{name}"
    return link


def _generate_ssh_link(config):
    user = config.get("user", "")
    password = config.get("password", "")
    server = config.get("server", "")
    port = config.get("port", "")
    name = config.get("name", "Unnamed")

    return f"ssh://{user}:{password}@{server}:{port}#{name}"


def _generate_vmess_link(config):
    vmess_config = {
        "v": "2",
        "ps": config.get("name", "Unnamed"),
        "add": config.get("server", ""),
        "port": str(config.get("port", 0)),
        "id": config.get("uuid", ""),
        "aid": str(config.get("alter_id", 0)),
        "scy": config.get("security", "auto"),
        "net": config.get("transport", "tcp"),
        "type": "none",  # Default for vmess
        "host": config.get("ws_host", ""),
        "path": config.get("ws_path", "/"),
        "tls": "tls" if config.get("tls_enabled") else "",
        "sni": config.get("sni", ""),
    }

    # Remove empty values to keep the link clean, but keep 'type' even if 'none'
    vmess_config_cleaned = {k: v for k,
                            v in vmess_config.items() if v or k == "type"}

    json_str = json.dumps(vmess_config_cleaned, ensure_ascii=False)
    encoded_str = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
    return f"vmess://{encoded_str}"


def _generate_shadowsocks_link(config):
    method = config.get("method", "")
    password = config.get("password", "")
    server = config.get("server", "")
    port = config.get("port", "")
    name = config.get("name", "Unnamed")

    user_info = f"{method}:{password}"
    encoded_user_info = (
        base64.b64encode(user_info.encode("utf-8")
                         ).decode("utf-8").replace("=", "")
    )

    link = f"ss://{encoded_user_info}@{server}:{port}"
    link += f"#{name}"
    return link


def _generate_trojan_link(config):
    password = config.get("password", "")
    server = config.get("server", "")
    port = config.get("port", "")
    name = config.get("name", "Unnamed")

    query_params = {}
    if config.get("sni"):
        query_params["sni"] = config["sni"]
    if config.get("fp"):
        query_params["fp"] = config["fp"]

    query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])

    link = f"trojan://{password}@{server}:{port}"
    if query_string:
        link += f"?{query_string}"
    link += f"#{name}"
    return link


def _generate_tuic_link(config):
    uuid = config.get("uuid", "")
    password = config.get("password", "")
    server = config.get("server", "")
    port = config.get("port", "")
    name = config.get("name", "Unnamed")

    query_params = {}
    if sni := config.get("sni"):
        query_params["sni"] = sni
    if congestion := config.get("congestion_control"):
        query_params["congestion_control"] = congestion
    if udp_relay := config.get("udp_relay_mode"):
        query_params["udp_relay_mode"] = udp_relay
    if alpn := config.get("alpn"):
        query_params["alpn"] = alpn
    if config.get("allow_insecure"):
        query_params["allow_insecure"] = "1"

    link = f"tuic://{uuid}:{password}@{server}:{port}"
    query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])

    if query_string:
        link += f"?{query_string}"
    link += f"#{name}"
    return link


def _generate_hysteria2_link(config):
    password = config.get("password", "")
    server = config.get("server", "")
    port = config.get("port", "")
    name = config.get("name", "Unnamed")

    query_params = {}
    if sni := config.get("sni"):
        query_params["sni"] = sni
    if config.get("insecure"):
        query_params["insecure"] = "1"
    if obfs := config.get("obfs"):
        query_params["obfs"] = obfs
    if obfs_pass := config.get("obfs_password"):
        query_params["obfs-password"] = obfs_pass

    query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])

    link = f"hysteria2://{password}@{server}:{port}"
    if query_string:
        link += f"?{query_string}"
    link += f"#{name}"
    return link
