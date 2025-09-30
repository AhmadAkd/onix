"""
Protocol Extensions Service
پشتیبانی از پروتکل‌های پیشرفته مانند QUIC، HTTP/3 و پروتکل‌های سفارشی
"""

import threading
import time
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from constants import LogLevel


class ProtocolType(Enum):
    """انواع پروتکل‌های پشتیبانی شده"""
    QUIC = "quic"
    HTTP3 = "http3"
    WEBSOCKET = "websocket"
    GRPC = "grpc"
    CUSTOM = "custom"


@dataclass
class ProtocolConfig:
    """پیکربندی پروتکل"""
    name: str
    protocol_type: ProtocolType
    enabled: bool = True
    priority: int = 0
    timeout: int = 30
    retry_count: int = 3
    custom_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.custom_params is None:
            self.custom_params = {}


@dataclass
class ConnectionMetrics:
    """معیارهای اتصال"""
    protocol: str
    latency: float
    bandwidth: float
    packet_loss: float
    jitter: float
    connection_time: float
    stability_score: float


class QUICManager:
    """مدیریت پروتکل QUIC"""

    def __init__(self):
        self.connections: Dict[str, Any] = {}
        self.config: Optional[ProtocolConfig] = None
        self.is_running = False
        self._lock = threading.Lock()

    def configure(self, config: ProtocolConfig):
        """پیکربندی QUIC"""
        self.config = config
        print(f"[{LogLevel.INFO}] QUIC configured: {config.name}")

    async def create_connection(self, host: str, port: int, server_name: str = None) -> Optional[Any]:
        """ایجاد اتصال QUIC"""
        try:
            # شبیه‌سازی اتصال QUIC
            connection_id = f"quic_{host}_{port}_{int(time.time())}"

            with self._lock:
                self.connections[connection_id] = {
                    'host': host,
                    'port': port,
                    'server_name': server_name,
                    'created_at': time.time(),
                    'status': 'connecting'
                }

            # شبیه‌سازی تأخیر اتصال
            await asyncio.sleep(0.1)

            with self._lock:
                self.connections[connection_id]['status'] = 'connected'

            print(f"[{LogLevel.INFO}] QUIC connection established: {host}:{port}")
            return connection_id

        except Exception as e:
            print(f"[{LogLevel.ERROR}] QUIC connection failed: {e}")
            return None

    def close_connection(self, connection_id: str):
        """بستن اتصال QUIC"""
        with self._lock:
            if connection_id in self.connections:
                self.connections[connection_id]['status'] = 'closed'
                del self.connections[connection_id]
                print(f"[{LogLevel.INFO}] QUIC connection closed: {connection_id}")

    def get_connection_metrics(self, connection_id: str) -> Optional[ConnectionMetrics]:
        """دریافت معیارهای اتصال"""
        with self._lock:
            if connection_id not in self.connections:
                return None

            conn = self.connections[connection_id]
            return ConnectionMetrics(
                protocol="QUIC",
                latency=50.0,  # شبیه‌سازی
                bandwidth=100.0,
                packet_loss=0.01,
                jitter=5.0,
                connection_time=time.time() - conn['created_at'],
                stability_score=0.95
            )


class HTTP3Manager:
    """مدیریت پروتکل HTTP/3"""

    def __init__(self):
        self.connections: Dict[str, Any] = {}
        self.config: Optional[ProtocolConfig] = None
        self._lock = threading.Lock()

    def configure(self, config: ProtocolConfig):
        """پیکربندی HTTP/3"""
        self.config = config
        print(f"[{LogLevel.INFO}] HTTP/3 configured: {config.name}")

    async def make_request(self, url: str, method: str = "GET", headers: Dict[str, str] = None) -> Optional[Dict[str, Any]]:
        """ارسال درخواست HTTP/3"""
        try:
            if headers is None:
                headers = {}

            # شبیه‌سازی درخواست HTTP/3
            request_id = f"http3_{int(time.time())}"

            with self._lock:
                self.connections[request_id] = {
                    'url': url,
                    'method': method,
                    'headers': headers,
                    'created_at': time.time(),
                    'status': 'pending'
                }

            # شبیه‌سازی تأخیر شبکه
            await asyncio.sleep(0.05)

            with self._lock:
                self.connections[request_id]['status'] = 'completed'

            print(f"[{LogLevel.INFO}] HTTP/3 request completed: {method} {url}")

            return {
                'status_code': 200,
                'headers': {'content-type': 'application/json'},
                'body': {'message': 'HTTP/3 response'},
                'request_id': request_id
            }

        except Exception as e:
            print(f"[{LogLevel.ERROR}] HTTP/3 request failed: {e}")
            return None

    def get_connection_metrics(self, request_id: str) -> Optional[ConnectionMetrics]:
        """دریافت معیارهای اتصال"""
        with self._lock:
            if request_id not in self.connections:
                return None

            conn = self.connections[request_id]
            return ConnectionMetrics(
                protocol="HTTP/3",
                latency=30.0,  # شبیه‌سازی
                bandwidth=150.0,
                packet_loss=0.005,
                jitter=3.0,
                connection_time=time.time() - conn['created_at'],
                stability_score=0.98
            )


class WebSocketManager:
    """مدیریت WebSocket"""

    def __init__(self):
        self.connections: Dict[str, Any] = {}
        self.config: Optional[ProtocolConfig] = None
        self._lock = threading.Lock()

    def configure(self, config: ProtocolConfig):
        """پیکربندی WebSocket"""
        self.config = config
        print(f"[{LogLevel.INFO}] WebSocket configured: {config.name}")

    async def connect(self, url: str, protocols: List[str] = None) -> Optional[str]:
        """اتصال WebSocket"""
        try:
            if protocols is None:
                protocols = []

            connection_id = f"ws_{int(time.time())}"

            with self._lock:
                self.connections[connection_id] = {
                    'url': url,
                    'protocols': protocols,
                    'created_at': time.time(),
                    'status': 'connecting'
                }

            # شبیه‌سازی تأخیر اتصال
            await asyncio.sleep(0.08)

            with self._lock:
                self.connections[connection_id]['status'] = 'connected'

            print(f"[{LogLevel.INFO}] WebSocket connected: {url}")
            return connection_id

        except Exception as e:
            print(f"[{LogLevel.ERROR}] WebSocket connection failed: {e}")
            return None

    async def send_message(self, connection_id: str, message: str) -> bool:
        """ارسال پیام WebSocket"""
        with self._lock:
            if connection_id not in self.connections:
                return False

            conn = self.connections[connection_id]
            if conn['status'] != 'connected':
                return False

        # شبیه‌سازی ارسال پیام
        await asyncio.sleep(0.01)
        print(f"[{LogLevel.INFO}] WebSocket message sent: {message[:50]}...")
        return True

    def close_connection(self, connection_id: str):
        """بستن اتصال WebSocket"""
        with self._lock:
            if connection_id in self.connections:
                self.connections[connection_id]['status'] = 'closed'
                del self.connections[connection_id]
                print(
                    f"[{LogLevel.INFO}] WebSocket connection closed: {connection_id}")


class CustomProtocolManager:
    """مدیریت پروتکل‌های سفارشی"""

    def __init__(self):
        self.protocols: Dict[str, ProtocolConfig] = {}
        self.connections: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def register_protocol(self, config: ProtocolConfig):
        """ثبت پروتکل سفارشی"""
        with self._lock:
            self.protocols[config.name] = config
            print(f"[{LogLevel.INFO}] Custom protocol registered: {config.name}")

    async def create_connection(self, protocol_name: str, host: str, port: int, params: Dict[str, Any] = None) -> Optional[str]:
        """ایجاد اتصال با پروتکل سفارشی"""
        try:
            with self._lock:
                if protocol_name not in self.protocols:
                    return None

            connection_id = f"custom_{protocol_name}_{int(time.time())}"

            with self._lock:
                self.connections[connection_id] = {
                    'protocol': protocol_name,
                    'host': host,
                    'port': port,
                    'params': params or {},
                    'created_at': time.time(),
                    'status': 'connecting'
                }

            # شبیه‌سازی تأخیر اتصال
            await asyncio.sleep(0.12)

            with self._lock:
                self.connections[connection_id]['status'] = 'connected'

            print(
                f"[{LogLevel.INFO}] Custom protocol connection established: {protocol_name} {host}:{port}")
            return connection_id

        except Exception as e:
            print(f"[{LogLevel.ERROR}] Custom protocol connection failed: {e}")
            return None


class ProtocolExtensionsManager:
    """مدیر کل پروتکل‌های پیشرفته"""

    def __init__(self):
        self.quic_manager = QUICManager()
        self.http3_manager = HTTP3Manager()
        self.websocket_manager = WebSocketManager()
        self.custom_manager = CustomProtocolManager()

        self.protocols: Dict[ProtocolType, Any] = {
            ProtocolType.QUIC: self.quic_manager,
            ProtocolType.HTTP3: self.http3_manager,
            ProtocolType.WEBSOCKET: self.websocket_manager,
            ProtocolType.CUSTOM: self.custom_manager
        }

        self.is_running = False
        self._monitoring_thread = None
        self._stop_event = threading.Event()

    def configure_protocol(self, protocol_type: ProtocolType, config: ProtocolConfig):
        """پیکربندی پروتکل"""
        if protocol_type in self.protocols:
            self.protocols[protocol_type].configure(config)
            print(f"[{LogLevel.INFO}] Protocol configured: {protocol_type.value}")

    async def create_connection(self, protocol_type: ProtocolType, **kwargs) -> Optional[str]:
        """ایجاد اتصال با پروتکل مشخص"""
        if protocol_type not in self.protocols:
            return None

        manager = self.protocols[protocol_type]

        if protocol_type == ProtocolType.QUIC:
            return await manager.create_connection(
                kwargs.get('host', 'localhost'),
                kwargs.get('port', 443),
                kwargs.get('server_name')
            )
        elif protocol_type == ProtocolType.HTTP3:
            return await manager.make_request(
                kwargs.get('url', 'https://example.com'),
                kwargs.get('method', 'GET'),
                kwargs.get('headers')
            )
        elif protocol_type == ProtocolType.WEBSOCKET:
            return await manager.connect(
                kwargs.get('url', 'ws://localhost:8080'),
                kwargs.get('protocols')
            )
        elif protocol_type == ProtocolType.CUSTOM:
            return await manager.create_connection(
                kwargs.get('protocol_name', ''),
                kwargs.get('host', 'localhost'),
                kwargs.get('port', 8080),
                kwargs.get('params')
            )

        return None

    def get_connection_metrics(self, protocol_type: ProtocolType, connection_id: str) -> Optional[ConnectionMetrics]:
        """دریافت معیارهای اتصال"""
        if protocol_type not in self.protocols:
            return None

        manager = self.protocols[protocol_type]
        return manager.get_connection_metrics(connection_id)

    def start_monitoring(self):
        """شروع نظارت بر پروتکل‌ها"""
        if self.is_running:
            return

        self.is_running = True
        self._stop_event.clear()
        self._monitoring_thread = threading.Thread(
            target=self._monitor_protocols, daemon=True)
        self._monitoring_thread.start()
        print(f"[{LogLevel.INFO}] Protocol monitoring started")

    def stop_monitoring(self):
        """توقف نظارت بر پروتکل‌ها"""
        if not self.is_running:
            return

        self.is_running = False
        self._stop_event.set()

        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=5)

        print(f"[{LogLevel.INFO}] Protocol monitoring stopped")

    def _monitor_protocols(self):
        """نظارت بر پروتکل‌ها"""
        while not self._stop_event.is_set():
            try:
                # بررسی وضعیت اتصالات
                for protocol_type, manager in self.protocols.items():
                    if hasattr(manager, 'connections'):
                        with manager._lock:
                            for conn_id, conn in list(manager.connections.items()):
                                if time.time() - conn['created_at'] > 300:  # 5 دقیقه
                                    if protocol_type == ProtocolType.QUIC:
                                        manager.close_connection(conn_id)
                                    elif protocol_type == ProtocolType.WEBSOCKET:
                                        manager.close_connection(conn_id)

                time.sleep(10)  # بررسی هر 10 ثانیه

            except Exception as e:
                print(f"[{LogLevel.ERROR}] Protocol monitoring error: {e}")
                time.sleep(5)

    def get_protocol_status(self) -> Dict[str, Any]:
        """دریافت وضعیت پروتکل‌ها"""
        status = {}

        for protocol_type, manager in self.protocols.items():
            if hasattr(manager, 'connections'):
                with manager._lock:
                    status[protocol_type.value] = {
                        'active_connections': len(manager.connections),
                        'connections': list(manager.connections.keys())
                    }
            else:
                status[protocol_type.value] = {
                    'active_connections': 0,
                    'connections': []
                }

        return status

    def cleanup(self):
        """پاکسازی منابع"""
        self.stop_monitoring()

        # بستن تمام اتصالات
        for protocol_type, manager in self.protocols.items():
            if hasattr(manager, 'connections'):
                with manager._lock:
                    for conn_id in list(manager.connections.keys()):
                        if protocol_type == ProtocolType.QUIC:
                            manager.close_connection(conn_id)
                        elif protocol_type == ProtocolType.WEBSOCKET:
                            manager.close_connection(conn_id)

        print(f"[{LogLevel.INFO}] Protocol extensions cleaned up")


# نمونه سراسری
_protocol_manager = None


def get_protocol_manager() -> ProtocolExtensionsManager:
    """دریافت نمونه سراسری مدیر پروتکل‌ها"""
    global _protocol_manager
    if _protocol_manager is None:
        _protocol_manager = ProtocolExtensionsManager()
    return _protocol_manager
