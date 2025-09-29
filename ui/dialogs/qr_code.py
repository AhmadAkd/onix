import io
import qrcode

from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QDialog,
)
from PySide6.QtGui import QPixmap


class QRCodeDialog(QDialog):
    def __init__(self, server_link, server_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("QR Code for {}").format(server_name))

        layout = QVBoxLayout(self)
        qr_label = QLabel()

        try:
            qr_img = qrcode.make(server_link)
            buf = io.BytesIO()
            qr_img.save(buf, format="PNG")
            img_bytes = buf.getvalue()
            pixmap = QPixmap()
            pixmap.loadFromData(img_bytes)
            qr_label.setPixmap(pixmap)
        except Exception as e:
            qr_label.setText(
                self.tr("Could not generate QR code: {}").format(e))

        layout.addWidget(qr_label)
