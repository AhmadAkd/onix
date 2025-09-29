from PySide6.QtWidgets import (
    QLineEdit,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QVBoxLayout,
    QListWidget,
    QHBoxLayout,
    QPushButton,
    QWidget,
    QCheckBox,
    QLabel,
    QListWidgetItem,
    QMessageBox,
)
from PySide6.QtCore import Qt


class SubscriptionEditDialog(QDialog):
    def __init__(self, parent=None, sub=None):
        super().__init__(parent)
        self.sub = sub
        self.setWindowTitle(self.tr("Edit Subscription")
                            if sub else self.tr("Add Subscription"))
        self.setMinimumWidth(450)

        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.url_edit = QLineEdit()

        if sub:
            self.name_edit.setText(sub.get("name", ""))
            self.url_edit.setText(sub.get("url", ""))

        layout.addRow(self.tr("Name:"), self.name_edit)
        layout.addRow(self.tr("URL:"), self.url_edit)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)

    def get_sub_data(self):
        name = self.name_edit.text().strip()
        url = self.url_edit.text().strip()
        if not name or not url:
            return None
        return {
            "name": name,
            "url": url,
            "enabled": self.sub.get("enabled", True) if self.sub else True
        }


class SubscriptionManagerDialog(QDialog):
    def __init__(self, parent=None, subscriptions=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Subscription Manager"))
        self.setMinimumSize(600, 400)

        self.subscriptions = subscriptions if subscriptions is not None else []

        main_layout = QVBoxLayout(self)

        self.sub_list_widget = QListWidget()
        main_layout.addWidget(self.sub_list_widget)

        # --- Buttons ---
        button_layout = QHBoxLayout()
        add_button = QPushButton(self.tr("Add"))
        add_button.clicked.connect(self.add_subscription)
        save_button = QPushButton(self.tr("Save & Close"))
        # Accept will trigger the save logic
        save_button.clicked.connect(self.accept)
        close_button = QPushButton(self.tr("Close"))
        # Reject will close without saving
        close_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(add_button)
        button_layout.addWidget(save_button)
        button_layout.addWidget(close_button)
        main_layout.addLayout(button_layout)

        self.populate_list()

    def populate_list(self):
        self.sub_list_widget.clear()
        for i, sub in enumerate(self.subscriptions):
            item_widget = QWidget()
            layout = QHBoxLayout(item_widget)
            layout.setContentsMargins(10, 10, 10, 10)  # Increased margins
            layout.setSpacing(10)  # Added spacing

            checkbox = QCheckBox("")
            checkbox.setChecked(sub.get("enabled", True))
            checkbox.stateChanged.connect(
                lambda state, index=i: self.toggle_subscription(index, state))
            # Make checkbox bigger
            checkbox.setStyleSheet(
                "QCheckBox::indicator { width: 18px; height: 18px; }")

            name_label = QLabel(sub.get("name"))
            name_label.setStyleSheet("font-size: 11pt;")  # Larger font

            edit_button = QPushButton(self.tr("Edit"))
            edit_button.setFixedWidth(80)  # Increased width
            edit_button.clicked.connect(
                lambda _, index=i: self.edit_subscription(index))
            delete_button = QPushButton(self.tr("Delete"))
            delete_button.setFixedWidth(80)  # Increased width
            delete_button.clicked.connect(
                lambda _, index=i: self.delete_subscription(index))

            layout.addWidget(checkbox)
            layout.addWidget(name_label)
            layout.addStretch()
            layout.addWidget(edit_button)
            layout.addWidget(delete_button)

            list_item = QListWidgetItem(self.sub_list_widget)
            # Increase size hint for taller rows
            size_hint = item_widget.sizeHint()
            size_hint.setHeight(size_hint.height() + 20)
            list_item.setSizeHint(size_hint)

            self.sub_list_widget.addItem(list_item)
            self.sub_list_widget.setItemWidget(list_item, item_widget)

    def toggle_subscription(self, index, state):
        self.subscriptions[index]["enabled"] = (state == Qt.Checked)

    def add_subscription(self):
        dialog = SubscriptionEditDialog(self)
        if dialog.exec() == QDialog.Accepted:
            new_sub = dialog.get_sub_data()
            if new_sub:
                self.subscriptions.append(new_sub)
                self.populate_list()

    def edit_subscription(self, index):
        dialog = SubscriptionEditDialog(self, sub=self.subscriptions[index])
        if dialog.exec() == QDialog.Accepted:
            updated_sub = dialog.get_sub_data()
            if updated_sub:
                self.subscriptions[index] = updated_sub
                self.populate_list()

    def delete_subscription(self, index):
        sub_name = self.subscriptions[index].get("name")
        reply = QMessageBox.question(self, self.tr("Confirm Deletion"),
                                     self.tr("Are you sure you want to delete subscription '{}'?").format(sub_name))
        if reply == QMessageBox.Yes:
            del self.subscriptions[index]
            self.populate_list()

    def get_subscriptions(self):
        return self.subscriptions
