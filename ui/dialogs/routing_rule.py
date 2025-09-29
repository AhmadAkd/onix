from PySide6.QtWidgets import (
    QComboBox,
    QLineEdit,
    QPushButton,
    QDialog,
    QFormLayout,
    QHBoxLayout,
)


class RoutingRuleDialog(QDialog):
    def __init__(self, parent=None, rule=None):
        super().__init__(parent)
        self.rule = rule
        self.setWindowTitle(self.tr("Edit Rule")
                            if rule else self.tr("Add Rule"))
        self.setMinimumWidth(400)

        self.layout = QFormLayout(self)

        self.type_combo = QComboBox()
        self.type_combo.addItems(
            ["domain", "ip", "process", "geosite", "geoip"])
        self.layout.addRow(self.tr("Type:"), self.type_combo)

        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText(
            self.tr("e.g., example.com or 8.8.8.8"))
        self.layout.addRow(self.tr("Value:"), self.value_edit)

        self.action_combo = QComboBox()
        self.action_combo.addItems(["proxy", "direct", "block"])
        self.layout.addRow(self.tr("Action:"), self.action_combo)

        if rule:
            self.type_combo.setCurrentText(rule.get("type", "domain"))
            self.value_edit.setText(rule.get("value", ""))
            self.action_combo.setCurrentText(rule.get("action", "proxy"))

        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton(self.tr("Save"))
        self.cancel_button = QPushButton(self.tr("Cancel"))
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)

        self.layout.addRow(button_layout)

        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def get_rule_data(self):
        return {
            "type": self.type_combo.currentText(),
            "value": self.value_edit.text().strip(),
            "action": self.action_combo.currentText()
        }
