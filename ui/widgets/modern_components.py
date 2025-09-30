"""
Modern UI Components for Onix
Provides modern, customizable UI components with advanced features
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QSlider, QProgressBar, QFrame, QSizePolicy,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QLinearGradient, QFontMetrics


class ModernCard(QFrame):
    """Modern card component with shadow and rounded corners."""

    def __init__(self, parent=None, title: str = "", content: str = "",
                 shadow_color: QColor = QColor(0, 0, 0, 30),
                 corner_radius: int = 12,
                 padding: int = 16):
        super().__init__(parent)
        self.title = title
        self.content = content
        self.shadow_color = shadow_color
        self.corner_radius = corner_radius
        self.padding = padding

        self.setup_ui()
        self.setup_style()

    def setup_ui(self):
        """Setup the card UI."""
        self.setFrameStyle(QFrame.NoFrame)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(
            self.padding, self.padding, self.padding, self.padding)
        self.main_layout.setSpacing(12)

        # Title label
        if self.title:
            self.title_label = QLabel(self.title)
            self.title_label.setObjectName("cardTitle")
            self.title_label.setWordWrap(True)
            self.main_layout.addWidget(self.title_label)

        # Content label
        if self.content:
            self.content_label = QLabel(self.content)
            self.content_label.setObjectName("cardContent")
            self.content_label.setWordWrap(True)
            self.content_label.setAlignment(Qt.AlignTop)
            self.main_layout.addWidget(self.content_label)

    def setup_style(self):
        """Setup the card styling."""
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(self.shadow_color)
        self.setGraphicsEffect(shadow)

        # Set background and border
        self.setStyleSheet(f"""
            ModernCard {{
                background-color: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: {self.corner_radius}px;
            }}
            QLabel#cardTitle {{
                font-size: 16px;
                font-weight: 600;
                color: #1a1a1a;
                margin-bottom: 4px;
            }}
            QLabel#cardContent {{
                font-size: 14px;
                color: #666666;
                line-height: 1.4;
            }}
        """)


class AnimatedButton(QPushButton):
    """Modern animated button with hover effects."""

    def __init__(self, text: str = "", parent=None,
                 primary_color: QColor = QColor(59, 130, 246),
                 hover_color: QColor = QColor(37, 99, 235),
                 text_color: QColor = QColor(255, 255, 255),
                 corner_radius: int = 8,
                 padding: int = 12):
        super().__init__(text, parent)
        self.primary_color = primary_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.corner_radius = corner_radius
        self.padding = padding

        self.setup_style()
        self.setup_animations()

    def setup_style(self):
        """Setup button styling."""
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setMinimumHeight(40)

        # Set initial style
        self.update_style(self.primary_color)

    def setup_animations(self):
        """Setup button animations."""
        # Hover animation
        self.hover_animation = QPropertyAnimation(self, b"geometry")
        self.hover_animation.setDuration(200)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)

        # Color animation
        self.color_animation = QPropertyAnimation(self, b"styleSheet")
        self.color_animation.setDuration(200)
        self.color_animation.setEasingCurve(QEasingCurve.OutCubic)

    def update_style(self, bg_color: QColor):
        """Update button style with given background color."""
        style = f"""
            QPushButton {{
                background-color: {bg_color.name()};
                color: {self.text_color.name()};
                border: none;
                border-radius: {self.corner_radius}px;
                padding: {self.padding}px;
                font-size: 14px;
                font-weight: 500;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {self.hover_color.name()};
                transform: translateY(-1px);
            }}
            QPushButton:pressed {{
                background-color: {self.hover_color.darker(120).name()};
                transform: translateY(0px);
            }}
            QPushButton:disabled {{
                background-color: #e5e7eb;
                color: #9ca3af;
            }}
        """
        self.setStyleSheet(style)

    def enterEvent(self, event):
        """Handle mouse enter event."""
        super().enterEvent(event)
        self.update_style(self.hover_color)

    def leaveEvent(self, event):
        """Handle mouse leave event."""
        super().leaveEvent(event)
        self.update_style(self.primary_color)


class ProgressRing(QWidget):
    """Modern circular progress indicator."""

    def __init__(self, parent=None, size: int = 100,
                 line_width: int = 8,
                 primary_color: QColor = QColor(59, 130, 246),
                 background_color: QColor = QColor(229, 231, 235),
                 show_percentage: bool = True):
        super().__init__(parent)
        self.size = size
        self.line_width = line_width
        self.primary_color = primary_color
        self.background_color = background_color
        self.show_percentage = show_percentage
        self.progress = 0.0

        self.setFixedSize(size, size)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def set_progress(self, value: float):
        """Set progress value (0.0 to 1.0)."""
        self.progress = max(0.0, min(1.0, value))
        self.update()

    def paintEvent(self, event):
        """Paint the progress ring."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate dimensions
        rect = self.rect()
        center = rect.center()
        radius = min(rect.width(), rect.height()) // 2 - self.line_width // 2

        # Draw background circle
        painter.setPen(QPen(self.background_color,
                       self.line_width, Qt.SolidLine, Qt.RoundCap))
        painter.drawEllipse(center, radius, radius)

        # Draw progress arc
        if self.progress > 0:
            painter.setPen(
                QPen(self.primary_color, self.line_width, Qt.SolidLine, Qt.RoundCap))
            start_angle = 90 * 16  # Start from top
            # Negative for clockwise
            span_angle = int(-self.progress * 360 * 16)
            painter.drawArc(center.x() - radius, center.y() - radius,
                            radius * 2, radius * 2, start_angle, span_angle)

        # Draw percentage text
        if self.show_percentage:
            painter.setPen(QPen(self.primary_color, 2))
            font = QFont("Arial", 12, QFont.Bold)
            painter.setFont(font)

            text = f"{int(self.progress * 100)}%"
            font_metrics = QFontMetrics(font)
            text_rect = font_metrics.boundingRect(text)
            text_x = center.x() - text_rect.width() // 2
            text_y = center.y() + text_rect.height() // 4

            painter.drawText(text_x, text_y, text)


class ModernSlider(QSlider):
    """Modern styled slider with custom appearance."""

    def __init__(self, orientation: Qt.Orientation = Qt.Horizontal, parent=None,
                 primary_color: QColor = QColor(59, 130, 246),
                 track_color: QColor = QColor(229, 231, 235),
                 handle_color: QColor = QColor(255, 255, 255),
                 track_height: int = 6,
                 handle_size: int = 20):
        super().__init__(orientation, parent)
        self.primary_color = primary_color
        self.track_color = track_color
        self.handle_color = handle_color
        self.track_height = track_height
        self.handle_size = handle_size

        self.setup_style()

    def setup_style(self):
        """Setup slider styling."""
        if self.orientation() == Qt.Horizontal:
            self.setMinimumHeight(40)
        else:
            self.setMinimumWidth(40)

        style = f"""
            QSlider::groove:horizontal {{
                height: {self.track_height}px;
                background: {self.track_color.name()};
                border-radius: {self.track_height // 2}px;
            }}
            QSlider::handle:horizontal {{
                background: {self.handle_color.name()};
                border: 2px solid {self.primary_color.name()};
                width: {self.handle_size}px;
                height: {self.handle_size}px;
                border-radius: {self.handle_size // 2}px;
                margin: -{(self.handle_size - self.track_height) // 2}px 0;
            }}
            QSlider::handle:horizontal:hover {{
                background: {self.primary_color.name()};
            }}
            QSlider::sub-page:horizontal {{
                background: {self.primary_color.name()};
                border-radius: {self.track_height // 2}px;
            }}
        """

        if self.orientation() == Qt.Vertical:
            style = style.replace("horizontal", "vertical")
            style = style.replace("height:", "width:")
            style = style.replace("width:", "height:")

        self.setStyleSheet(style)


class StatusIndicator(QWidget):
    """Modern status indicator with different states."""

    # Status states
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"
    LOADING = "loading"

    def __init__(self, parent=None, status: str = INFO, size: int = 16):
        super().__init__(parent)
        self.status = status
        self.size = size
        self.animation_angle = 0

        self.setFixedSize(size, size)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Setup animation timer for loading state
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)

        if status == self.LOADING:
            self.animation_timer.start(50)  # 20 FPS

    def set_status(self, status: str):
        """Set the status indicator state."""
        self.status = status
        if status == self.LOADING:
            self.animation_timer.start(50)
        else:
            self.animation_timer.stop()
        self.update()

    def update_animation(self):
        """Update loading animation."""
        self.animation_angle = (self.animation_angle + 10) % 360
        self.update()

    def paintEvent(self, event):
        """Paint the status indicator."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        center = rect.center()
        radius = min(rect.width(), rect.height()) // 2 - 2

        # Get color based on status
        color_map = {
            self.SUCCESS: QColor(34, 197, 94),
            self.WARNING: QColor(245, 158, 11),
            self.ERROR: QColor(239, 68, 68),
            self.INFO: QColor(59, 130, 246),
            self.LOADING: QColor(59, 130, 246)
        }

        color = color_map.get(self.status, QColor(107, 114, 128))

        if self.status == self.LOADING:
            # Draw loading spinner
            painter.setPen(QPen(color, 3, Qt.SolidLine, Qt.RoundCap))
            start_angle = self.animation_angle * 16
            span_angle = 270 * 16  # 3/4 circle
            painter.drawArc(center.x() - radius, center.y() - radius,
                            radius * 2, radius * 2, start_angle, span_angle)
        else:
            # Draw filled circle
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, radius, radius)


class ModernTooltip(QWidget):
    """Modern tooltip with custom styling."""

    def __init__(self, text: str, parent=None,
                 bg_color: QColor = QColor(31, 41, 55),
                 text_color: QColor = QColor(255, 255, 255),
                 corner_radius: int = 8,
                 padding: int = 12):
        super().__init__(parent)
        self.text = text
        self.bg_color = bg_color
        self.text_color = text_color
        self.corner_radius = corner_radius
        self.padding = padding

        self.setup_ui()
        self.setup_style()

    def setup_ui(self):
        """Setup tooltip UI."""
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            self.padding, self.padding, self.padding, self.padding)

        self.label = QLabel(self.text)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

    def setup_style(self):
        """Setup tooltip styling."""
        self.setStyleSheet(f"""
            ModernTooltip {{
                background-color: {self.bg_color.name()};
                border-radius: {self.corner_radius}px;
            }}
            QLabel {{
                color: {self.text_color.name()};
                font-size: 12px;
                font-weight: 500;
            }}
        """)


class GradientButton(QPushButton):
    """Button with gradient background."""

    def __init__(self, text: str = "", parent=None,
                 start_color: QColor = QColor(59, 130, 246),
                 end_color: QColor = QColor(147, 51, 234),
                 direction: Qt.Orientation = Qt.Horizontal):
        super().__init__(text, parent)
        self.start_color = start_color
        self.end_color = end_color
        self.direction = direction

        self.setup_style()

    def setup_style(self):
        """Setup gradient button styling."""
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(40)

        # Create gradient
        if self.direction == Qt.Horizontal:
            gradient = QLinearGradient(0, 0, 1, 0)
        else:
            gradient = QLinearGradient(0, 0, 0, 1)

        gradient.setColorAt(0, self.start_color)
        gradient.setColorAt(1, self.end_color)

        # Apply gradient as background
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {self.start_color.name()}, 
                    stop:1 {self.end_color.name()});
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {self.start_color.darker(110).name()}, 
                    stop:1 {self.end_color.darker(110).name()});
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {self.start_color.darker(120).name()}, 
                    stop:1 {self.end_color.darker(120).name()});
            }}
        """)


class ModernProgressBar(QProgressBar):
    """Modern progress bar with custom styling."""

    def __init__(self, parent=None,
                 primary_color: QColor = QColor(59, 130, 246),
                 background_color: QColor = QColor(229, 231, 235),
                 text_color: QColor = QColor(31, 41, 55),
                 height: int = 8,
                 corner_radius: int = 4):
        super().__init__(parent)
        self.primary_color = primary_color
        self.background_color = background_color
        self.text_color = text_color
        self.height = height
        self.corner_radius = corner_radius

        self.setup_style()

    def setup_style(self):
        """Setup progress bar styling."""
        self.setMinimumHeight(self.height)
        self.setMaximumHeight(self.height)

        self.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: {self.corner_radius}px;
                background-color: {self.background_color.name()};
                text-align: center;
                color: {self.text_color.name()};
                font-weight: 500;
            }}
            QProgressBar::chunk {{
                background-color: {self.primary_color.name()};
                border-radius: {self.corner_radius}px;
            }}
        """)


class FloatingActionButton(QPushButton):
    """Floating action button with shadow and animation."""

    def __init__(self, icon_text: str = "+", parent=None,
                 primary_color: QColor = QColor(59, 130, 246),
                 size: int = 56):
        super().__init__(icon_text, parent)
        self.primary_color = primary_color
        self.size = size

        self.setup_ui()
        self.setup_style()
        self.setup_animations()

    def setup_ui(self):
        """Setup FAB UI."""
        self.setFixedSize(self.size, self.size)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)

    def setup_style(self):
        """Setup FAB styling."""
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.primary_color.name()};
                color: white;
                border: none;
                border-radius: {self.size // 2}px;
                font-size: 24px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.primary_color.darker(110).name()};
                transform: scale(1.05);
            }}
            QPushButton:pressed {{
                background-color: {self.primary_color.darker(120).name()};
                transform: scale(0.95);
            }}
        """)

    def setup_animations(self):
        """Setup FAB animations."""
        # Scale animation
        self.scale_animation = QPropertyAnimation(self, b"geometry")
        self.scale_animation.setDuration(200)
        self.scale_animation.setEasingCurve(QEasingCurve.OutCubic)
