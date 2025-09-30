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
        self.setMinimumHeight(90)
        self.setMaximumHeight(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setStyleSheet(
            """
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
        """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Server info section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        # Server name with modern styling
        self.name_label = QLabel(server_data.get("name", "Unnamed"))
        self.name_label.setStyleSheet(
            """
            font-size: 14px; 
            font-weight: 600; 
            color: #1f2937;
            margin-bottom: 2px;
        """
        )

        # Server protocol/type info
        protocol = server_data.get("protocol", "Unknown")
        # Fix protocol names
        protocol_map = {
            "shadowsocks": "Shadowsocks",
            "ss": "Shadowsocks",
            "vless": "VLESS",
            "vmess": "VMess",
            "trojan": "Trojan",
            "hysteria2": "Hysteria2",
            "tuic": "TUIC",
            "wireguard": "WireGuard",
        }
        display_protocol = protocol_map.get(protocol.lower(), protocol.upper())
        self.protocol_label = QLabel(display_protocol)
        self.protocol_label.setStyleSheet(
            """
            font-size: 10px; 
            font-weight: 500; 
            color: #6b7280;
            background-color: #f3f4f6;
            padding: 2px 8px;
            border-radius: 4px;
            min-width: 80px;
        """
        )
        self.protocol_label.setAlignment(Qt.AlignCenter)

        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.protocol_label)

        # Ping and stats section
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(4)
        stats_layout.setAlignment(Qt.AlignRight)

        self.tcp_ping_label = QLabel("TCP: N/A")
        self.tcp_ping_label.setStyleSheet(
            """
            font-size: 13px; 
            font-weight: 600;
            color: #ef4444;
            background-color: #fef2f2;
            padding: 10px 16px;
            border-radius: 6px;
            margin: 2px 0;
            min-width: 80px;
            min-height: 20px;
        """
        )

        self.url_ping_label = QLabel("URI: N/A")
        self.url_ping_label.setStyleSheet(
            """
            font-size: 13px; 
            font-weight: 600;
            color: #ef4444;
            background-color: #fef2f2;
            padding: 10px 16px;
            border-radius: 6px;
            margin: 2px 0;
            min-width: 80px;
            min-height: 20px;
        """
        )

        # Health stats label removed - using TCP/URI badges instead

        stats_layout.addWidget(self.tcp_ping_label)
        stats_layout.addWidget(self.url_ping_label)

        # Menu button with modern styling
        self.menu_button = QPushButton(QIcon(":/icons/more-horizontal.svg"), "")
        self.menu_button.setObjectName("ServerCardMenuButton")
        self.menu_button.setFixedSize(32, 32)
        self.menu_button.setStyleSheet(
            """
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
        """
        )
        self.menu_button.hide()  # Hide by default, show on hover

        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addLayout(stats_layout)
        layout.addWidget(self.menu_button)

        # Setup context menu
        self.setup_menu()

        # Initialize ping value from existing data
        self.update_ping("direct_tcp", self.server_data.get("tcp_ping", -1))
        self.update_ping("url", self.server_data.get("url_ping", -1))

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

        ping_action = QAction(
            QIcon(":/icons/zap.svg"), self.tr("Test Ping (TCP)"), self
        )
        ping_action.triggered.connect(
            lambda: self.action_requested.emit("ping_tcp", self.server_data)
        )

        url_test_action = QAction(
            QIcon(":/icons/activity.svg"), self.tr("Test Latency (URL)"), self
        )
        url_test_action.triggered.connect(
            lambda: self.action_requested.emit("ping_url", self.server_data)
        )

        edit_action = QAction(QIcon(":/icons/edit-2.svg"), self.tr("Edit Server"), self)
        edit_action.triggered.connect(
            lambda: self.action_requested.emit("edit_server", self.server_data)
        )

        copy_link_action = QAction(
            QIcon(":/icons/copy.svg"), self.tr("Copy Link"), self
        )
        copy_link_action.triggered.connect(
            lambda: self.action_requested.emit("copy_link", self.server_data)
        )

        # Using a placeholder icon
        qr_action = QAction(QIcon(":/icons/qr-code.svg"), self.tr("Show QR Code"), self)
        qr_action.triggered.connect(
            lambda: self.action_requested.emit("qr_code", self.server_data)
        )

        delete_action = QAction(QIcon(":/icons/trash-2.svg"), self.tr("Delete"), self)
        delete_action.triggered.connect(
            lambda: self.action_requested.emit("delete", self.server_data)
        )

        self.menu.addAction(ping_action)
        self.menu.addAction(url_test_action)
        self.menu.addAction(edit_action)
        self.menu.addAction(copy_link_action)
        self.menu.addAction(qr_action)
        self.menu.addSeparator()
        self.menu.addAction(delete_action)
        self.menu_button.setMenu(self.menu)

    def update_ping(self, test_type, ping_value):
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
            color = "#ef4444"  # Red
            bg_color = "#fef2f2"  # Light red background
        elif ping_value == -2:  # Special value for "testing..."
            text = f"{prefix}: Testing..."
            color = "#6b7280"  # Gray
            bg_color = "#f9fafb"  # Light gray background
        else:
            text = f"{prefix}: {ping_value}ms"
            if ping_value < 100:
                color = "#10b981"  # Green
                bg_color = "#d1fae5"  # Light green background
            elif ping_value < 300:
                color = "#f59e0b"  # Amber
                bg_color = "#fef3c7"  # Light amber background
            else:
                color = "#ef4444"  # Red
                bg_color = "#fef2f2"  # Light red background

        label_to_update.setText(text)
        label_to_update.setStyleSheet(
            f"""
            color: {color};
            background-color: {bg_color};
            padding: 10px 16px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 13px;
            margin: 2px 0;
            min-width: 80px;
            min-height: 20px;
        """
        )

    def update_health_stats(self, stats):
        """Health stats removed - using TCP/URI badges instead."""
        pass
