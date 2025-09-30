import socket
import time
from typing import Callable, Optional

import requests

from constants import (
    TEST_RETRY_COUNT,
    TEST_RETRY_DELAY,
    TEST_ENDPOINTS,
)


def _should_stop(is_cancelled: Optional[Callable[[], bool]]) -> bool:
    return bool(is_cancelled and is_cancelled())


def direct_tcp(host: str, port: int, timeout: int = None) -> int:
    if timeout is None:
        timeout = TEST_ENDPOINTS["tcp"]["timeout"]

    start = time.time()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((host, port))
        return round((time.time() - start) * 1000)
    except Exception:
        return -1


def proxy_tcp_connect(
    proxy_address: str, host: str, port: int, timeout: int = None
) -> int:
    if timeout is None:
        timeout = TEST_ENDPOINTS["tcp"]["timeout"]

    start = time.time()
    try:
        proxy_host, proxy_port = proxy_address.split(":")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((proxy_host, int(proxy_port)))
            req = f"CONNECT {host}:{port} HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n"
            sock.sendall(req.encode())
            resp = sock.recv(1024)
            line = resp.split(b"\r\n", 1)[0]
            if not line.startswith(b"HTTP/") or b" 200" not in line:
                return -1
        return round((time.time() - start) * 1000)
    except Exception:
        return -1


def url_latency_via_proxy(
    proxy_address: str,
    url: str = None,
    timeout: int = None,
    retries: int = None,
    is_cancelled: Optional[Callable[[], bool]] = None,
) -> int:
    if url is None:
        url = TEST_ENDPOINTS["url"]["url"]
    if timeout is None:
        timeout = TEST_ENDPOINTS["url"]["timeout"]
    if retries is None:
        retries = TEST_RETRY_COUNT

    proxies = {"http": f"http://{proxy_address}", "https": f"http://{proxy_address}"}
    attempt = 0
    best = -1
    while attempt <= retries and not _should_stop(is_cancelled):
        attempt += 1
        try:
            start = time.time()
            r = requests.get(url, proxies=proxies, timeout=timeout)
            end = time.time()
            if r.status_code in (200, 204):
                elapsed = round((end - start) * 1000)
                if best == -1 or elapsed < best:
                    best = elapsed
        except requests.exceptions.RequestException:
            pass

        # Add delay between retries
        if attempt <= retries and not _should_stop(is_cancelled):
            time.sleep(TEST_RETRY_DELAY)

    return best
