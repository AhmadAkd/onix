from PySide6.QtWidgets import (
    QLabel,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QMenu,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QAction


class ServerCardWidget(QWidget):
    # Signal to be emitted when an action is requested on this card
    action_requested = Signal(str, dict)

    def __init__(self, server_data):
        super().__init__()
        self.server_data = server_data

        layout = QHBoxLayout(self)
        self.name_label = QLabel(server_data.get("name", "Unnamed"))
        self.name_label.setStyleSheet("font-size: 11pt; font-weight: bold;")

        # Create a vertical layout for ping labels
        ping_layout = QVBoxLayout()
        ping_layout.setSpacing(0)
        self.tcp_ping_label = QLabel()
        self.url_ping_label = QLabel()
        ping_layout.addWidget(self.tcp_ping_label)
        ping_layout.addWidget(self.url_ping_label)

        self.menu_button = QPushButton(
            QIcon(":/icons/more-horizontal.svg"), "")
        self.menu_button.setObjectName("ServerCardMenuButton")
        self.menu_button.setFixedSize(30, 30)
        self.menu_button.hide()  # Hide by default, show on hover

        layout.addWidget(self.name_label)
        layout.addStretch()
        layout.addLayout(ping_layout)
        layout.addWidget(self.menu_button)

        # Setup context menu
        self.setup_menu()

        # Initialize ping value from existing data
        self.update_ping(self.server_data.get("tcp_ping", -1), "direct_tcp")
        self.update_ping(self.server_data.get("url_ping", -1), "url")

    def enterEvent(self, event):
        """Show the menu button when the mouse enters the widget."""
        self.menu_button.show()

    def leaveEvent(self, event):
        """Hide the menu button when the mouse leaves the widget."""
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
            prefix = self.tr("TCP")
            self.server_data["tcp_ping"] = ping_value
        elif test_type == "url":
            label_to_update = self.url_ping_label
            prefix = self.tr("URL")
            self.server_data["url_ping"] = ping_value

        if not label_to_update:
            return

        if ping_value == -1 or ping_value is None:
            text = f"{prefix}: N/A"
            color = "#F44336"  # Red for failure
        elif ping_value == -2:  # Special value for "testing..."
            text = f"{prefix}: ..."
            color = "#888"  # Gray
        else:
            text = f"{prefix}: {ping_value} ms"
            if ping_value < 200:
                color = "#4CAF50"  # Green
            elif ping_value < 500:
                color = "#FFC107"  # Amber
            else:
                color = "#F44336"  # Red

        label_to_update.setText(text)
        label_to_update.setStyleSheet(f"color: {color};")
