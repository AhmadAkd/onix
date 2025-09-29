import uuid
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton,
    QDialogButtonBox, QLineEdit, QFormLayout, QLabel, QMessageBox, QListWidgetItem
)
from PySide6.QtCore import Qt


class ChainEditDialog(QDialog):
    """
    A dialog for creating and editing a single server chain.
    """

    def __init__(self, parent, all_servers, chain=None):
        super().__init__(parent)
        self.chain = chain
        self.all_servers = all_servers

        self.setWindowTitle(self.tr(
            "Edit Chain") if chain else self.tr("Add Chain"))
        self.setMinimumSize(600, 450)

        main_layout = QVBoxLayout(self)

        # Chain Name Input
        form_layout = QFormLayout()
        self.name_edit = QLineEdit()
        if chain:
            self.name_edit.setText(chain.get("name", ""))
        form_layout.addRow(self.tr("Chain Name:"), self.name_edit)
        main_layout.addLayout(form_layout)

        # Server Selection Layout
        selection_layout = QHBoxLayout()

        # Available Servers List
        available_layout = QVBoxLayout()
        available_layout.addWidget(QLabel(self.tr("Available Servers")))
        self.available_list = QListWidget()
        self.available_list.setSelectionMode(QListWidget.ExtendedSelection)
        available_layout.addWidget(self.available_list)
        selection_layout.addLayout(available_layout)

        # Add/Remove Buttons
        add_remove_layout = QVBoxLayout()
        add_remove_layout.addStretch()
        add_button = QPushButton(">>")
        add_button.setToolTip(self.tr("Add selected servers to chain"))
        add_button.clicked.connect(self.add_servers_to_chain)
        remove_button = QPushButton("<<")
        remove_button.setToolTip(self.tr("Remove selected servers from chain"))
        remove_button.clicked.connect(self.remove_servers_from_chain)
        add_remove_layout.addWidget(add_button)
        add_remove_layout.addWidget(remove_button)
        add_remove_layout.addStretch()
        selection_layout.addLayout(add_remove_layout)

        # Servers in Chain List
        chain_layout = QVBoxLayout()
        chain_layout.addWidget(QLabel(self.tr("Servers in Chain (in order)")))
        self.chain_list = QListWidget()
        # Enable Drag and Drop for reordering
        self.chain_list.setDragDropMode(QListWidget.InternalMove)
        self.chain_list.setDropIndicatorShown(True)
        self.chain_list.setSelectionMode(QListWidget.ExtendedSelection)
        chain_layout.addWidget(self.chain_list)
        selection_layout.addLayout(chain_layout)
        main_layout.addLayout(selection_layout)

        # Dialog Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        self.populate_lists()

    def populate_lists(self):
        chain_server_ids = set(self.chain.get(
            "servers", [])) if self.chain else set()

        # Populate available servers list
        for server in self.all_servers:
            if server.get("id") not in chain_server_ids:
                item = QListWidgetItem(server.get("name"))
                item.setData(Qt.UserRole, server.get("id"))
                self.available_list.addItem(item)

        # Populate chain servers list
        if self.chain:
            for server_id in self.chain.get("servers", []):
                # Find the server name from the full list
                server_name = next(
                    (s.get("name") for s in self.all_servers if s.get("id") == server_id), "Unknown Server")
                item = QListWidgetItem(server_name)
                item.setData(Qt.UserRole, server_id)
                self.chain_list.addItem(item)

    def add_servers_to_chain(self):
        for item in self.available_list.selectedItems():
            self.chain_list.addItem(item.clone())
            # Remove from available list by taking the row, not the item itself
            self.available_list.takeItem(self.available_list.row(item))

    def remove_servers_from_chain(self):
        for item in self.chain_list.selectedItems():
            self.available_list.addItem(item.clone())
            self.chain_list.takeItem(self.chain_list.row(item))

    def get_chain_data(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, self.tr("Input Error"), self.tr(
                "Chain name cannot be empty."))
            return None

        server_ids = [self.chain_list.item(i).data(Qt.UserRole)
                      for i in range(self.chain_list.count())]

        if len(server_ids) < 2:
            QMessageBox.warning(self, self.tr("Input Error"), self.tr(
                "A chain must contain at least two servers."))
            return None

        chain_id = self.chain.get(
            "id") if self.chain else f"chain_{uuid.uuid4()}"

        return {"id": chain_id, "name": name, "servers": server_ids}


class ChainManagerDialog(QDialog):
    """
    A dialog to manage a list of server chains.
    """

    def __init__(self, parent, chains, all_servers):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Chain Manager"))
        self.setMinimumSize(600, 400)

        self.chains = chains
        self.all_servers = all_servers

        main_layout = QVBoxLayout(self)

        self.chain_list_widget = QListWidget()
        main_layout.addWidget(self.chain_list_widget)

        button_layout = QHBoxLayout()
        add_button = QPushButton(self.tr("Add"))
        add_button.clicked.connect(self.add_chain)
        edit_button = QPushButton(self.tr("Edit"))
        edit_button.clicked.connect(self.edit_chain)
        delete_button = QPushButton(self.tr("Delete"))
        delete_button.clicked.connect(self.delete_chain)
        save_button = QPushButton(self.tr("Save & Close"))
        save_button.clicked.connect(self.accept)

        button_layout.addStretch()
        button_layout.addWidget(add_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(save_button)
        main_layout.addLayout(button_layout)

        self.populate_list()

    def populate_list(self):
        self.chain_list_widget.clear()
        for chain in self.chains:
            # Display name and number of servers
            display_text = f"{chain.get('name')} ({len(chain.get('servers', []))} servers)"
            self.chain_list_widget.addItem(display_text)

    def add_chain(self):
        dialog = ChainEditDialog(self, self.all_servers)
        if dialog.exec() == QDialog.Accepted:
            new_chain = dialog.get_chain_data()
            if new_chain:
                self.chains.append(new_chain)
                self.populate_list()

    def edit_chain(self):
        selected_item = self.chain_list_widget.currentItem()
        if not selected_item:
            return
        index = self.chain_list_widget.row(selected_item)
        dialog = ChainEditDialog(
            self, self.all_servers, chain=self.chains[index])
        if dialog.exec() == QDialog.Accepted:
            updated_chain = dialog.get_chain_data()
            if updated_chain:
                self.chains[index] = updated_chain
                self.populate_list()

    def delete_chain(self):
        selected_item = self.chain_list_widget.currentItem()
        if not selected_item:
            return
        index = self.chain_list_widget.row(selected_item)
        chain_name = self.chains[index].get("name")
        reply = QMessageBox.question(self, self.tr("Confirm Deletion"),
                                     self.tr("Are you sure you want to delete the chain '{}'?").format(chain_name))
        if reply == QMessageBox.Yes:
            del self.chains[index]
            self.populate_list()

    def get_chains(self):
        return self.chains

    # This is for compatibility with the main window which reuses the method name
    def get_subscriptions(self):
        return self.get_chains()
