from PySide6.QtWidgets import (
    QLabel,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QMenu,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QAction


class ServerCardWidget(QWidget):
    # Signal to be emitted when an action is requested on this card
    action_requested = Signal(str, dict)

    def __init__(self, server_data):
        super().__init__()
        self.server_data = server_data

        # Set responsive height
        self.setMinimumHeight(70)
        self.setMaximumHeight(100)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setStyleSheet("""
            ServerCardWidget {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                margin: 4px 0;
                padding: 12px;
            }
            ServerCardWidget:hover {
                border-color: #6366f1;
                background-color: #f8fafc;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Server info section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        # Server name with modern styling
        self.name_label = QLabel(server_data.get("name", "Unnamed"))
        self.name_label.setStyleSheet("""
            font-size: 14px; 
            font-weight: 600; 
            color: #1f2937;
            margin-bottom: 2px;
        """)

        # Server protocol/type info
        protocol = server_data.get("protocol", "Unknown")
        self.protocol_label = QLabel(protocol.upper())
        self.protocol_label.setStyleSheet("""
            font-size: 10px; 
            font-weight: 500; 
            color: #6b7280;
            background-color: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            max-width: 60px;
        """)
        self.protocol_label.setAlignment(Qt.AlignCenter)

        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.protocol_label)

        # Ping and stats section
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(2)
        stats_layout.setAlignment(Qt.AlignRight)

        self.tcp_ping_label = QLabel()
        self.tcp_ping_label.setStyleSheet("font-size: 12px; font-weight: 500;")

        self.url_ping_label = QLabel()
        self.url_ping_label.setStyleSheet("font-size: 12px; font-weight: 500;")

        self.health_stats_label = QLabel()
        self.health_stats_label.setStyleSheet("""
            font-size: 10px; 
            color: #6b7280;
            margin-top: 4px;
        """)

        stats_layout.addWidget(self.tcp_ping_label)
        stats_layout.addWidget(self.url_ping_label)
        stats_layout.addWidget(self.health_stats_label)

        # Menu button with modern styling
        self.menu_button = QPushButton(
            QIcon(":/icons/more-horizontal.svg"), "")
        self.menu_button.setObjectName("ServerCardMenuButton")
        self.menu_button.setFixedSize(32, 32)
        self.menu_button.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 8px;
                background-color: transparent;
                color: #6b7280;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
                color: #6366f1;
            }
        """)
        self.menu_button.hide()  # Hide by default, show on hover

        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addLayout(stats_layout)
        layout.addWidget(self.menu_button)

        # Setup context menu
        self.setup_menu()

        # Initialize ping value from existing data
        self.update_ping(self.server_data.get("tcp_ping", -1), "direct_tcp")
        self.update_ping(self.server_data.get("url_ping", -1), "url")

    def enterEvent(self, event):
        """Show the menu button when the mouse enters the widget."""
        super().enterEvent(event)
        self.menu_button.show()

    def leaveEvent(self, event):
        """Hide the menu button when the mouse leaves the widget."""
        super().leaveEvent(event)
        self.menu_button.hide()

    def setup_menu(self):
        self.menu = QMenu(self)

        ping_action = QAction(QIcon(":/icons/zap.svg"),
                              self.tr("Test Ping (TCP)"), self)
        ping_action.triggered.connect(
            lambda: self.action_requested.emit("ping_tcp", self.server_data))

        url_test_action = QAction(
            QIcon(":/icons/activity.svg"), self.tr("Test Latency (URL)"), self)
        url_test_action.triggered.connect(
            lambda: self.action_requested.emit("ping_url", self.server_data))

        edit_action = QAction(QIcon(":/icons/edit-2.svg"),
                              self.tr("Edit Server"), self)
        edit_action.triggered.connect(
            lambda: self.action_requested.emit("edit_server", self.server_data))

        copy_link_action = QAction(
            QIcon(":/icons/copy.svg"), self.tr("Copy Link"), self)
        copy_link_action.triggered.connect(
            lambda: self.action_requested.emit("copy_link", self.server_data))

        # Using a placeholder icon
        qr_action = QAction(QIcon(":/icons/qr-code.svg"),
                            self.tr("Show QR Code"), self)
        qr_action.triggered.connect(
            lambda: self.action_requested.emit("qr_code", self.server_data))

        delete_action = QAction(
            QIcon(":/icons/trash-2.svg"), self.tr("Delete"), self)
        delete_action.triggered.connect(
            lambda: self.action_requested.emit("delete", self.server_data))

        self.menu.addAction(ping_action)
        self.menu.addAction(url_test_action)
        self.menu.addAction(edit_action)
        self.menu.addAction(copy_link_action)
        self.menu.addAction(qr_action)
        self.menu.addSeparator()
        self.menu.addAction(delete_action)
        self.menu_button.setMenu(self.menu)

    def update_ping(self, ping_value, test_type):
        """Updates the correct ping label based on the test type."""
        label_to_update = None
        prefix = ""
        if test_type == "direct_tcp" or test_type == "tcp":
            label_to_update = self.tcp_ping_label
            prefix = "TCP"
            self.server_data["tcp_ping"] = ping_value
        elif test_type == "url":
            label_to_update = self.url_ping_label
            prefix = "URL"
            self.server_data["url_ping"] = ping_value

        if not label_to_update:
            return

        if ping_value == -1 or ping_value is None:
            text = f"{prefix}: N/A"
            color = "#ef4444"  # Modern red
            bg_color = "#fef2f2"
        elif ping_value == -2:  # Special value for "testing..."
            text = f"{prefix}: Testing..."
            color = "#6b7280"  # Modern gray
            bg_color = "#f9fafb"
        else:
            text = f"{prefix}: {ping_value}ms"
            if ping_value < 100:
                color = "#10b981"  # Modern green
                bg_color = "#d1fae5"
            elif ping_value < 300:
                color = "#f59e0b"  # Modern amber
                bg_color = "#fef3c7"
            else:
                color = "#ef4444"  # Modern red
                bg_color = "#fef2f2"

        label_to_update.setText(text)
        label_to_update.setStyleSheet(f"""
            color: {color};
            background-color: {bg_color};
            padding: 4px 8px;
            border-radius: 6px;
            font-weight: 500;
            font-size: 11px;
        """)

    def update_health_stats(self, stats):
        """Updates health check statistics display."""
        if not stats:
            self.health_stats_label.setText("")
            return

        tcp_ema = stats.get("tcp_ema")
        url_ema = stats.get("url_ema")
        failures = stats.get("failures", 0)
        last_test = stats.get("last_test", 0)

        if last_test > 0:
            import time
            time_ago = int(time.time() - last_test)
            if time_ago < 60:
                time_str = f"{time_ago}s ago"
            elif time_ago < 3600:
                time_str = f"{time_ago//60}m ago"
            else:
                time_str = f"{time_ago//3600}h ago"
        else:
            time_str = "Never"

        # Modern status indicator
        if failures == 0:
            status_icon = "●"
            status_color = "#10b981"  # Modern green
            bg_color = "#d1fae5"
        elif failures < 3:
            status_icon = "●"
            status_color = "#f59e0b"  # Modern amber
            bg_color = "#fef3c7"
        else:
            status_icon = "●"
            status_color = "#ef4444"  # Modern red
            bg_color = "#fef2f2"

        # Build stats text with modern styling
        stats_parts = []
        if tcp_ema:
            stats_parts.append(f"TCP: {int(tcp_ema)}ms")
        if url_ema:
            stats_parts.append(f"URL: {int(url_ema)}ms")
        if failures > 0:
            stats_parts.append(f"Fails: {failures}")
        stats_parts.append(time_str)

        stats_text = " • ".join(stats_parts)
        self.health_stats_label.setText(f"{status_icon} {stats_text}")

        # Apply modern styling
        self.health_stats_label.setStyleSheet(f"""
            color: {status_color};
            background-color: {bg_color};
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 10px;
            font-weight: 500;
            margin-top: 4px;
        """)

        # Set detailed tooltip
        tooltip_parts = []
        if tcp_ema:
            tooltip_parts.append(f"TCP EMA: {tcp_ema:.1f}ms")
        if url_ema:
            tooltip_parts.append(f"URL EMA: {url_ema:.1f}ms")
        if failures > 0:
            tooltip_parts.append(f"Consecutive Failures: {failures}")
        tooltip_parts.append(f"Last Test: {time_str}")

        self.health_stats_label.setToolTip("\n".join(tooltip_parts))
