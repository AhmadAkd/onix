"""
Advanced Analytics Dashboard for Onix
Provides comprehensive analytics, charts, and insights
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QGroupBox, QScrollArea, QFrame, QSizePolicy,
    QGridLayout, QProgressBar, QTextEdit, QComboBox, QSpinBox,
    QCheckBox, QSlider, QDateTimeEdit, QCalendarWidget
)
from PySide6.QtCore import Qt, QTimer, Signal, QDateTime, QDate
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QLinearGradient
from services.ai_optimization import AIPerformanceAnalyzer, PerformanceMetrics, OptimizationRecommendation
from services.statistics_service import RealTimeStatisticsService
from constants import LogLevel
import time
import json
from typing import Dict, Any, List, Optional
from collections import deque
import math


class ChartWidget(QWidget):
    """Base class for chart widgets."""

    def __init__(self, parent=None, title: str = ""):
        super().__init__(parent)
        self.title = title
        self.data = deque(maxlen=100)
        self.colors = {
            'primary': QColor(59, 130, 246),
            'secondary': QColor(16, 185, 129),
            'warning': QColor(245, 158, 11),
            'error': QColor(239, 68, 68),
            'background': QColor(249, 250, 251)
        }
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def add_data_point(self, value: float, timestamp: float = None):
        """Add a data point to the chart."""
        if timestamp is None:
            timestamp = time.time()
        self.data.append((timestamp, value))
        self.update()

    def paintEvent(self, event):
        """Paint the chart."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw background
        painter.fillRect(self.rect(), self.colors['background'])

        # Draw title
        if self.title:
            painter.setPen(QPen(QColor(31, 41, 55), 2))
            font = QFont("Arial", 12, QFont.Bold)
            painter.setFont(font)
            painter.drawText(10, 25, self.title)

        # Draw chart content (to be implemented by subclasses)
        self.draw_chart(painter)

    def draw_chart(self, painter: QPainter):
        """Draw the actual chart (to be implemented by subclasses)."""
        pass


class LineChart(ChartWidget):
    """Line chart widget."""

    def __init__(self, parent=None, title: str = "", color: QColor = None):
        super().__init__(parent, title)
        self.color = color or self.colors['primary']
        self.line_width = 2

    def draw_chart(self, painter: QPainter):
        """Draw line chart."""
        if len(self.data) < 2:
            return

        # Calculate chart area
        margin = 40
        chart_rect = self.rect().adjusted(margin, margin, -margin, -margin)

        if chart_rect.width() <= 0 or chart_rect.height() <= 0:
            return

        # Find min/max values
        values = [point[1] for point in self.data]
        min_val = min(values)
        max_val = max(values)

        if max_val == min_val:
            max_val = min_val + 1

        # Draw grid lines
        painter.setPen(QPen(QColor(229, 231, 235), 1))
        for i in range(5):
            y = chart_rect.top() + (i * chart_rect.height() // 4)
            painter.drawLine(chart_rect.left(), y, chart_rect.right(), y)

        # Draw data line
        painter.setPen(QPen(self.color, self.line_width))

        points = []
        for i, (timestamp, value) in enumerate(self.data):
            x = chart_rect.left() + (i * chart_rect.width() // (len(self.data) - 1))
            y = chart_rect.bottom() - ((value - min_val) / (max_val - min_val)) * \
                chart_rect.height()
            points.append((x, y))

        # Draw line
        for i in range(len(points) - 1):
            painter.drawLine(points[i][0], points[i][1],
                             points[i+1][0], points[i+1][1])

        # Draw data points
        painter.setBrush(QBrush(self.color))
        for x, y in points:
            painter.drawEllipse(x - 3, y - 3, 6, 6)


class BarChart(ChartWidget):
    """Bar chart widget."""

    def __init__(self, parent=None, title: str = "", color: QColor = None):
        super().__init__(parent, title)
        self.color = color or self.colors['primary']
        self.bar_width = 20

    def draw_chart(self, painter: QPainter):
        """Draw bar chart."""
        if not self.data:
            return

        # Calculate chart area
        margin = 40
        chart_rect = self.rect().adjusted(margin, margin, -margin, -margin)

        if chart_rect.width() <= 0 or chart_rect.height() <= 0:
            return

        # Find max value
        values = [point[1] for point in self.data]
        max_val = max(values) if values else 1

        # Draw bars
        painter.setBrush(QBrush(self.color))
        painter.setPen(Qt.NoPen)

        bar_width = min(self.bar_width, chart_rect.width() //
                        len(self.data) - 2)

        for i, (timestamp, value) in enumerate(self.data):
            x = chart_rect.left() + (i * (chart_rect.width() // len(self.data)))
            bar_height = (value / max_val) * chart_rect.height()
            y = chart_rect.bottom() - bar_height

            painter.drawRect(x, y, bar_width, bar_height)


class PieChart(ChartWidget):
    """Pie chart widget."""

    def __init__(self, parent=None, title: str = ""):
        super().__init__(parent, title)
        self.slices = {}  # {label: (value, color)}
        self.colors_list = [
            QColor(59, 130, 246),
            QColor(16, 185, 129),
            QColor(245, 158, 11),
            QColor(239, 68, 68),
            QColor(147, 51, 234),
            QColor(236, 72, 153)
        ]

    def set_data(self, data: Dict[str, float]):
        """Set pie chart data."""
        self.slices = {}
        total = sum(data.values())

        for i, (label, value) in enumerate(data.items()):
            if total > 0:
                percentage = (value / total) * 100
                color = self.colors_list[i % len(self.colors_list)]
                self.slices[label] = (percentage, color)

    def draw_chart(self, painter: QPainter):
        """Draw pie chart."""
        if not self.slices:
            return

        # Calculate chart area
        margin = 60
        chart_rect = self.rect().adjusted(margin, margin, -margin, -margin)

        if chart_rect.width() <= 0 or chart_rect.height() <= 0:
            return

        # Calculate pie chart dimensions
        center_x = chart_rect.center().x()
        center_y = chart_rect.center().y()
        radius = min(chart_rect.width(), chart_rect.height()) // 2 - 10

        # Draw pie slices
        start_angle = 0
        for label, (percentage, color) in self.slices.items():
            span_angle = int(percentage * 3.6)  # Convert percentage to degrees

            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawPie(center_x - radius, center_y - radius,
                            radius * 2, radius * 2, start_angle * 16, span_angle * 16)

            # Draw label
            angle_rad = math.radians(start_angle + span_angle / 2)
            label_x = center_x + (radius * 0.7) * math.cos(angle_rad)
            label_y = center_y + (radius * 0.7) * math.sin(angle_rad)

            painter.setPen(QPen(QColor(31, 41, 55), 2))
            font = QFont("Arial", 8)
            painter.setFont(font)
            painter.drawText(label_x - 20, label_y,
                             f"{label}\n{percentage:.1f}%")

            start_angle += span_angle


class MetricCard(QFrame):
    """Metric display card."""

    def __init__(self, title: str, value: str, unit: str = "",
                 trend: str = "neutral", parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.unit = unit
        self.trend = trend  # "up", "down", "neutral"

        self.setup_ui()
        self.setup_style()

    def setup_ui(self):
        """Setup metric card UI."""
        self.setFrameStyle(QFrame.StyledPanel)
        self.setLineWidth(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # Title
        self.title_label = QLabel(self.title)
        self.title_label.setObjectName("metricTitle")
        layout.addWidget(self.title_label)

        # Value and unit
        value_layout = QHBoxLayout()

        self.value_label = QLabel(self.value)
        self.value_label.setObjectName("metricValue")
        value_layout.addWidget(self.value_label)

        if self.unit:
            self.unit_label = QLabel(self.unit)
            self.unit_label.setObjectName("metricUnit")
            value_layout.addWidget(self.unit_label)

        value_layout.addStretch()
        layout.addLayout(value_layout)

        # Trend indicator
        if self.trend != "neutral":
            trend_text = "↗" if self.trend == "up" else "↘"
            self.trend_label = QLabel(trend_text)
            self.trend_label.setObjectName("metricTrend")
            layout.addWidget(self.trend_label)

    def setup_style(self):
        """Setup metric card styling."""
        trend_colors = {
            "up": "#10b981",
            "down": "#ef4444",
            "neutral": "#6b7280"
        }

        trend_color = trend_colors.get(self.trend, "#6b7280")

        self.setStyleSheet(f"""
            MetricCard {{
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 8px;
            }}
            QLabel#metricTitle {{
                font-size: 12px;
                color: #6b7280;
                font-weight: 500;
            }}
            QLabel#metricValue {{
                font-size: 24px;
                color: #1f2937;
                font-weight: 700;
            }}
            QLabel#metricUnit {{
                font-size: 14px;
                color: #6b7280;
                font-weight: 500;
            }}
            QLabel#metricTrend {{
                font-size: 16px;
                color: {trend_color};
                font-weight: bold;
            }}
        """)

    def update_value(self, value: str, trend: str = None):
        """Update metric value and trend."""
        self.value = value
        self.value_label.setText(value)

        if trend is not None:
            self.trend = trend
            if hasattr(self, 'trend_label'):
                trend_text = "↗" if trend == "up" else "↘" if trend == "down" else "→"
                self.trend_label.setText(trend_text)


def create_analytics_view(main_window) -> QWidget:
    """Create the analytics dashboard view."""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(20)

    # Header
    header_layout = QHBoxLayout()

    title_label = QLabel("Analytics Dashboard")
    title_label.setObjectName("viewTitle")
    header_layout.addWidget(title_label)

    header_layout.addStretch()

    # Refresh button
    refresh_button = QPushButton("Refresh")
    refresh_button.clicked.connect(
        lambda: refresh_analytics(main_window, widget))
    header_layout.addWidget(refresh_button)

    layout.addLayout(header_layout)

    # Create tab widget
    tab_widget = QTabWidget()

    # Overview tab
    overview_tab = create_overview_tab(main_window)
    tab_widget.addTab(overview_tab, "Overview")

    # Performance tab
    performance_tab = create_performance_tab(main_window)
    tab_widget.addTab(performance_tab, "Performance")

    # AI Insights tab
    ai_tab = create_ai_insights_tab(main_window)
    tab_widget.addTab(ai_tab, "AI Insights")

    # Traffic Analysis tab
    traffic_tab = create_traffic_analysis_tab(main_window)
    tab_widget.addTab(traffic_tab, "Traffic Analysis")

    layout.addWidget(tab_widget)

    # Setup refresh timer
    refresh_timer = QTimer()
    refresh_timer.timeout.connect(
        lambda: refresh_analytics(main_window, widget))
    refresh_timer.start(5000)  # Refresh every 5 seconds

    return widget


def create_overview_tab(main_window) -> QWidget:
    """Create overview tab."""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setSpacing(20)

    # Key metrics row
    metrics_layout = QHBoxLayout()

    # Connection status
    status_card = MetricCard("Connection Status", "Connected", "", "up")
    metrics_layout.addWidget(status_card)

    # Current speed
    speed_card = MetricCard("Current Speed", "45.2", "Mbps", "up")
    metrics_layout.addWidget(speed_card)

    # Ping
    ping_card = MetricCard("Ping", "23", "ms", "down")
    metrics_layout.addWidget(ping_card)

    # Uptime
    uptime_card = MetricCard("Uptime", "2h 34m", "", "neutral")
    metrics_layout.addWidget(uptime_card)

    layout.addLayout(metrics_layout)

    # Charts row
    charts_layout = QHBoxLayout()

    # Speed chart
    speed_chart = LineChart(title="Speed Over Time",
                            color=QColor(59, 130, 246))
    charts_layout.addWidget(speed_chart)

    # Ping chart
    ping_chart = LineChart(title="Ping Over Time", color=QColor(16, 185, 129))
    charts_layout.addWidget(ping_chart)

    layout.addLayout(charts_layout)

    # Server distribution pie chart
    pie_chart = PieChart(title="Server Distribution")
    pie_data = {
        "US East": 35,
        "US West": 25,
        "Europe": 20,
        "Asia": 15,
        "Other": 5
    }
    pie_chart.set_data(pie_data)
    pie_chart.setMaximumHeight(300)
    layout.addWidget(pie_chart)

    return widget


def create_performance_tab(main_window) -> QWidget:
    """Create performance analysis tab."""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setSpacing(20)

    # Performance metrics
    perf_group = QGroupBox("Performance Metrics")
    perf_layout = QGridLayout(perf_group)

    # CPU Usage
    cpu_label = QLabel("CPU Usage:")
    cpu_progress = QProgressBar()
    cpu_progress.setValue(45)
    perf_layout.addWidget(cpu_label, 0, 0)
    perf_layout.addWidget(cpu_progress, 0, 1)

    # Memory Usage
    memory_label = QLabel("Memory Usage:")
    memory_progress = QProgressBar()
    memory_progress.setValue(67)
    perf_layout.addWidget(memory_label, 1, 0)
    perf_layout.addWidget(memory_progress, 1, 1)

    # Network Usage
    network_label = QLabel("Network Usage:")
    network_progress = QProgressBar()
    network_progress.setValue(23)
    perf_layout.addWidget(network_label, 2, 0)
    perf_layout.addWidget(network_progress, 2, 1)

    layout.addWidget(perf_group)

    # Performance charts
    charts_layout = QHBoxLayout()

    # CPU chart
    cpu_chart = LineChart(title="CPU Usage", color=QColor(239, 68, 68))
    charts_layout.addWidget(cpu_chart)

    # Memory chart
    memory_chart = LineChart(title="Memory Usage", color=QColor(245, 158, 11))
    charts_layout.addWidget(memory_chart)

    layout.addLayout(charts_layout)

    return widget


def create_ai_insights_tab(main_window) -> QWidget:
    """Create AI insights tab."""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setSpacing(20)

    # AI Recommendations
    recommendations_group = QGroupBox("AI Recommendations")
    recommendations_layout = QVBoxLayout(recommendations_group)

    # Sample recommendations
    recommendations = [
        "Switch to US East server for better performance",
        "Enable compression to reduce bandwidth usage",
        "Consider upgrading to premium plan for faster speeds"
    ]

    for i, rec in enumerate(recommendations):
        rec_label = QLabel(f"{i+1}. {rec}")
        rec_label.setWordWrap(True)
        rec_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                background-color: #f3f4f6;
                border-radius: 4px;
                margin: 2px;
            }
        """)
        recommendations_layout.addWidget(rec_label)

    layout.addWidget(recommendations_group)

    # AI Analysis
    analysis_group = QGroupBox("AI Analysis")
    analysis_layout = QVBoxLayout(analysis_group)

    analysis_text = QTextEdit()
    analysis_text.setReadOnly(True)
    analysis_text.setMaximumHeight(200)
    analysis_text.setPlainText("""
    AI Analysis Summary:
    
    • Traffic patterns show peak usage between 7-9 PM
    • Server performance is optimal during off-peak hours
    • Recommended to implement load balancing
    • Consider implementing predictive failover
    • Network stability is above average (94.2%)
    """)
    analysis_layout.addWidget(analysis_text)

    layout.addWidget(analysis_group)

    return widget


def create_traffic_analysis_tab(main_window) -> QWidget:
    """Create traffic analysis tab."""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setSpacing(20)

    # Traffic patterns
    patterns_group = QGroupBox("Traffic Patterns")
    patterns_layout = QVBoxLayout(patterns_group)

    # Hourly usage chart
    hourly_chart = BarChart(title="Hourly Usage", color=QColor(147, 51, 234))
    patterns_layout.addWidget(hourly_chart)

    layout.addWidget(patterns_group)

    # Geographic distribution
    geo_group = QGroupBox("Geographic Distribution")
    geo_layout = QVBoxLayout(geo_group)

    geo_pie = PieChart(title="Traffic by Region")
    geo_data = {
        "North America": 45,
        "Europe": 30,
        "Asia": 20,
        "Other": 5
    }
    geo_pie.set_data(geo_data)
    geo_pie.setMaximumHeight(250)
    geo_layout.addWidget(geo_pie)

    layout.addWidget(geo_group)

    return widget


def refresh_analytics(main_window, widget: QWidget):
    """Refresh analytics data."""
    try:
        # Update metrics if AI analyzer is available
        if hasattr(main_window, 'ai_analyzer'):
            summary = main_window.ai_analyzer.get_performance_summary()

            # Update metric cards
            for child in widget.findChildren(MetricCard):
                if "Speed" in child.title:
                    speed = summary.get('avg_download_speed', 0)
                    child.update_value(f"{speed:.1f}")
                elif "Ping" in child.title:
                    ping = summary.get('avg_ping', 0)
                    child.update_value(f"{ping:.0f}")

        # Update charts with sample data
        for chart in widget.findChildren(ChartWidget):
            if isinstance(chart, LineChart):
                # Add random data point
                import random
                value = random.uniform(10, 100)
                chart.add_data_point(value)
            elif isinstance(chart, BarChart):
                # Add random data point
                import random
                value = random.uniform(0, 50)
                chart.add_data_point(value)

    except Exception as e:
        if hasattr(main_window, 'log'):
            main_window.log(f"Error refreshing analytics: {e}", LogLevel.ERROR)
