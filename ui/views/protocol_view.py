"""
Protocol Extensions View
نمایش و مدیریت پروتکل‌های پیشرفته
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QGroupBox,
    QGridLayout,
    QTextEdit,
    QComboBox,
    QSpinBox,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QPainter, QPen, QColor, QFont
from services.protocol_extensions import (
    get_protocol_manager,
    ProtocolType,
    ProtocolConfig,
    ConnectionMetrics,
)
from constants import LogLevel
import time
from typing import List
from collections import deque


class ProtocolTestThread(QThread):
    """Thread برای تست پروتکل‌ها"""

    test_completed = Signal(str, dict)
    test_failed = Signal(str, str)

    def __init__(self, protocol_type: ProtocolType, test_params: dict):
        super().__init__()
        self.protocol_type = protocol_type
        self.test_params = test_params
        self._stop_requested = False

    def run(self):
        """اجرای تست پروتکل"""
        try:
            if self._stop_requested:
                return

            manager = get_protocol_manager()

            # شبیه‌سازی تست پروتکل
            import asyncio

            async def run_test():
                if self._stop_requested:
                    return None

                if self.protocol_type == ProtocolType.QUIC:
                    connection_id = await manager.create_connection(
                        ProtocolType.QUIC,
                        host=self.test_params.get("host", "localhost"),
                        port=self.test_params.get("port", 443),
                        server_name=self.test_params.get("server_name"),
                    )
                    return connection_id

                elif self.protocol_type == ProtocolType.HTTP3:
                    result = await manager.create_connection(
                        ProtocolType.HTTP3,
                        url=self.test_params.get("url", "https://example.com"),
                        method=self.test_params.get("method", "GET"),
                        headers=self.test_params.get("headers", {}),
                    )
                    return result

                elif self.protocol_type == ProtocolType.WEBSOCKET:
                    connection_id = await manager.create_connection(
                        ProtocolType.WEBSOCKET,
                        url=self.test_params.get("url", "ws://localhost:8080"),
                        protocols=self.test_params.get("protocols", []),
                    )
                    return connection_id

                return None

            if not self._stop_requested:
                result = asyncio.run(run_test())
                if result and not self._stop_requested:
                    self.test_completed.emit(
                        self.protocol_type.value, {"connection_id": result}
                    )
                elif not self._stop_requested:
                    self.test_failed.emit(self.protocol_type.value, "Test failed")

        except Exception as e:
            if not self._stop_requested:
                self.test_failed.emit(self.protocol_type.value, str(e))

    def stop(self):
        """توقف تست"""
        self._stop_requested = True
        self.quit()
        self.wait(3000)


class ProtocolMetricsWidget(QWidget):
    """ویجت نمایش معیارهای پروتکل"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.metrics_data = deque(maxlen=100)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # به‌روزرسانی هر ثانیه

    def setup_ui(self):
        """راه‌اندازی UI"""
        layout = QVBoxLayout(self)

        # عنوان
        title = QLabel("Protocol Metrics")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)

        # جدول معیارها
        self.metrics_table = QTableWidget(0, 3)
        self.metrics_table.setHorizontalHeaderLabels(
            ["Protocol", "Latency (ms)", "Bandwidth (Mbps)"]
        )
        self.metrics_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.metrics_table)

        # نمودار ساده
        self.chart_widget = QLabel("Real-time Chart")
        self.chart_widget.setMinimumHeight(200)
        self.chart_widget.setStyleSheet(
            """
            QLabel {
                border: 1px solid #ccc;
                background-color: #f9f9f9;
                border-radius: 5px;
            }
        """
        )
        layout.addWidget(self.chart_widget)

    def add_metrics(self, protocol: str, metrics: ConnectionMetrics):
        """اضافه کردن معیارهای جدید"""
        self.metrics_data.append(
            {
                "protocol": protocol,
                "latency": metrics.latency,
                "bandwidth": metrics.bandwidth,
                "timestamp": time.time(),
            }
        )

    def update_display(self):
        """به‌روزرسانی نمایش"""
        # به‌روزرسانی جدول
        self.metrics_table.setRowCount(len(self.metrics_data))

        for i, data in enumerate(self.metrics_data):
            self.metrics_table.setItem(i, 0, QTableWidgetItem(data["protocol"]))
            self.metrics_table.setItem(i, 1, QTableWidgetItem(f"{data['latency']:.1f}"))
            self.metrics_table.setItem(
                i, 2, QTableWidgetItem(f"{data['bandwidth']:.1f}")
            )

        # رسم نمودار ساده
        self.draw_simple_chart()

    def draw_simple_chart(self):
        """رسم نمودار ساده"""
        if not self.metrics_data:
            return

        # ایجاد تصویر ساده
        pixmap = self.chart_widget.pixmap()
        if pixmap is None:
            pixmap = self.chart_widget.grab()

        painter = QPainter(pixmap)
        painter.fillRect(pixmap.rect(), QColor(249, 249, 249))

        # رسم خطوط
        if len(self.metrics_data) > 1:
            width = pixmap.width()
            height = pixmap.height()

            # رسم خط latency
            painter.setPen(QPen(QColor(255, 0, 0), 2))
            points = []
            for i, data in enumerate(self.metrics_data):
                x = int((i / (len(self.metrics_data) - 1)) * width)
                y = int(height - (data["latency"] / 100) * height)
                points.append((x, y))

            for i in range(len(points) - 1):
                painter.drawLine(
                    points[i][0], points[i][1], points[i + 1][0], points[i + 1][1]
                )

        painter.end()
        self.chart_widget.setPixmap(pixmap)


def create_protocol_view(main_window) -> QWidget:
    """ایجاد ویو پروتکل‌های پیشرفته"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # عنوان اصلی
    title = QLabel("Advanced Protocol Extensions")
    title.setFont(QFont("Arial", 16, QFont.Bold))
    title.setAlignment(Qt.AlignCenter)
    layout.addWidget(title)

    # تب‌ها
    tab_widget = QTabWidget()

    # تب QUIC
    quic_tab = create_quic_tab(main_window)
    tab_widget.addTab(quic_tab, "QUIC")

    # تب HTTP/3
    http3_tab = create_http3_tab(main_window)
    tab_widget.addTab(http3_tab, "HTTP/3")

    # تب WebSocket
    websocket_tab = create_websocket_tab(main_window)
    tab_widget.addTab(websocket_tab, "WebSocket")

    # تب Custom Protocols
    custom_tab = create_custom_tab(main_window)
    tab_widget.addTab(custom_tab, "Custom")

    # تب Metrics
    metrics_tab = create_metrics_tab(main_window)
    tab_widget.addTab(metrics_tab, "Metrics")

    layout.addWidget(tab_widget)

    return widget


def create_quic_tab(main_window) -> QWidget:
    """ایجاد تب QUIC"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # تنظیمات QUIC
    config_group = QGroupBox("QUIC Configuration")
    config_layout = QGridLayout(config_group)

    # Host
    config_layout.addWidget(QLabel("Host:"), 0, 0)
    host_input = QLineEdit("localhost")
    config_layout.addWidget(host_input, 0, 1)

    # Port
    config_layout.addWidget(QLabel("Port:"), 1, 0)
    port_input = QSpinBox()
    port_input.setRange(1, 65535)
    port_input.setValue(443)
    config_layout.addWidget(port_input, 1, 1)

    # Server Name
    config_layout.addWidget(QLabel("Server Name:"), 2, 0)
    server_name_input = QLineEdit()
    config_layout.addWidget(server_name_input, 2, 1)

    layout.addWidget(config_group)

    # دکمه‌های کنترل
    control_layout = QHBoxLayout()

    test_button = QPushButton("Test QUIC Connection")
    test_button.clicked.connect(
        lambda: test_quic_connection(
            main_window, host_input.text(), port_input.value(), server_name_input.text()
        )
    )
    control_layout.addWidget(test_button)

    enable_button = QPushButton("Enable QUIC")
    enable_button.clicked.connect(lambda: enable_quic_protocol(main_window))
    control_layout.addWidget(enable_button)

    layout.addLayout(control_layout)

    # لاگ
    log_group = QGroupBox("Connection Log")
    log_text = QTextEdit()
    log_text.setMaximumHeight(150)
    log_group_layout = QVBoxLayout(log_group)
    log_group_layout.addWidget(log_text)
    layout.addWidget(log_group)

    # ذخیره رفرنس‌ها
    widget.host_input = host_input
    widget.port_input = port_input
    widget.server_name_input = server_name_input
    widget.log_text = log_text

    return widget


def create_http3_tab(main_window) -> QWidget:
    """ایجاد تب HTTP/3"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # تنظیمات HTTP/3
    config_group = QGroupBox("HTTP/3 Configuration")
    config_layout = QGridLayout(config_group)

    # URL
    config_layout.addWidget(QLabel("URL:"), 0, 0)
    url_input = QLineEdit("https://example.com")
    config_layout.addWidget(url_input, 0, 1)

    # Method
    config_layout.addWidget(QLabel("Method:"), 1, 0)
    method_combo = QComboBox()
    method_combo.addItems(["GET", "POST", "PUT", "DELETE"])
    config_layout.addWidget(method_combo, 1, 1)

    layout.addWidget(config_group)

    # دکمه‌های کنترل
    control_layout = QHBoxLayout()

    test_button = QPushButton("Test HTTP/3 Request")
    test_button.clicked.connect(
        lambda: test_http3_request(
            main_window, url_input.text(), method_combo.currentText()
        )
    )
    control_layout.addWidget(test_button)

    enable_button = QPushButton("Enable HTTP/3")
    enable_button.clicked.connect(lambda: enable_http3_protocol(main_window))
    control_layout.addWidget(enable_button)

    layout.addLayout(control_layout)

    # لاگ
    log_group = QGroupBox("Request Log")
    log_text = QTextEdit()
    log_text.setMaximumHeight(150)
    log_group_layout = QVBoxLayout(log_group)
    log_group_layout.addWidget(log_text)
    layout.addWidget(log_group)

    # ذخیره رفرنس‌ها
    widget.url_input = url_input
    widget.method_combo = method_combo
    widget.log_text = log_text

    return widget


def create_websocket_tab(main_window) -> QWidget:
    """ایجاد تب WebSocket"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # تنظیمات WebSocket
    config_group = QGroupBox("WebSocket Configuration")
    config_layout = QGridLayout(config_group)

    # URL
    config_layout.addWidget(QLabel("WebSocket URL:"), 0, 0)
    url_input = QLineEdit("ws://localhost:8080")
    config_layout.addWidget(url_input, 0, 1)

    # Protocols
    config_layout.addWidget(QLabel("Protocols:"), 1, 0)
    protocols_input = QLineEdit("chat, echo")
    config_layout.addWidget(protocols_input, 1, 1)

    layout.addWidget(config_group)

    # دکمه‌های کنترل
    control_layout = QHBoxLayout()

    connect_button = QPushButton("Connect WebSocket")
    connect_button.clicked.connect(
        lambda: connect_websocket(
            main_window, url_input.text(), protocols_input.text().split(",")
        )
    )
    control_layout.addWidget(connect_button)

    disconnect_button = QPushButton("Disconnect")
    disconnect_button.clicked.connect(lambda: disconnect_websocket(main_window))
    control_layout.addWidget(disconnect_button)

    layout.addLayout(control_layout)

    # پیام‌ها
    message_group = QGroupBox("Messages")
    message_layout = QVBoxLayout(message_group)

    message_input = QLineEdit()
    message_input.setPlaceholderText("Enter message to send...")
    message_layout.addWidget(message_input)

    send_button = QPushButton("Send Message")
    send_button.clicked.connect(
        lambda: send_websocket_message(main_window, message_input.text())
    )
    message_layout.addWidget(send_button)

    message_log = QTextEdit()
    message_log.setMaximumHeight(150)
    message_layout.addWidget(message_log)

    layout.addWidget(message_group)

    # ذخیره رفرنس‌ها
    widget.url_input = url_input
    widget.protocols_input = protocols_input
    widget.message_input = message_input
    widget.message_log = message_log

    return widget


def create_custom_tab(main_window) -> QWidget:
    """ایجاد تب پروتکل‌های سفارشی"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # ثبت پروتکل جدید
    register_group = QGroupBox("Register Custom Protocol")
    register_layout = QGridLayout(register_group)

    # نام پروتکل
    register_layout.addWidget(QLabel("Protocol Name:"), 0, 0)
    name_input = QLineEdit()
    register_layout.addWidget(name_input, 0, 1)

    # اولویت
    register_layout.addWidget(QLabel("Priority:"), 1, 0)
    priority_input = QSpinBox()
    priority_input.setRange(0, 100)
    priority_input.setValue(50)
    register_layout.addWidget(priority_input, 1, 1)

    # Timeout
    register_layout.addWidget(QLabel("Timeout (s):"), 2, 0)
    timeout_input = QSpinBox()
    timeout_input.setRange(1, 300)
    timeout_input.setValue(30)
    register_layout.addWidget(timeout_input, 2, 1)

    register_button = QPushButton("Register Protocol")
    register_button.clicked.connect(
        lambda: register_custom_protocol(
            main_window,
            name_input.text(),
            priority_input.value(),
            timeout_input.value(),
        )
    )
    register_layout.addWidget(register_button, 3, 0, 1, 2)

    layout.addWidget(register_group)

    # لیست پروتکل‌های ثبت شده
    protocols_group = QGroupBox("Registered Protocols")
    protocols_layout = QVBoxLayout(protocols_group)

    protocols_table = QTableWidget(0, 4)
    protocols_table.setHorizontalHeaderLabels(["Name", "Priority", "Timeout", "Status"])
    protocols_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    protocols_layout.addWidget(protocols_table)

    layout.addWidget(protocols_group)

    # ذخیره رفرنس‌ها
    widget.name_input = name_input
    widget.priority_input = priority_input
    widget.timeout_input = timeout_input
    widget.protocols_table = protocols_table

    return widget


def create_metrics_tab(main_window) -> QWidget:
    """ایجاد تب معیارها"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # ویجت معیارها
    metrics_widget = ProtocolMetricsWidget()
    layout.addWidget(metrics_widget)

    # دکمه‌های کنترل
    control_layout = QHBoxLayout()

    refresh_button = QPushButton("Refresh Metrics")
    refresh_button.clicked.connect(
        lambda: refresh_protocol_metrics(main_window, metrics_widget)
    )
    control_layout.addWidget(refresh_button)

    clear_button = QPushButton("Clear Data")
    clear_button.clicked.connect(lambda: clear_metrics_data(metrics_widget))
    control_layout.addWidget(clear_button)

    layout.addLayout(control_layout)

    return widget


# توابع کمکی


def test_quic_connection(main_window, host: str, port: int, server_name: str):
    """تست اتصال QUIC"""
    try:
        manager = get_protocol_manager()

        # پیکربندی QUIC
        config = ProtocolConfig(
            name="QUIC Test", protocol_type=ProtocolType.QUIC, enabled=True
        )
        manager.configure_protocol(ProtocolType.QUIC, config)

        # شروع تست
        test_thread = ProtocolTestThread(
            ProtocolType.QUIC, {"host": host, "port": port, "server_name": server_name}
        )

        def on_completed(protocol, result):
            main_window.protocol_view.quic_tab.log_text.append(
                f"QUIC connection successful: {result}"
            )
            test_thread.deleteLater()

        def on_failed(protocol, error):
            main_window.protocol_view.quic_tab.log_text.append(
                f"QUIC connection failed: {error}"
            )
            test_thread.deleteLater()

        test_thread.test_completed.connect(on_completed)
        test_thread.test_failed.connect(on_failed)
        test_thread.start()

    except Exception as e:
        print(f"[{LogLevel.ERROR}] QUIC test error: {e}")


def test_http3_request(main_window, url: str, method: str):
    """تست درخواست HTTP/3"""
    try:
        manager = get_protocol_manager()

        # پیکربندی HTTP/3
        config = ProtocolConfig(
            name="HTTP/3 Test", protocol_type=ProtocolType.HTTP3, enabled=True
        )
        manager.configure_protocol(ProtocolType.HTTP3, config)

        # شروع تست
        test_thread = ProtocolTestThread(
            ProtocolType.HTTP3, {"url": url, "method": method}
        )

        def on_completed(protocol, result):
            main_window.protocol_view.http3_tab.log_text.append(
                f"HTTP/3 request successful: {result}"
            )
            test_thread.deleteLater()

        def on_failed(protocol, error):
            main_window.protocol_view.http3_tab.log_text.append(
                f"HTTP/3 request failed: {error}"
            )
            test_thread.deleteLater()

        test_thread.test_completed.connect(on_completed)
        test_thread.test_failed.connect(on_failed)
        test_thread.start()

    except Exception as e:
        print(f"[{LogLevel.ERROR}] HTTP/3 test error: {e}")


def connect_websocket(main_window, url: str, protocols: List[str]):
    """اتصال WebSocket"""
    try:
        manager = get_protocol_manager()

        # پیکربندی WebSocket
        config = ProtocolConfig(
            name="WebSocket Test", protocol_type=ProtocolType.WEBSOCKET, enabled=True
        )
        manager.configure_protocol(ProtocolType.WEBSOCKET, config)

        # شروع اتصال
        test_thread = ProtocolTestThread(
            ProtocolType.WEBSOCKET, {"url": url, "protocols": protocols}
        )

        def on_completed(protocol, result):
            main_window.protocol_view.websocket_tab.message_log.append(
                f"WebSocket connected: {result}"
            )
            test_thread.deleteLater()

        def on_failed(protocol, error):
            main_window.protocol_view.websocket_tab.message_log.append(
                f"WebSocket connection failed: {error}"
            )
            test_thread.deleteLater()

        test_thread.test_completed.connect(on_completed)
        test_thread.test_failed.connect(on_failed)
        test_thread.start()

    except Exception as e:
        print(f"[{LogLevel.ERROR}] WebSocket connection error: {e}")


def disconnect_websocket(main_window):
    """قطع اتصال WebSocket"""
    try:
        manager = get_protocol_manager()
        manager.websocket_manager.close_connection("all")
        main_window.protocol_view.websocket_tab.message_log.append(
            "WebSocket disconnected"
        )
    except Exception as e:
        print(f"[{LogLevel.ERROR}] WebSocket disconnect error: {e}")


def send_websocket_message(main_window, message: str):
    """ارسال پیام WebSocket"""
    if not message.strip():
        return

    try:
        # شبیه‌سازی ارسال پیام
        main_window.protocol_view.websocket_tab.message_log.append(f"Sent: {message}")
        main_window.protocol_view.websocket_tab.message_input.clear()
    except Exception as e:
        print(f"[{LogLevel.ERROR}] WebSocket send error: {e}")


def register_custom_protocol(main_window, name: str, priority: int, timeout: int):
    """ثبت پروتکل سفارشی"""
    if not name.strip():
        return

    try:
        manager = get_protocol_manager()

        config = ProtocolConfig(
            name=name,
            protocol_type=ProtocolType.CUSTOM,
            enabled=True,
            priority=priority,
            timeout=timeout,
        )

        manager.custom_manager.register_protocol(config)

        # به‌روزرسانی جدول
        table = main_window.protocol_view.custom_tab.protocols_table
        row = table.rowCount()
        table.insertRow(row)
        table.setItem(row, 0, QTableWidgetItem(name))
        table.setItem(row, 1, QTableWidgetItem(str(priority)))
        table.setItem(row, 2, QTableWidgetItem(str(timeout)))
        table.setItem(row, 3, QTableWidgetItem("Registered"))

        print(f"[{LogLevel.INFO}] Custom protocol registered: {name}")

    except Exception as e:
        print(f"[{LogLevel.ERROR}] Custom protocol registration error: {e}")


def enable_quic_protocol(main_window):
    """فعال‌سازی پروتکل QUIC"""
    try:
        manager = get_protocol_manager()
        manager.start_monitoring()
        print(f"[{LogLevel.INFO}] QUIC protocol enabled")
    except Exception as e:
        print(f"[{LogLevel.ERROR}] QUIC enable error: {e}")


def enable_http3_protocol(main_window):
    """فعال‌سازی پروتکل HTTP/3"""
    try:
        manager = get_protocol_manager()
        manager.start_monitoring()
        print(f"[{LogLevel.INFO}] HTTP/3 protocol enabled")
    except Exception as e:
        print(f"[{LogLevel.ERROR}] HTTP/3 enable error: {e}")


def refresh_protocol_metrics(main_window, metrics_widget: ProtocolMetricsWidget):
    """به‌روزرسانی معیارهای پروتکل"""
    try:
        manager = get_protocol_manager()
        status = manager.get_protocol_status()

        for protocol, data in status.items():
            if data["active_connections"] > 0:
                # شبیه‌سازی معیارها
                metrics = ConnectionMetrics(
                    protocol=protocol,
                    latency=50.0 + (hash(protocol) % 50),
                    bandwidth=100.0 + (hash(protocol) % 100),
                    packet_loss=0.01,
                    jitter=5.0,
                    connection_time=time.time(),
                    stability_score=0.9,
                )
                metrics_widget.add_metrics(protocol, metrics)

    except Exception as e:
        print(f"[{LogLevel.ERROR}] Metrics refresh error: {e}")


def clear_metrics_data(metrics_widget: ProtocolMetricsWidget):
    """پاک کردن داده‌های معیارها"""
    metrics_widget.metrics_data.clear()
    metrics_widget.metrics_table.setRowCount(0)
    print(f"[{LogLevel.INFO}] Metrics data cleared")
