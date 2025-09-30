from constants import (
    XRAY_LOG_FILE,
    PROXY_HOST,
    PROXY_PORT,
)
from .base_generator import BaseConfigGenerator


class XrayConfigGenerator(BaseConfigGenerator):
    """Generates a configuration file for the Xray core."""

    def generate_test_config(self, servers, settings):
        """Generates an Xray config for testing multiple servers."""
        # For testing, DNS should resolve directly (AsIs).
        dns_config = self._build_dns_config(settings, use_proxy_dns=False)
        inbounds = []
        outbounds = [
            {"protocol": "freedom", "tag": "direct"},
            {"protocol": "blackhole", "tag": "block"},
        ]

        for i, server_config in enumerate(servers):
            port = 11000 + i
            inbound_tag = f"http-in-{i}"
            outbound_tag = f"proxy-out-{i}"

            # Create proper inbound configuration for Xray
            inbound_config = {
                "protocol": "http",
                "tag": inbound_tag,
                "listen": "127.0.0.1",
                "port": port,
                "settings": {
                    "allowTransparent": False
                },
                "sniffing": {
                    "enabled": False
                }
            }

            inbounds.append(inbound_config)
            outbounds.append(self._build_test_outbound_config(
                server_config, settings, tag=outbound_tag))

        # Create routing rules
        route_rules = []
        for i in range(len(servers)):
            route_rules.append({
                "inboundTag": [f"http-in-{i}"],
                "outboundTag": f"proxy-out-{i}"
            })

        routing_config = {
            "rules": route_rules,
            "domainStrategy": "AsIs"
        }

        return {
            "dns": dns_config,
            "inbounds": inbounds,
            "outbounds": outbounds,
            "routing": routing_config
        }

    def generate_config_json(self, server_config, settings):
        """Generates the complete Xray configuration JSON."""
        outbound_config = self._build_outbound_config(server_config, settings)
        routing_config = self._build_routing_config(settings)
        dns_config = self._build_dns_config(settings)

        return {
            "log": {
                "loglevel": "warning",
                "access": XRAY_LOG_FILE,
                "error": XRAY_LOG_FILE,
            },
            "inbounds": [
                {
                    "port": PROXY_PORT,
                    "listen": PROXY_HOST,
                    "protocol": "http",
                    "sniffing": {"enabled": True, "destOverride": ["http", "tls"]},
                    "tag": "http-in",
                },
                {
                    "port": 1080,  # Placeholder, will be replaced dynamically
                    "listen": "127.0.0.1",
                    "protocol": "socks",
                    "sniffing": {"enabled": True, "destOverride": ["http", "tls"]},
                    "tag": "socks-in",
                },
            ],
            "outbounds": [
                outbound_config,
                {"protocol": "freedom", "tag": "direct"},
                {"protocol": "blackhole", "tag": "block"},
            ],
            "routing": routing_config,
            "dns": dns_config,
        }

    def _build_dns_config(self, settings, use_proxy_dns=True):
        """Builds the DNS configuration for Xray."""
        user_dns_str = settings.get("dns_servers", "1.1.1.1,8.8.8.8")
        dns_servers = [s.strip() for s in user_dns_str.split(",") if s.strip()]
        dns_config = {"servers": dns_servers}
        # For the main config, route DNS through the proxy. For tests, resolve directly.
        if use_proxy_dns:
            dns_config["domainStrategy"] = "UseIP"
        return dns_config

    def _build_routing_config(self, settings):
        """Builds the routing configuration for Xray."""
        rules = []
        bypass_domains = settings.get("bypass_domains", "").split(',')
        bypass_ips = settings.get("bypass_ips", "").split(',')

        # Add bypass rules
        if bypass_domains:
            rules.append({
                "type": "field",
                "domain": [d.strip() for d in bypass_domains if d.strip()],
                "outboundTag": "direct"
            })
        if bypass_ips:
            rules.append({
                "type": "field",
                "ip": [i.strip() for i in bypass_ips if i.strip()],
                "outboundTag": "direct"
            })

        # Add custom rules
        for rule in settings.get("custom_routing_rules", []):
            outbound_tag = "proxy-out" if rule.get(
                "action") == "proxy" else rule.get("action")
            rules.append({
                "type": "field",
                rule.get("type"): [rule.get("value")],
                "outboundTag": outbound_tag
            })

        return {"rules": rules}

    def _build_test_outbound_config(self, server_config, settings, tag="proxy-out"):
        """Builds a lean outbound object for Xray testing, without sockopt."""
        protocol = server_config.get("protocol")
        outbound = {
            "protocol": protocol,
            "tag": tag,
            "settings": {},
            "streamSettings": {}
        }

        # Common server details
        server_details = {
            "address": server_config.get("server"),
            "port": server_config.get("port"),
        }

        if protocol == "vless":
            server_details["users"] = [{
                "id": server_config.get("uuid"),
                "flow": server_config.get("flow", "xtls-rprx-vision")
            }]
            outbound["settings"]["vnext"] = [server_details]

        elif protocol == "vmess":
            server_details["users"] = [{
                "id": server_config.get("uuid"),
                "alterId": server_config.get("alter_id", 0),
                "security": server_config.get("security", "auto")
            }]
            outbound["settings"]["vnext"] = [server_details]

        elif protocol == "trojan":
            server_details["password"] = server_config.get("password")
            outbound["settings"]["servers"] = [server_details]

        elif protocol == "shadowsocks":
            server_details["method"] = server_config.get("method")
            server_details["password"] = server_config.get("password")
            outbound["settings"]["servers"] = [server_details]

        # Stream settings (TLS, transport, etc.)
        if server_config.get("tls_enabled"):
            outbound["streamSettings"]["security"] = "tls"
            outbound["streamSettings"]["tlsSettings"] = {
                "serverName": server_config.get("sni") or server_config.get("server"),
                "allowInsecure": True
            }
            if fp := server_config.get("fp"):
                outbound["streamSettings"]["tlsSettings"]["fingerprint"] = fp

        transport = server_config.get("transport", "tcp")
        outbound["streamSettings"]["network"] = transport

        return outbound

    def _build_outbound_config(self, server_config, settings, tag="proxy-out"):
        """Builds the main outbound object for Xray."""
        protocol = server_config.get("protocol")
        outbound = {
            "protocol": protocol,
            "tag": tag,
            "settings": {},
            "streamSettings": {},
        }

        # Common server details
        server_details = {
            "address": server_config.get("server"),
            "port": server_config.get("port"),
        }

        if protocol == "vless":
            server_details["users"] = [{
                "id": server_config.get("uuid"),
                "flow": server_config.get("flow", "xtls-rprx-vision")
            }]
            outbound["settings"]["vnext"] = [server_details]

        elif protocol == "vmess":
            server_details["users"] = [{
                "id": server_config.get("uuid"),
                "alterId": server_config.get("alter_id", 0),
                "security": server_config.get("security", "auto")
            }]
            outbound["settings"]["vnext"] = [server_details]

        elif protocol == "trojan":
            server_details["password"] = server_config.get("password")
            outbound["settings"]["servers"] = [server_details]

        elif protocol == "shadowsocks":
            server_details["method"] = server_config.get("method")
            server_details["password"] = server_config.get("password")
            outbound["settings"]["servers"] = [server_details]

        # Stream settings (TLS, transport, etc.)
        if server_config.get("tls_enabled"):
            outbound["streamSettings"]["security"] = "tls"
            outbound["streamSettings"]["tlsSettings"] = {
                "serverName": server_config.get("sni") or server_config.get("server"),
                "allowInsecure": True
            }
            if fp := server_config.get("fp"):
                outbound["streamSettings"]["tlsSettings"]["fingerprint"] = fp

        transport = server_config.get("transport", "tcp")
        outbound["streamSettings"]["network"] = transport
        if transport == "ws":
            outbound["streamSettings"]["wsSettings"] = {
                "path": server_config.get("ws_path", "/"),
                "headers": {"Host": server_config.get("ws_host") or server_config.get("sni")}
            }

        # Mux settings
        if settings.get("mux_enabled"):
            outbound["mux"] = {"enabled": True, "concurrency": 8}

        return outbound
