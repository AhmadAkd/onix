from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QRadioButton, QButtonGroup, QFileDialog, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from services.export_service import ExportService


class ExportDialog(QDialog):
    def __init__(self, parent, servers, health_stats=None):
        super().__init__(parent)
        self.parent = parent
        self.servers = servers
        self.health_stats = health_stats or {}
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle(self.tr("Export Data"))
        self.setModal(True)
        self.setMinimumSize(400, 200)
        self.setMaximumSize(600, 400)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel(self.tr("Choose export format:"))
        title_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        layout.addWidget(title_label)

        # Export options
        self.button_group = QButtonGroup()

        self.server_list_radio = QRadioButton(self.tr("Server List Only"))
        self.server_list_radio.setChecked(True)
        self.button_group.addButton(self.server_list_radio, 0)
        layout.addWidget(self.server_list_radio)

        self.health_stats_radio = QRadioButton(
            self.tr("Health Check Statistics"))
        self.button_group.addButton(self.health_stats_radio, 1)
        layout.addWidget(self.health_stats_radio)

        # Description
        desc_label = QLabel(self.tr(
            "Server List: Basic server information\nHealth Stats: Includes ping data and health check results"))
        desc_label.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(desc_label)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()

        self.export_button = QPushButton(
            QIcon(":/icons/file-text.svg"), self.tr("Export"))
        self.export_button.clicked.connect(self.export_data)
        button_layout.addWidget(self.export_button)

        self.cancel_button = QPushButton(self.tr("Cancel"))
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def export_data(self):
        """Export data based on selected option."""
        try:
            # Get file path
            file_filter = "CSV Files (*.csv);;All Files (*)"
            filename, _ = QFileDialog.getSaveFileName(
                self,
                self.tr("Save Export File"),
                "",
                file_filter
            )

            if not filename:
                return

            # Ensure .csv extension
            if not filename.endswith('.csv'):
                filename += '.csv'

            # Export based on selection
            if self.button_group.checkedId() == 0:
                # Server list only
                filepath = ExportService.export_server_list_to_csv(
                    self.servers, filename)
                message = self.tr("Server list exported successfully!")
            else:
                # Health statistics
                filepath = ExportService.export_health_stats_to_csv(
                    self.servers, self.health_stats, filename)
                message = self.tr("Health statistics exported successfully!")

            # Show success message
            QMessageBox.information(
                self,
                self.tr("Export Successful"),
                f"{message}\n\n{self.tr('File saved to:')} {filepath}"
            )

            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                self.tr("Export Error"),
                self.tr("Failed to export data: {}").format(str(e))
            )
