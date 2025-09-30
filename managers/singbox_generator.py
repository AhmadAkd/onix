from constants import (
    GEOIP_RULE_SET_URL,
    GEOSITE_RULE_SET_URL,
    IRAN_GEOIP_RULE_SET_URL,
    IRAN_GEOSITE_RULE_SET_URL,
    STATS_API_PORT,
    PROXY_HOST,
    PROXY_PORT,
    SINGBOX_LOG_FILE,
)
from .base_generator import BaseConfigGenerator


class SingboxConfigGenerator(BaseConfigGenerator):

    def generate_test_config(self, servers, settings):
        """Generates a sing-box config for testing multiple servers."""
        # For testing, DNS should resolve directly, not through the proxy.
        # The "final" resolver must be a tag from the DNS servers list.
        dns_config, _ = self._build_dns_config(settings, final_resolver="dns_direct")
        inbounds = []
        outbounds = [
            {"type": "direct", "tag": "direct"},
            {"type": "block", "tag": "block"},
        ]

        for i, server_config in enumerate(servers):
            port = 11000 + i
            # Use HTTP inbound for tests because the tester performs HTTP URL requests
            # and HTTP CONNECT for TCP pings through the proxy.
            inbounds.append(
                {
                    "type": "http",
                    "tag": f"http-in-{i}",
                    "listen": "127.0.0.1",
                    "listen_port": port,
                }
            )
            outbounds.append(
                self._build_outbound_config(
                    server_config, settings, tag=f"proxy-out-{i}"
                )
            )

        route_rules = [
            {"inbound": f"http-in-{i}", "outbound": f"proxy-out-{i}"}
            for i in range(len(servers))
        ]
        route_config = {"rules": route_rules, "final": "direct"}

        return {
            "dns": dns_config,
            "inbounds": inbounds,
            "outbounds": outbounds,
            "route": route_config,
        }

    def generate_config_json(self, server_config, settings):
        """Generates the complete sing-box configuration JSON."""
        dns_config, _ = self._build_dns_config(settings)
        route_config = self._build_route_config(settings)

        # --- Outbound Generation Logic ---
        outbounds = [
            {"type": "direct", "tag": "direct"},
            {"type": "block", "tag": "block"},
        ]
        if server_config.get("is_chain"):
            # It's a chain configuration
            chain_outbounds = self._build_chained_outbounds(server_config, settings)
            outbounds.extend(chain_outbounds)
        else:
            # It's a single server configuration
            single_outbound = self._build_outbound_config(
                server_config, settings, tag="proxy-out"
            )
            outbounds.append(single_outbound)

        return {
            "log": {
                "level": "info",
                "output": SINGBOX_LOG_FILE,
            },
            "experimental": {
                "cache_file": {
                    "enabled": True,
                    "path": "cache.db",
                    "store_fakeip": True,
                },
                "stats": {"listen": PROXY_HOST, "listen_port": STATS_API_PORT},
            },
            "dns": dns_config,
            "inbounds": [
                *(
                    [
                        {
                            "type": "tun",
                            "tag": "tun-in",
                            "interface_name": "onix_tun",
                            "inet4_address": "172.19.0.1/24",
                            "mtu": 9000,
                            "auto_route": True,
                            "strict_route": True,
                            "endpoint_independent_nat": True,
                        }
                    ]
                    if settings.get("tun_enabled")
                    else []
                ),
                {
                    "type": "socks",
                    "tag": "socks-in",
                    "listen": "127.0.0.1",
                    "listen_port": 1080,  # Placeholder, will be replaced dynamically
                },
                {
                    "type": "http",
                    "tag": "http-in",
                    "listen": PROXY_HOST,
                    "listen_port": PROXY_PORT,
                },
            ],
            "outbounds": outbounds,
            "route": route_config,
        }

    def _build_dns_config(self, settings, final_resolver="proxy-out"):
        user_dns_str = settings.get("dns_servers")
        user_dns_list = [s.strip() for s in user_dns_str.split(",") if s.strip()]

        # The `servers` field must be an array of objects, each with a tag and address.
        dns_servers = []
        if user_dns_list:
            dns_servers.append({"tag": "dns-out", "address": user_dns_list[0]})
            dns_direct_address = (
                user_dns_list[1] if len(user_dns_list) > 1 else "8.8.8.8"
            )
            dns_servers.append({"tag": "dns_direct", "address": dns_direct_address})
        else:
            dns_servers.extend(
                [
                    {"tag": "dns-out", "address": "1.1.1.1"},
                    {"tag": "dns_direct", "address": "8.8.8.8"},
                ]
            )

        bypass_domains_str = settings.get("bypass_domains")
        bypass_domains_list = [
            d.strip() for d in bypass_domains_str.split(",") if d.strip()
        ]
        non_geosite_bypass_domains = [
            d for d in bypass_domains_list if not d.startswith("domain:geosite:")
        ]

        dns_rules = []
        if non_geosite_bypass_domains:
            dns_rules.append(
                {"domain": non_geosite_bypass_domains, "server": "dns_direct"}
            )

        return {
            "servers": dns_servers,
            "rules": dns_rules,
            "strategy": "prefer_ipv4",
            "final": final_resolver,
        }, dns_rules

    def _build_route_config(self, settings):
        bypass_domains_str = settings.get("bypass_domains")
        bypass_domains_list = [
            d.strip() for d in bypass_domains_str.split(",") if d.strip()
        ]

        bypass_ips_str = settings.get("bypass_ips")
        bypass_ips_list = [i.strip() for i in bypass_ips_str.split(",") if i.strip()]

        route_rules = []
        rule_sets = []

        # Add a rule to route DNS queries to the dns-out outbound
        route_rules.append({"protocol": ["dns"], "outbound": "dns"})

        # Add custom rules from settings
        custom_routing_rules = settings.get("custom_routing_rules", [])
        for rule in custom_routing_rules:
            rule_type = rule.get("type")
            rule_value = rule.get("value")
            rule_action = rule.get("action")

            if rule_type and rule_value and rule_action:
                outbound_tag = "proxy-out" if rule_action == "proxy" else rule_action

                if rule_type == "domain":
                    route_rules.append({"domain": rule_value, "outbound": outbound_tag})
                elif rule_type == "ip":
                    route_rules.append(
                        {"ip_cidr": rule_value, "outbound": outbound_tag}
                    )
                elif rule_type == "process":
                    route_rules.append(
                        {"process_name": rule_value, "outbound": outbound_tag}
                    )
                elif rule_type == "geosite":
                    rule_set_tag = f"geosite-{rule_value}"
                    route_rules.append(
                        {"rule_set": rule_set_tag, "outbound": outbound_tag}
                    )
                    # Add rule_set definition if not already present
                    if not any(rs.get("tag") == rule_set_tag for rs in rule_sets):
                        url = GEOSITE_RULE_SET_URL.format(code=rule_value)
                        if rule_value == "ir" or rule_value == "tld-ir":
                            url = IRAN_GEOSITE_RULE_SET_URL
                        rule_sets.append(
                            {
                                "tag": rule_set_tag,
                                "type": "remote",
                                "format": "binary",
                                "url": url,
                                "download_detour": "direct",
                            }
                        )
                elif rule_type == "geoip":
                    rule_set_tag = f"geoip-{rule_value}"
                    route_rules.append(
                        {"rule_set": rule_set_tag, "outbound": outbound_tag}
                    )
                    # Add rule_set definition if not already present
                    if not any(rs.get("tag") == rule_set_tag for rs in rule_sets):
                        url = GEOIP_RULE_SET_URL.format(code=rule_value)
                        if rule_value == "ir":
                            url = IRAN_GEOIP_RULE_SET_URL
                        rule_sets.append(
                            {
                                "tag": rule_set_tag,
                                "type": "remote",
                                "format": "binary",
                                "url": url,
                                "download_detour": "direct",
                            }
                        )

        # GeoIP handling
        geoip_codes = [
            i.replace("geoip:", "") for i in bypass_ips_list if i.startswith("geoip:")
        ]
        ip_cidr_rules = [i for i in bypass_ips_list if not i.startswith("geoip:")]

        if "private" in geoip_codes:
            route_rules.append({"ip_is_private": True, "outbound": "direct"})
            geoip_codes.remove("private")

        if geoip_codes:
            rule_set_tags = [f"geoip-{code}" for code in geoip_codes]
            route_rules.append({"rule_set": rule_set_tags, "outbound": "direct"})
            for code in geoip_codes:
                url = GEOIP_RULE_SET_URL.format(code=code)
                if code == "ir":
                    url = IRAN_GEOIP_RULE_SET_URL
                rule_sets.append(
                    {
                        "tag": f"geoip-{code}",
                        "type": "remote",
                        "format": "binary",
                        "url": url,
                        "download_detour": "direct",
                    }
                )

        if ip_cidr_rules:
            route_rules.append({"ip_cidr": ip_cidr_rules, "outbound": "direct"})

        # Geosite handling
        geosite_domains = [
            d.replace("domain:geosite:", "")
            for d in bypass_domains_list
            if d.startswith("domain:geosite:")
        ]
        other_domains = [
            d for d in bypass_domains_list if not d.startswith("domain:geosite:")
        ]

        if geosite_domains:
            geosite_rule_set_tags = [f"geosite-{code}" for code in geosite_domains]
            route_rules.append(
                {"rule_set": geosite_rule_set_tags, "outbound": "direct"}
            )
            for code in geosite_domains:
                url = GEOSITE_RULE_SET_URL.format(code=code)
                if code == "ir" or code == "tld-ir":
                    url = IRAN_GEOSITE_RULE_SET_URL
                rule_sets.append(
                    {
                        "tag": f"geosite-{code}",
                        "type": "remote",
                        "format": "binary",
                        "url": url,
                        "download_detour": "direct",
                    }
                )

        if other_domains:
            route_rules.append({"domain": other_domains, "outbound": "direct"})

        return {"rules": route_rules, "rule_set": rule_sets, "final": "proxy-out"}

    def _build_outbound_config(self, server_config, settings, tag="proxy-out"):
        protocol = server_config.get("protocol")
        sni_value = server_config.get("sni") or server_config.get("server")

        outbound = {
            "type": protocol if protocol != "reality" else "vless",
            "tag": tag,
            "server": server_config.get("server"),
            "server_port": server_config.get("port"),
        }

        if protocol == "vless":
            outbound.update({"uuid": server_config.get("uuid")})
            if server_config.get("tls_enabled"):
                tls_config = {
                    "enabled": True,
                    "server_name": sni_value,
                    "insecure": True,
                    "alpn": ["h2", "http/1.1"],
                }
                if fingerprint := server_config.get("fp"):
                    tls_config["utls"] = {"enabled": True, "fingerprint": fingerprint}
                if settings.get("tls_fragment_enabled"):
                    try:
                        size_str = settings.get("tls_fragment_size", "10-100")
                        sleep_str = settings.get("tls_fragment_sleep", "10-100")
                        size = [int(x.strip()) for x in size_str.split("-")]
                        sleep = [int(x.strip()) for x in sleep_str.split("-")]
                        if len(size) == 2 and len(sleep) == 2:
                            tls_config["fragment"] = {
                                "size": size,
                                "sleep": sleep,
                            }
                    except (ValueError, IndexError):
                        pass
                outbound["tls"] = tls_config
            if server_config.get("flow") and server_config.get("transport") != "ws":
                outbound["flow"] = server_config.get("flow")
            if server_config.get("transport") == "ws":
                outbound["transport"] = {
                    "type": "ws",
                    "path": server_config.get("ws_path", "/"),
                    "headers": {"Host": sni_value},
                }
            self._apply_mux_config(outbound, settings)

        elif protocol == "vmess":
            outbound.update(
                {
                    "uuid": server_config.get("uuid"),
                    "security": server_config.get("security", "auto"),
                    "alter_id": int(server_config.get("aid", 0)),
                    "tls": {
                        "enabled": server_config.get("tls_enabled"),
                        "server_name": sni_value,
                        "insecure": True,
                    },
                }
            )
            if server_config.get("transport") == "ws":
                outbound["transport"] = {
                    "type": "ws",
                    "path": server_config.get("ws_path", "/"),
                    "headers": {"Host": server_config.get("ws_host") or sni_value},
                }
            self._apply_mux_config(outbound, settings)

        elif protocol == "shadowsocks":
            outbound.update(
                {
                    "method": server_config.get("method"),
                    "password": server_config.get("password"),
                }
            )
            self._apply_mux_config(outbound, settings)

        elif protocol == "trojan":
            outbound.update({"password": server_config.get("password")})
            tls_config = {
                "enabled": True,
                "server_name": sni_value,
                "insecure": True,
            }
            if fingerprint := server_config.get("fp"):
                tls_config["utls"] = {"enabled": True, "fingerprint": fingerprint}
            if settings.get("tls_fragment_enabled"):
                try:
                    size_str = settings.get("tls_fragment_size", "10-100")
                    sleep_str = settings.get("tls_fragment_sleep", "10-100")
                    size = [int(x.strip()) for x in size_str.split("-")]
                    sleep = [int(x.strip()) for x in sleep_str.split("-")]
                    if len(size) == 2 and len(sleep) == 2:
                        tls_config["fragment"] = {
                            "size": size,
                            "sleep": sleep,
                        }
                except (ValueError, IndexError):
                    pass
            outbound["tls"] = tls_config
            self._apply_mux_config(outbound, settings)

        elif protocol == "tuic":
            outbound.update(
                {
                    "uuid": server_config.get("uuid"),
                    "password": server_config.get("password"),
                    "congestion_control": server_config.get(
                        "congestion_control", "bbr"
                    ),
                    "udp_relay_mode": server_config.get("udp_relay_mode", "native"),
                }
            )
            tls_config = {
                "enabled": True,
                "server_name": server_config.get("sni") or server_config.get("server"),
                "insecure": server_config.get("allow_insecure", False),
            }
            if alpn := server_config.get("alpn"):
                tls_config["alpn"] = [alpn]

            # Add uTLS fingerprint if available, defaulting to chrome
            tls_config["utls"] = {"enabled": True, "fingerprint": "chrome"}

            outbound["tls"] = tls_config

        elif protocol == "hysteria2":
            try:
                up_mbps = int(settings.get("hy2_up_mbps", 50))
                down_mbps = int(settings.get("hy2_down_mbps", 100))
            except (ValueError, TypeError):
                up_mbps = 50
                down_mbps = 100

            outbound.update(
                {
                    "password": server_config.get("password", ""),
                    "up_mbps": up_mbps,
                    "down_mbps": down_mbps,
                }
            )
            tls_config = {
                "enabled": True,
                "server_name": server_config.get("sni") or server_config.get("server"),
                "insecure": server_config.get("insecure", False),
            }
            outbound["tls"] = tls_config

            if server_config.get("obfs") and server_config.get("obfs_password"):
                outbound["obfs"] = {
                    "type": server_config.get("obfs"),
                    "password": server_config.get("obfs_password"),
                }

        elif protocol == "wireguard":
            # server and server_port are defined in peers, so remove them from the top level
            outbound.pop("server", None)
            outbound.pop("server_port", None)

            outbound.update(
                {
                    "local_address": [server_config.get("local_address")],
                    "private_key": server_config.get("private_key"),
                    "mtu": 1420,  # A common MTU for WireGuard
                    "peers": [
                        {
                            "server": server_config.get("server"),
                            "server_port": server_config.get("port"),
                            "public_key": server_config.get("public_key"),
                            "preshared_key": server_config.get("preshared_key"),
                            "allowed_ips": [
                                ip.strip()
                                for ip in server_config.get("allowed_ips", "").split(
                                    ","
                                )
                            ],
                        }
                    ],
                }
            )

        elif protocol == "ssh":
            outbound.update(
                {
                    "user": server_config.get("user"),
                    "password": server_config.get("password"),
                    # You can add more options like private_key if needed
                }
            )
            # SSH does not typically use multiplexing in this context

        return outbound

    def _build_chained_outbounds(self, chain_config, settings):
        """
        Builds a list of outbounds for a chain, including the 'chain' outbound itself.
        """
        all_outbounds = []
        node_tags = []
        all_servers_map = {
            s["id"]: s for s in self.parent.server_manager.get_all_servers()
        }

        node_ids = chain_config.get("nodes", [])

        for i, node_id in enumerate(node_ids):
            server_config = all_servers_map.get(node_id)
            if not server_config:
                continue  # Skip if server not found

            node_tag = f"chain-node-{i}-{server_config.get('name', 'node')[:8]}"
            node_tags.append(node_tag)

            # Build the individual outbound config for this node
            outbound_node = self._build_outbound_config(
                server_config, settings, tag=node_tag
            )
            all_outbounds.append(outbound_node)

        # Create the main 'chain' outbound that links them all
        chain_outbound = {
            "type": "chain",
            "tag": "proxy-out",  # This is the final outbound the router will use
            "outbounds": node_tags,
        }
        # Add the chain outbound at the beginning
        all_outbounds.insert(0, chain_outbound)

        return all_outbounds

    def _apply_mux_config(self, outbound, settings):
        if settings.get("mux_enabled"):
            try:
                max_streams = int(settings.get("mux_max_streams", 0))
            except (ValueError, TypeError):
                max_streams = 0

            outbound["multiplex"] = {
                "enabled": True,
                "protocol": settings.get("mux_protocol", "h2mux"),
                "max_streams": max_streams,
                "padding": settings.get("mux_padding", False),
            }
