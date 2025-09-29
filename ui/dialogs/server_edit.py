from PySide6.QtWidgets import (
    QLineEdit,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QVBoxLayout,
    QCheckBox,
)


class ServerEditDialog(QDialog):
    def __init__(self, parent=None, server_config=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Edit Server Configuration"))
        self.setMinimumWidth(500)

        self.config = server_config.copy()  # Work on a copy
        self.widgets = {}

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Common fields
        self.add_form_row(form_layout, self.tr("Name"), "name")
        self.add_form_row(form_layout, self.tr("Server"), "server")
        self.add_form_row(form_layout, self.tr(
            "Port"), "port", is_numeric=True)

        protocol = self.config.get("protocol")

        # Protocol-specific fields
        if protocol in ["vless", "vmess", "trojan", "hysteria2", "tuic"]:
            self.add_form_row(form_layout, self.tr("SNI"), "sni")

        if protocol in ["vless", "vmess", "tuic"]:
            self.add_form_row(form_layout, self.tr("UUID"), "uuid")

        if protocol in ["trojan", "shadowsocks", "hysteria2", "tuic"]:
            self.add_form_row(form_layout, self.tr("Password"), "password")

        if protocol in ["vless", "vmess"]:
            self.add_form_row(form_layout, self.tr("Transport"), "transport")
            self.add_form_row(form_layout, self.tr("WS Path"), "ws_path")

        if protocol == "wireguard":
            self.add_form_row(form_layout, self.tr(
                "Private Key"), "private_key")
            self.add_form_row(form_layout, self.tr("Public Key"), "public_key")
            self.add_form_row(form_layout, self.tr(
                "Preshared Key"), "preshared_key")
            self.add_form_row(form_layout, self.tr(
                "Local Address"), "local_address")

        main_layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.on_save)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def add_form_row(self, layout, label, key, is_numeric=False):
        """Helper to add a row to the form layout."""
        value = self.config.get(key, "")
        # For numeric fields, ensure we have a string representation
        if is_numeric and isinstance(value, (int, float)):
            value = str(value)

        if isinstance(value, bool):
            widget = QCheckBox()
            widget.setChecked(value)
        else:
            widget = QLineEdit()
            widget.setText(value or "")

        self.widgets[key] = widget
        layout.addRow(f"{label}:", widget)

    def on_save(self):
        """Update the config dictionary from widget values before accepting."""
        for key, widget in self.widgets.items():
            if isinstance(widget, QLineEdit):
                new_value = widget.text().strip()
                # Try to convert back to numeric if needed
                original_value = self.config.get(key)
                if isinstance(original_value, int):
                    try:
                        new_value = int(new_value)
                    except (ValueError, TypeError):
                        new_value = original_value  # Revert on error
                elif isinstance(original_value, float):
                    try:
                        new_value = float(new_value)
                    except (ValueError, TypeError):
                        new_value = original_value  # Revert on error

                self.config[key] = new_value
            elif isinstance(widget, QCheckBox):
                self.config[key] = widget.isChecked()

        self.accept()

    def get_updated_config(self):
        """Returns the modified configuration dictionary."""
        return self.config
