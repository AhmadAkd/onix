
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QAction, QPainter, QFont, QColor, QPixmap
from PySide6.QtCore import QSize, Qt, QRect
from constants import TRAY_SHOW, TRAY_QUIT


class TrayManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.app = QApplication.instance()
        self.tray_icon = QSystemTrayIcon(self.main_window)

        # Set Icon from resource file
        icon = QIcon(":/icons/app-icon.svg")
        self.main_window.setWindowIcon(icon)
        self.tray_icon.setIcon(icon)

        # Create Menu
        tray_menu = QMenu()
        show_action = QAction(TRAY_SHOW, self.main_window)
        show_action.triggered.connect(self.show_window)
        quit_action = QAction(TRAY_QUIT, self.main_window)
        quit_action.triggered.connect(self.app.quit)

        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()

    def show_window(self):
        self.main_window.show()
        self.main_window.activateWindow()

    def show_message(self, title, message, icon=QSystemTrayIcon.Information, msecs=2000):
        self.tray_icon.showMessage(title, message, icon, msecs)

    def update_tray_icon(self, up_speed, down_speed):
        """
        Dynamically creates an icon with speed information and updates the system tray.
        """
        # Use a slightly larger pixmap for better text rendering
        pixmap_size = 64
        pixmap = QPixmap(pixmap_size, pixmap_size)
        pixmap.fill(Qt.transparent)  # Transparent background

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw the base application icon
        base_icon = QIcon(":/icons/app-icon.svg")
        base_pixmap = base_icon.pixmap(QSize(pixmap_size, pixmap_size))
        painter.drawPixmap(0, 0, base_pixmap)

        # --- Text Drawing ---
        # Set a clear, small font
        font = QFont("Segoe UI", 16, QFont.Bold)
        painter.setFont(font)

        # Set text color with a slight outline for better visibility
        text_color = QColor("white")
        outline_color = QColor("black")

        # Format speed text to be compact
        up_text = self.main_window.format_speed(up_speed, compact=True)
        down_text = self.main_window.format_speed(down_speed, compact=True)

        # Define positions for text (top for upload, bottom for download)
        up_rect = QRect(0, 0, pixmap_size, pixmap_size // 2)
        down_rect = QRect(0, pixmap_size // 2, pixmap_size, pixmap_size // 2)

        # Draw outline (by drawing text slightly offset in black)
        painter.setPen(outline_color)
        painter.drawText(up_rect.translated(1, 1), Qt.AlignCenter, up_text)
        painter.drawText(down_rect.translated(1, 1), Qt.AlignCenter, down_text)

        # Draw main text
        painter.setPen(text_color)
        painter.drawText(up_rect, Qt.AlignCenter, up_text)
        painter.drawText(down_rect, Qt.AlignCenter, down_text)

        painter.end()
        self.tray_icon.setIcon(QIcon(pixmap))
