from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QPushButton,
    QDialog,
)
from PySide6.QtCore import Qt

from constants import APP_VERSION, GITHUB_RELEASES_URL


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("About Onix"))
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        title_label = QLabel("Onix")
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        version_label = QLabel(self.tr("Version: {}").format(APP_VERSION))
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)

        github_link = QLabel(
            f'<a href="{GITHUB_RELEASES_URL}">{self.tr("GitHub Releases Page")}</a>')
        github_link.setOpenExternalLinks(True)
        github_link.setAlignment(Qt.AlignCenter)
        layout.addWidget(github_link)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button, alignment=Qt.AlignCenter)
