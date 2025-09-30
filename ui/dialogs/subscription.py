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
    QSizePolicy,
)
from PySide6.QtCore import Qt


class SubscriptionEditDialog(QDialog):
    def __init__(self, parent=None, sub=None):
        super().__init__(parent)
        self.sub = sub
        self.setWindowTitle(
            self.tr("Edit Subscription") if sub else self.tr("Add Subscription")
        )
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
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
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
            "enabled": self.sub.get("enabled", True) if self.sub else True,
        }


class SubscriptionManagerDialog(QDialog):
    def __init__(self, parent=None, subscriptions=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Subscription Manager"))
        self.setMinimumSize(600, 400)
        self.setMaximumSize(1000, 700)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        self.subscriptions = subscriptions if subscriptions is not None else []

        main_layout = QVBoxLayout(self)

        # Update All button at the top
        update_all_layout = QHBoxLayout()
        self.update_all_button = QPushButton(self.tr("Update All Subscriptions"))
        self.update_all_button.setStyleSheet(
            """
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #5b5bd6;
            }
            QPushButton:pressed {
                background-color: #4f46e5;
            }
        """
        )
        self.update_all_button.clicked.connect(self.update_all_subscriptions)
        update_all_layout.addWidget(self.update_all_button)
        update_all_layout.addStretch()
        main_layout.addLayout(update_all_layout)

        self.sub_list_widget = QListWidget()
        main_layout.addWidget(self.sub_list_widget)

        # --- Buttons ---
        button_layout = QHBoxLayout()
        add_button = QPushButton(self.tr("Add"))
        add_button.clicked.connect(self.add_subscription)
        save_button = QPushButton(self.tr("Save & Close"))
        # Accept will trigger the save logic
        save_button.clicked.connect(self.accept)

        button_layout.addStretch()
        button_layout.addWidget(add_button)
        button_layout.addWidget(save_button)
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
                lambda state, index=i: self.toggle_subscription(index, state)
            )
            # Make checkbox bigger and more visible
            checkbox.setStyleSheet(
                """
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    border: 2px solid #d1d5db;
                    border-radius: 4px;
                    background-color: white;
                }
                QCheckBox::indicator:checked {
                    background-color: #6366f1;
                    border-color: #6366f1;
                    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
                }
                QCheckBox::indicator:hover {
                    border-color: #6366f1;
                }
            """
            )

            name_label = QLabel(sub.get("name"))
            name_label.setStyleSheet("font-size: 11pt;")  # Larger font

            edit_button = QPushButton(self.tr("Edit"))
            edit_button.setFixedWidth(100)
            edit_button.setStyleSheet(
                """
                QPushButton {
                    background-color: #6366f1;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 12px 16px;
                    font-weight: 600;
                    font-size: 13px;
                    min-height: 20px;
                }
                QPushButton:hover {
                    background-color: #5b5bd6;
                }
                QPushButton:pressed {
                    background-color: #4f46e5;
                }
            """
            )
            edit_button.clicked.connect(
                lambda _, index=i: self.edit_subscription(index)
            )

            update_button = QPushButton(self.tr("Update"))
            update_button.setFixedWidth(100)
            update_button.setStyleSheet(
                """
                QPushButton {
                    background-color: #10b981;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 12px 16px;
                    font-weight: 600;
                    font-size: 13px;
                    min-height: 20px;
                }
                QPushButton:hover {
                    background-color: #059669;
                }
                QPushButton:pressed {
                    background-color: #047857;
                }
            """
            )
            update_button.clicked.connect(
                lambda _, index=i: self.update_single_subscription(index)
            )

            delete_button = QPushButton(self.tr("Delete"))
            delete_button.setFixedWidth(100)
            delete_button.setStyleSheet(
                """
                QPushButton {
                    background-color: #ef4444;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 12px 16px;
                    font-weight: 600;
                    font-size: 13px;
                    min-height: 20px;
                }
                QPushButton:hover {
                    background-color: #dc2626;
                }
                QPushButton:pressed {
                    background-color: #b91c1c;
                }
            """
            )
            delete_button.clicked.connect(
                lambda _, index=i: self.delete_subscription(index)
            )

            layout.addWidget(checkbox)
            layout.addWidget(name_label)
            layout.addStretch()

            # Button container with proper spacing
            button_container = QHBoxLayout()
            button_container.setSpacing(6)
            button_container.addWidget(edit_button)
            button_container.addWidget(update_button)
            button_container.addWidget(delete_button)

            layout.addLayout(button_container)

            list_item = QListWidgetItem(self.sub_list_widget)
            # Increase size hint for taller rows
            size_hint = item_widget.sizeHint()
            size_hint.setHeight(size_hint.height() + 30)
            list_item.setSizeHint(size_hint)

            self.sub_list_widget.addItem(list_item)
            self.sub_list_widget.setItemWidget(list_item, item_widget)

    def toggle_subscription(self, index, state):
        self.subscriptions[index]["enabled"] = state == Qt.Checked

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
        reply = QMessageBox.question(
            self,
            self.tr("Confirm Deletion"),
            self.tr("Are you sure you want to delete subscription '{}'?").format(
                sub_name
            ),
        )
        if reply == QMessageBox.Yes:
            del self.subscriptions[index]
            self.populate_list()

    def update_single_subscription(self, index):
        """Update a single subscription."""
        if 0 <= index < len(self.subscriptions):
            sub = self.subscriptions[index]
            if sub.get("enabled", True):
                # Check if parent has subscription manager
                if hasattr(self.parent(), "subscription_manager"):
                    if self.parent().subscription_manager.is_update_in_progress():
                        QMessageBox.warning(
                            self,
                            self.tr("Update In Progress"),
                            self.tr(
                                "Another subscription update is already running. Please wait."
                            ),
                        )
                        return

                # Emit signal to parent to update this specific subscription
                if hasattr(self.parent(), "update_single_subscription"):
                    self.parent().update_single_subscription(sub)
                else:
                    QMessageBox.information(
                        self,
                        self.tr("Update"),
                        self.tr("Updating subscription: {}").format(
                            sub.get("name", "Unknown")
                        ),
                    )
            else:
                QMessageBox.warning(
                    self,
                    self.tr("Update"),
                    self.tr(
                        "Subscription '{}' is disabled. Please enable it first."
                    ).format(sub.get("name", "Unknown")),
                )

    def update_all_subscriptions(self):
        """Update all enabled subscriptions."""
        enabled_subs = [sub for sub in self.subscriptions if sub.get("enabled", True)]
        if not enabled_subs:
            QMessageBox.information(
                self, self.tr("Update"), self.tr("No enabled subscriptions to update.")
            )
            return

        # Check if parent has subscription manager
        if hasattr(self.parent(), "subscription_manager"):
            if self.parent().subscription_manager.is_update_in_progress():
                QMessageBox.warning(
                    self,
                    self.tr("Update In Progress"),
                    self.tr(
                        "Another subscription update is already running. Please wait."
                    ),
                )
                return

        # Emit signal to parent to update all subscriptions
        if hasattr(self.parent(), "update_all_subscriptions"):
            self.parent().update_all_subscriptions()
        else:
            QMessageBox.information(
                self,
                self.tr("Update"),
                self.tr("Updating {} subscriptions...").format(len(enabled_subs)),
            )

    def get_subscriptions(self):
        return self.subscriptions
