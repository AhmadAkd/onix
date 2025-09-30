"""
Traffic Management Service
مدیریت پیشرفته ترافیک و Load Balancing
"""

import threading
import time
import statistics
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from collections import deque, defaultdict
from constants import LogLevel
import random


class TrafficPriority(Enum):
    """اولویت ترافیک"""

    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


class LoadBalancingStrategy(Enum):
    """استراتژی‌های Load Balancing"""

    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_RESPONSE_TIME = "least_response_time"
    RANDOM = "random"
    IP_HASH = "ip_hash"


@dataclass
class TrafficRule:
    """قانون ترافیک"""

    name: str
    priority: TrafficPriority
    source_pattern: str
    destination_pattern: str
    bandwidth_limit: int  # KB/s
    enabled: bool = True
    created_at: float = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


@dataclass
class ServerStats:
    """آمار سرور"""

    server_id: str
    active_connections: int = 0
    total_requests: int = 0
    response_time: float = 0.0
    bandwidth_usage: float = 0.0
    error_rate: float = 0.0
    last_updated: float = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = time.time()


@dataclass
class TrafficMetrics:
    """معیارهای ترافیک"""

    timestamp: float
    total_bandwidth: float
    active_connections: int
    requests_per_second: float
    average_response_time: float
    error_rate: float


class TrafficShaping:
    """شکل‌دهی ترافیک"""

    def __init__(self):
        self.rules: List[TrafficRule] = []
        self.bandwidth_usage: Dict[str, float] = defaultdict(float)
        self.is_active = False
        self._lock = threading.Lock()

    def add_rule(self, rule: TrafficRule):
        """اضافه کردن قانون ترافیک"""
        with self._lock:
            self.rules.append(rule)
            self.rules.sort(key=lambda x: x.priority.value)
            print(f"[{LogLevel.INFO}] Traffic rule added: {rule.name}")

    def remove_rule(self, rule_name: str):
        """حذف قانون ترافیک"""
        with self._lock:
            self.rules = [r for r in self.rules if r.name != rule_name]
            print(f"[{LogLevel.INFO}] Traffic rule removed: {rule_name}")

    def apply_shaping(
        self, connection_id: str, data_size: int, source: str, destination: str
    ) -> bool:
        """اعمال شکل‌دهی ترافیک"""
        with self._lock:
            for rule in self.rules:
                if not rule.enabled:
                    continue

                # بررسی تطبیق الگوها
                if self._matches_pattern(
                    source, rule.source_pattern
                ) and self._matches_pattern(destination, rule.destination_pattern):

                    # بررسی محدودیت پهنای باند
                    current_usage = self.bandwidth_usage.get(connection_id, 0)
                    if current_usage + data_size > rule.bandwidth_limit:
                        print(
                            f"[{LogLevel.WARNING}] Bandwidth limit exceeded for {rule.name}"
                        )
                        return False

                    # به‌روزرسانی استفاده از پهنای باند
                    self.bandwidth_usage[connection_id] = current_usage + data_size
                    return True

        return True

    def _matches_pattern(self, text: str, pattern: str) -> bool:
        """بررسی تطبیق الگو"""
        if pattern == "*":
            return True
        return pattern in text

    def reset_usage(self):
        """بازنشانی استفاده از پهنای باند"""
        with self._lock:
            self.bandwidth_usage.clear()
            print(f"[{LogLevel.INFO}] Bandwidth usage reset")


class LoadBalancer:
    """Load Balancer پیشرفته"""

    def __init__(self):
        self.servers: Dict[str, ServerStats] = {}
        self.strategy = LoadBalancingStrategy.ROUND_ROBIN
        self.current_index = 0
        self.is_active = False
        self._lock = threading.Lock()
        self._request_history = deque(maxlen=1000)

    def add_server(self, server_id: str, weight: int = 1):
        """اضافه کردن سرور"""
        with self._lock:
            self.servers[server_id] = ServerStats(server_id=server_id)
            print(f"[{LogLevel.INFO}] Server added to load balancer: {server_id}")

    def remove_server(self, server_id: str):
        """حذف سرور"""
        with self._lock:
            if server_id in self.servers:
                del self.servers[server_id]
                print(
                    f"[{LogLevel.INFO}] Server removed from load balancer: {server_id}"
                )

    def update_server_stats(self, server_id: str, stats: Dict[str, Any]):
        """به‌روزرسانی آمار سرور"""
        with self._lock:
            if server_id in self.servers:
                server = self.servers[server_id]
                server.active_connections = stats.get(
                    "active_connections", server.active_connections
                )
                server.total_requests = stats.get(
                    "total_requests", server.total_requests
                )
                server.response_time = stats.get("response_time", server.response_time)
                server.bandwidth_usage = stats.get(
                    "bandwidth_usage", server.bandwidth_usage
                )
                server.error_rate = stats.get("error_rate", server.error_rate)
                server.last_updated = time.time()

    def select_server(self, client_ip: str = None) -> Optional[str]:
        """انتخاب سرور بر اساس استراتژی"""
        with self._lock:
            if not self.servers:
                return None

            available_servers = [s for s in self.servers.values() if s.error_rate < 0.5]
            if not available_servers:
                return None

            if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
                return self._round_robin_selection(available_servers)
            elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
                return self._least_connections_selection(available_servers)
            elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
                return self._weighted_round_robin_selection(available_servers)
            elif self.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
                return self._least_response_time_selection(available_servers)
            elif self.strategy == LoadBalancingStrategy.RANDOM:
                return self._random_selection(available_servers)
            elif self.strategy == LoadBalancingStrategy.IP_HASH:
                return self._ip_hash_selection(available_servers, client_ip)

            return available_servers[0].server_id

    def _round_robin_selection(self, servers: List[ServerStats]) -> str:
        """انتخاب Round Robin"""
        if not servers:
            return None

        server = servers[self.current_index % len(servers)]
        self.current_index += 1
        return server.server_id

    def _least_connections_selection(self, servers: List[ServerStats]) -> str:
        """انتخاب کمترین اتصالات"""
        if not servers:
            return None

        return min(servers, key=lambda s: s.active_connections).server_id

    def _weighted_round_robin_selection(self, servers: List[ServerStats]) -> str:
        """انتخاب Round Robin وزنی"""
        if not servers:
            return None

        # شبیه‌سازی وزن بر اساس عملکرد
        weights = []
        for server in servers:
            weight = max(1, int(100 - server.error_rate * 100))
            weights.append(weight)

        total_weight = sum(weights)
        if total_weight == 0:
            return servers[0].server_id

        # انتخاب تصادفی بر اساس وزن
        rand = random.uniform(0, total_weight)
        current_weight = 0

        for i, weight in enumerate(weights):
            current_weight += weight
            if rand <= current_weight:
                return servers[i].server_id

        return servers[-1].server_id

    def _least_response_time_selection(self, servers: List[ServerStats]) -> str:
        """انتخاب کمترین زمان پاسخ"""
        if not servers:
            return None

        return min(servers, key=lambda s: s.response_time).server_id

    def _random_selection(self, servers: List[ServerStats]) -> str:
        """انتخاب تصادفی"""
        if not servers:
            return None

        return random.choice(servers).server_id

    def _ip_hash_selection(self, servers: List[ServerStats], client_ip: str) -> str:
        """انتخاب بر اساس هش IP"""
        if not servers or not client_ip:
            return servers[0].server_id if servers else None

        hash_value = hash(client_ip) % len(servers)
        return servers[hash_value].server_id

    def record_request(self, server_id: str, response_time: float, success: bool):
        """ثبت درخواست"""
        with self._lock:
            if server_id in self.servers:
                server = self.servers[server_id]
                server.total_requests += 1
                server.response_time = (server.response_time + response_time) / 2

                if not success:
                    server.error_rate = (server.error_rate + 1) / 2

                server.last_updated = time.time()

            # ثبت در تاریخچه
            self._request_history.append(
                {
                    "timestamp": time.time(),
                    "server_id": server_id,
                    "response_time": response_time,
                    "success": success,
                }
            )

    def get_server_stats(self) -> Dict[str, ServerStats]:
        """دریافت آمار سرورها"""
        with self._lock:
            return self.servers.copy()

    def get_load_balancing_stats(self) -> Dict[str, Any]:
        """دریافت آمار Load Balancing"""
        with self._lock:
            total_requests = sum(s.total_requests for s in self.servers.values())
            total_connections = sum(s.active_connections for s in self.servers.values())
            avg_response_time = (
                statistics.mean([s.response_time for s in self.servers.values()])
                if self.servers
                else 0
            )
            avg_error_rate = (
                statistics.mean([s.error_rate for s in self.servers.values()])
                if self.servers
                else 0
            )

            return {
                "strategy": self.strategy.value,
                "total_servers": len(self.servers),
                "total_requests": total_requests,
                "total_connections": total_connections,
                "average_response_time": avg_response_time,
                "average_error_rate": avg_error_rate,
                "servers": {
                    sid: {
                        "active_connections": s.active_connections,
                        "total_requests": s.total_requests,
                        "response_time": s.response_time,
                        "error_rate": s.error_rate,
                    }
                    for sid, s in self.servers.items()
                },
            }


class TrafficAnalyzer:
    """تحلیلگر ترافیک"""

    def __init__(self):
        self.metrics_history: deque = deque(maxlen=1000)
        self.is_monitoring = False
        self._monitoring_thread = None
        self._stop_event = threading.Event()

    def start_monitoring(self):
        """شروع نظارت"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self._stop_event.clear()
        self._monitoring_thread = threading.Thread(
            target=self._monitor_traffic, daemon=True
        )
        self._monitoring_thread.start()
        print(f"[{LogLevel.INFO}] Traffic monitoring started")

    def stop_monitoring(self):
        """توقف نظارت"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        self._stop_event.set()

        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=5)

        print(f"[{LogLevel.INFO}] Traffic monitoring stopped")

    def _monitor_traffic(self):
        """نظارت بر ترافیک"""
        while not self._stop_event.is_set():
            try:
                # شبیه‌سازی جمع‌آوری معیارها
                metrics = TrafficMetrics(
                    timestamp=time.time(),
                    total_bandwidth=random.uniform(100, 1000),  # MB/s
                    active_connections=random.randint(50, 500),
                    requests_per_second=random.uniform(10, 100),
                    average_response_time=random.uniform(50, 200),  # ms
                    error_rate=random.uniform(0.01, 0.05),
                )

                self.metrics_history.append(metrics)

                time.sleep(5)  # جمع‌آوری هر 5 ثانیه

            except Exception as e:
                print(f"[{LogLevel.ERROR}] Traffic monitoring error: {e}")
                time.sleep(5)

    def get_traffic_analysis(self) -> Dict[str, Any]:
        """دریافت تحلیل ترافیک"""
        if not self.metrics_history:
            return {}

        recent_metrics = list(self.metrics_history)[-100:]  # آخرین 100 نمونه

        bandwidth_values = [m.total_bandwidth for m in recent_metrics]
        response_times = [m.average_response_time for m in recent_metrics]
        error_rates = [m.error_rate for m in recent_metrics]

        return {
            "current_bandwidth": bandwidth_values[-1] if bandwidth_values else 0,
            "average_bandwidth": (
                statistics.mean(bandwidth_values) if bandwidth_values else 0
            ),
            "peak_bandwidth": max(bandwidth_values) if bandwidth_values else 0,
            "average_response_time": (
                statistics.mean(response_times) if response_times else 0
            ),
            "peak_response_time": max(response_times) if response_times else 0,
            "average_error_rate": statistics.mean(error_rates) if error_rates else 0,
            "total_samples": len(recent_metrics),
            "trend": self._calculate_trend(bandwidth_values),
        }

    def _calculate_trend(self, values: List[float]) -> str:
        """محاسبه روند"""
        if len(values) < 2:
            return "stable"

        recent_avg = (
            statistics.mean(values[-10:])
            if len(values) >= 10
            else statistics.mean(values[-len(values) // 2 :])
        )
        older_avg = (
            statistics.mean(values[: len(values) // 2])
            if len(values) >= 4
            else values[0]
        )

        if recent_avg > older_avg * 1.1:
            return "increasing"
        elif recent_avg < older_avg * 0.9:
            return "decreasing"
        else:
            return "stable"


class TrafficManagementService:
    """سرویس مدیریت ترافیک"""

    def __init__(self, log_callback: Callable = None):
        self.log = log_callback or print
        self.traffic_shaping = TrafficShaping()
        self.load_balancer = LoadBalancer()
        self.traffic_analyzer = TrafficAnalyzer()
        self.is_running = False
        self._cleanup_timer = None

    def start(self):
        """شروع سرویس"""
        if self.is_running:
            return

        self.is_running = True
        self.traffic_analyzer.start_monitoring()
        self._start_cleanup_timer()
        self.log(f"[{LogLevel.INFO}] Traffic management service started")

    def stop(self):
        """توقف سرویس"""
        if not self.is_running:
            return

        self.is_running = False
        self.traffic_analyzer.stop_monitoring()
        self._stop_cleanup_timer()
        self.log(f"[{LogLevel.INFO}] Traffic management service stopped")

    def _start_cleanup_timer(self):
        """شروع تایمر پاکسازی"""
        self._cleanup_timer = threading.Timer(300, self._cleanup_old_data)  # هر 5 دقیقه
        self._cleanup_timer.daemon = True
        self._cleanup_timer.start()

    def _stop_cleanup_timer(self):
        """توقف تایمر پاکسازی"""
        if self._cleanup_timer:
            self._cleanup_timer.cancel()
            self._cleanup_timer = None

    def _cleanup_old_data(self):
        """پاکسازی داده‌های قدیمی"""
        try:
            # پاکسازی قوانین قدیمی
            current_time = time.time()
            old_rules = [
                r
                for r in self.traffic_shaping.rules
                if current_time - r.created_at > 86400
            ]  # 24 ساعت
            for rule in old_rules:
                self.traffic_shaping.remove_rule(rule.name)

            # بازنشانی استفاده از پهنای باند
            self.traffic_shaping.reset_usage()

            # راه‌اندازی مجدد تایمر
            if self.is_running:
                self._start_cleanup_timer()

        except Exception as e:
            self.log(f"[{LogLevel.ERROR}] Cleanup error: {e}")

    def add_traffic_rule(self, rule: TrafficRule):
        """اضافه کردن قانون ترافیک"""
        self.traffic_shaping.add_rule(rule)

    def remove_traffic_rule(self, rule_name: str):
        """حذف قانون ترافیک"""
        self.traffic_shaping.remove_rule(rule_name)

    def add_server_to_balancer(self, server_id: str, weight: int = 1):
        """اضافه کردن سرور به Load Balancer"""
        self.load_balancer.add_server(server_id, weight)

    def remove_server_from_balancer(self, server_id: str):
        """حذف سرور از Load Balancer"""
        self.load_balancer.remove_server(server_id)

    def set_load_balancing_strategy(self, strategy: LoadBalancingStrategy):
        """تنظیم استراتژی Load Balancing"""
        self.load_balancer.strategy = strategy
        self.log(f"[{LogLevel.INFO}] Load balancing strategy set to: {strategy.value}")

    def select_best_server(self, client_ip: str = None) -> Optional[str]:
        """انتخاب بهترین سرور"""
        return self.load_balancer.select_server(client_ip)

    def record_request(self, server_id: str, response_time: float, success: bool):
        """ثبت درخواست"""
        self.load_balancer.record_request(server_id, response_time, success)

    def get_service_status(self) -> Dict[str, Any]:
        """دریافت وضعیت سرویس"""
        return {
            "is_running": self.is_running,
            "traffic_rules_count": len(self.traffic_shaping.rules),
            "load_balancer_stats": self.load_balancer.get_load_balancing_stats(),
            "traffic_analysis": self.traffic_analyzer.get_traffic_analysis(),
        }

    def cleanup(self):
        """پاکسازی منابع"""
        self.stop()
        self.traffic_shaping.reset_usage()
        self.log(f"[{LogLevel.INFO}] Traffic management service cleaned up")


# نمونه سراسری
_traffic_service = None


def get_traffic_service() -> TrafficManagementService:
    """دریافت نمونه سراسری سرویس ترافیک"""
    global _traffic_service
    if _traffic_service is None:
        _traffic_service = TrafficManagementService()
    return _traffic_service
