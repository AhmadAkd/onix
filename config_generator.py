from constants import (
    GEOIP_RULE_SET_URL,
    GEOSITE_RULE_SET_URL,
    IRAN_GEOIP_RULE_SET_URL,
    IRAN_GEOSITE_RULE_SET_URL,
    PROXY_HOST,
    PROXY_PORT,
)


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
            {
                "type": "socks",
                "tag": "socks-in",
                "listen": "127.0.0.1",
                "listen_port": 0,
            },
            {
                "type": "http",
                "tag": "http-in",
                "listen": PROXY_HOST,
                "listen_port": PROXY_PORT,
            },
        ],
        "outbounds": [
            {"type": "direct", "tag": "direct"},
            {"type": "block", "tag": "block"},
            outbound_config,
        ],
        "route": route_config,
    }


def _build_dns_config(settings):
    user_dns_str = settings.get("dns_servers")
    user_dns_list = [s.strip() for s in user_dns_str.split(",") if s.strip()]

    dns_servers = []
    if user_dns_list:
        dns_servers.append({"address": user_dns_list[0], "tag": "dns_proxy"})
        dns_servers.append(
            {
                "address": user_dns_list[1] if len(user_dns_list) > 1 else "8.8.8.8",
                "tag": "dns_direct",
            }
        )
    else:
        dns_servers.extend(
            [
                {"address": "1.1.1.1", "tag": "dns_proxy"},
                {"address": "8.8.8.8", "tag": "dns_direct"},
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
        dns_rules.append({"domain": non_geosite_bypass_domains, "server": "dns_direct"})

    return {
        "servers": dns_servers,
        "rules": dns_rules,
        "strategy": "prefer_ipv4",
        "final": "dns_proxy",
    }, dns_rules


def _build_route_config(settings):
    bypass_domains_str = settings.get("bypass_domains")
    bypass_domains_list = [
        d.strip() for d in bypass_domains_str.split(",") if d.strip()
    ]

    bypass_ips_str = settings.get("bypass_ips")
    bypass_ips_list = [i.strip() for i in bypass_ips_str.split(",") if i.strip()]

    route_rules = []
    rule_sets = []

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
                route_rules.append({"ip_cidr": rule_value, "outbound": outbound_tag})
            elif rule_type == "process":
                route_rules.append(
                    {"process_name": rule_value, "outbound": outbound_tag}
                )
            elif rule_type == "geosite":
                rule_set_tag = f"geosite-{rule_value}"
                route_rules.append({"rule_set": rule_set_tag, "outbound": outbound_tag})
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
                route_rules.append({"rule_set": rule_set_tag, "outbound": outbound_tag})
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

    route_rules.append(
        {"protocol": ["dns"], "outbound": "dns_proxy"}
    )  # Add default DNS rule after custom rules

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
        route_rules.append({"rule_set": geosite_rule_set_tags, "outbound": "direct"})
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

    route_rules.append({"protocol": ["quic"], "outbound": "block"})

    return {"rules": route_rules, "rule_set": rule_sets, "final": "proxy-out"}


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
            tls_config = {
                "enabled": True,
                "server_name": sni_value,
                "insecure": True,
                "alpn": ["h2", "http/1.1"],
            }
            if fingerprint := server_config.get("fp"):
                tls_config["utls"] = {"enabled": True, "fingerprint": fingerprint}
            outbound["tls"] = tls_config
        if server_config.get("flow") and server_config.get("transport") != "ws":
            outbound["flow"] = server_config.get("flow")
        if server_config.get("transport") == "ws":
            outbound["transport"] = {
                "type": "ws",
                "path": server_config.get("ws_path", "/"),
                "headers": {"Host": sni_value},
            }

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

    elif protocol == "shadowsocks":
        outbound.update(
            {
                "method": server_config.get("method"),
                "password": server_config.get("password"),
            }
        )

    return outbound
