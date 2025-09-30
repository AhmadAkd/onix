"""
Traffic Management View
نمایش و مدیریت ترافیک و Load Balancing
"""

from PySide6.QtWidgets import QInputDialog
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QGroupBox, QGridLayout, QComboBox, QSpinBox,
    QCheckBox, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDialog, QDialogButtonBox,
    QFormLayout
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from services.traffic_management import (
    get_traffic_service, TrafficRule, TrafficPriority, LoadBalancingStrategy
)
from constants import LogLevel
import time
from collections import deque


class TrafficRuleDialog(QDialog):
    """دیالوگ ایجاد/ویرایش قانون ترافیک"""

    def __init__(self, parent=None, rule: TrafficRule = None):
        super().__init__(parent)
        self.rule = rule
        self.setup_ui()

        if rule:
            self.load_rule_data()

    def setup_ui(self):
        """راه‌اندازی UI"""
        self.setWindowTitle("Traffic Rule")
        self.setModal(True)
        self.resize(400, 300)

        layout = QVBoxLayout(self)

        # فرم تنظیمات
        form_layout = QFormLayout()

        # نام قانون
        self.name_input = QLineEdit()
        form_layout.addRow("Rule Name:", self.name_input)

        # اولویت
        self.priority_combo = QComboBox()
        self.priority_combo.addItems([p.name for p in TrafficPriority])
        form_layout.addRow("Priority:", self.priority_combo)

        # الگوی مبدأ
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("e.g., 192.168.1.* or *")
        form_layout.addRow("Source Pattern:", self.source_input)

        # الگوی مقصد
        self.destination_input = QLineEdit()
        self.destination_input.setPlaceholderText("e.g., *.example.com or *")
        form_layout.addRow("Destination Pattern:", self.destination_input)

        # محدودیت پهنای باند
        self.bandwidth_input = QSpinBox()
        self.bandwidth_input.setRange(1, 10000)
        self.bandwidth_input.setValue(1000)
        self.bandwidth_input.setSuffix(" KB/s")
        form_layout.addRow("Bandwidth Limit:", self.bandwidth_input)

        # فعال/غیرفعال
        self.enabled_checkbox = QCheckBox("Enabled")
        self.enabled_checkbox.setChecked(True)
        form_layout.addRow("", self.enabled_checkbox)

        layout.addLayout(form_layout)

        # دکمه‌ها
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def load_rule_data(self):
        """بارگذاری داده‌های قانون"""
        if not self.rule:
            return

        self.name_input.setText(self.rule.name)
        self.priority_combo.setCurrentText(self.rule.priority.name)
        self.source_input.setText(self.rule.source_pattern)
        self.destination_input.setText(self.rule.destination_pattern)
        self.bandwidth_input.setValue(self.rule.bandwidth_limit)
        self.enabled_checkbox.setChecked(self.rule.enabled)

    def get_rule_data(self) -> TrafficRule:
        """دریافت داده‌های قانون"""
        return TrafficRule(
            name=self.name_input.text(),
            priority=TrafficPriority[self.priority_combo.currentText()],
            source_pattern=self.source_input.text(),
            destination_pattern=self.destination_input.text(),
            bandwidth_limit=self.bandwidth_input.value(),
            enabled=self.enabled_checkbox.isChecked()
        )


class TrafficChartWidget(QWidget):
    """ویجت نمودار ترافیک"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self.data_points = deque(maxlen=100)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_chart)
        self.update_timer.start(1000)

    def add_data_point(self, value: float):
        """اضافه کردن نقطه داده"""
        self.data_points.append({
            'timestamp': time.time(),
            'value': value
        })

    def update_chart(self):
        """به‌روزرسانی نمودار"""
        self.update()

    def paintEvent(self, event):
        """رسم نمودار"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # پس‌زمینه
        painter.fillRect(self.rect(), QColor(248, 249, 250))

        if not self.data_points:
            return

        # محاسبه مقادیر
        values = [p['value'] for p in self.data_points]
        if not values:
            return

        min_val = min(values)
        max_val = max(values)
        if max_val == min_val:
            max_val = min_val + 1

        # رسم نمودار
        width = self.width()
        height = self.height()
        margin = 20

        painter.setPen(QPen(QColor(59, 130, 246), 2))

        points = []
        for i, point in enumerate(self.data_points):
            x = margin + (i / (len(self.data_points) - 1)) * \
                (width - 2 * margin)
            y = height - margin - \
                ((point['value'] - min_val) / (max_val - min_val)) * \
                (height - 2 * margin)
            points.append((x, y))

        for i in range(len(points) - 1):
            painter.drawLine(points[i][0], points[i][1],
                             points[i+1][0], points[i+1][1])

        # رسم نقاط
        painter.setBrush(QBrush(QColor(59, 130, 246)))
        for x, y in points:
            painter.drawEllipse(x - 2, y - 2, 4, 4)


def create_traffic_view(main_window) -> QWidget:
    """ایجاد ویو مدیریت ترافیک"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # عنوان اصلی
    title = QLabel("Traffic Management")
    title.setFont(QFont("Arial", 16, QFont.Bold))
    title.setAlignment(Qt.AlignCenter)
    layout.addWidget(title)

    # تب‌ها
    tab_widget = QTabWidget()

    # تب Traffic Shaping
    shaping_tab = create_traffic_shaping_tab(main_window)
    tab_widget.addTab(shaping_tab, "Traffic Shaping")

    # تب Load Balancing
    balancing_tab = create_load_balancing_tab(main_window)
    tab_widget.addTab(balancing_tab, "Load Balancing")

    # تب Analytics
    analytics_tab = create_traffic_analytics_tab(main_window)
    tab_widget.addTab(analytics_tab, "Analytics")

    layout.addWidget(tab_widget)

    return widget


def create_traffic_shaping_tab(main_window) -> QWidget:
    """ایجاد تب Traffic Shaping"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # دکمه‌های کنترل
    control_layout = QHBoxLayout()

    add_rule_button = QPushButton("Add Rule")
    add_rule_button.clicked.connect(
        lambda: add_traffic_rule(main_window, widget))
    control_layout.addWidget(add_rule_button)

    remove_rule_button = QPushButton("Remove Rule")
    remove_rule_button.clicked.connect(
        lambda: remove_traffic_rule(main_window, widget))
    control_layout.addLayout(control_layout)

    # جدول قوانین
    rules_group = QGroupBox("Traffic Rules")
    rules_layout = QVBoxLayout(rules_group)

    rules_table = QTableWidget(0, 6)
    rules_table.setHorizontalHeaderLabels([
        "Name", "Priority", "Source", "Destination", "Bandwidth", "Enabled"
    ])
    rules_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    rules_layout.addWidget(rules_table)

    layout.addWidget(rules_group)

    # ذخیره رفرنس‌ها
    widget.rules_table = rules_table

    # بارگذاری قوانین موجود
    refresh_traffic_rules(main_window, widget)

    return widget


def create_load_balancing_tab(main_window) -> QWidget:
    """ایجاد تب Load Balancing"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # تنظیمات Load Balancing
    config_group = QGroupBox("Load Balancing Configuration")
    config_layout = QGridLayout(config_group)

    # استراتژی
    config_layout.addWidget(QLabel("Strategy:"), 0, 0)
    strategy_combo = QComboBox()
    strategy_combo.addItems([s.value for s in LoadBalancingStrategy])
    config_layout.addWidget(strategy_combo, 0, 1)

    # دکمه اعمال
    apply_button = QPushButton("Apply Strategy")
    apply_button.clicked.connect(lambda: apply_load_balancing_strategy(
        main_window, strategy_combo.currentText()))
    config_layout.addWidget(apply_button, 0, 2)

    layout.addWidget(config_group)

    # آمار سرورها
    servers_group = QGroupBox("Server Statistics")
    servers_layout = QVBoxLayout(servers_group)

    servers_table = QTableWidget(0, 5)
    servers_table.setHorizontalHeaderLabels([
        "Server ID", "Connections", "Requests", "Response Time", "Error Rate"
    ])
    servers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    servers_layout.addWidget(servers_table)

    # دکمه‌های کنترل سرور
    server_control_layout = QHBoxLayout()

    add_server_button = QPushButton("Add Server")
    add_server_button.clicked.connect(
        lambda: add_server_to_balancer(main_window, widget))
    server_control_layout.addWidget(add_server_button)

    remove_server_button = QPushButton("Remove Server")
    remove_server_button.clicked.connect(
        lambda: remove_server_from_balancer(main_window, widget))
    server_control_layout.addWidget(remove_server_button)

    refresh_button = QPushButton("Refresh")
    refresh_button.clicked.connect(
        lambda: refresh_server_stats(main_window, widget))
    server_control_layout.addWidget(refresh_button)

    servers_layout.addLayout(server_control_layout)
    layout.addWidget(servers_group)

    # ذخیره رفرنس‌ها
    widget.strategy_combo = strategy_combo
    widget.servers_table = servers_table

    # بارگذاری آمار سرورها
    refresh_server_stats(main_window, widget)

    return widget


def create_traffic_analytics_tab(main_window) -> QWidget:
    """ایجاد تب Analytics"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # نمودار ترافیک
    chart_group = QGroupBox("Traffic Chart")
    chart_layout = QVBoxLayout(chart_group)

    chart_widget = TrafficChartWidget()
    chart_layout.addWidget(chart_widget)

    layout.addWidget(chart_group)

    # معیارهای کلیدی
    metrics_group = QGroupBox("Key Metrics")
    metrics_layout = QGridLayout(metrics_group)

    # برچسب‌های معیارها
    bandwidth_label = QLabel("Current Bandwidth:")
    bandwidth_value = QLabel("0 MB/s")
    metrics_layout.addWidget(bandwidth_label, 0, 0)
    metrics_layout.addWidget(bandwidth_value, 0, 1)

    connections_label = QLabel("Active Connections:")
    connections_value = QLabel("0")
    metrics_layout.addWidget(connections_label, 1, 0)
    metrics_layout.addWidget(connections_value, 1, 1)

    response_time_label = QLabel("Avg Response Time:")
    response_time_value = QLabel("0 ms")
    metrics_layout.addWidget(response_time_label, 2, 0)
    metrics_layout.addWidget(response_time_value, 2, 1)

    error_rate_label = QLabel("Error Rate:")
    error_rate_value = QLabel("0%")
    metrics_layout.addWidget(error_rate_label, 3, 0)
    metrics_layout.addWidget(error_rate_value, 3, 1)

    layout.addWidget(metrics_group)

    # تایمر به‌روزرسانی
    update_timer = QTimer()
    update_timer.timeout.connect(
        lambda: update_traffic_analytics(main_window, widget))
    update_timer.start(2000)  # هر 2 ثانیه

    # ذخیره رفرنس‌ها
    widget.chart_widget = chart_widget
    widget.bandwidth_value = bandwidth_value
    widget.connections_value = connections_value
    widget.response_time_value = response_time_value
    widget.error_rate_value = error_rate_value
    widget.update_timer = update_timer

    return widget

# توابع کمکی


def add_traffic_rule(main_window, widget):
    """اضافه کردن قانون ترافیک"""
    dialog = TrafficRuleDialog(main_window)
    if dialog.exec() == QDialog.Accepted:
        try:
            rule = dialog.get_rule_data()
            service = get_traffic_service()
            service.add_traffic_rule(rule)
            refresh_traffic_rules(main_window, widget)
            print(f"[{LogLevel.INFO}] Traffic rule added: {rule.name}")
        except Exception as e:
            QMessageBox.warning(main_window, "Error",
                                f"Failed to add rule: {e}")


def remove_traffic_rule(main_window, widget):
    """حذف قانون ترافیک"""
    table = widget.rules_table
    current_row = table.currentRow()
    if current_row < 0:
        QMessageBox.warning(main_window, "Warning",
                            "Please select a rule to remove")
        return

    rule_name = table.item(current_row, 0).text()

    reply = QMessageBox.question(
        main_window, "Confirm", f"Are you sure you want to remove rule '{rule_name}'?",
        QMessageBox.Yes | QMessageBox.No
    )

    if reply == QMessageBox.Yes:
        try:
            service = get_traffic_service()
            service.remove_traffic_rule(rule_name)
            refresh_traffic_rules(main_window, widget)
            print(f"[{LogLevel.INFO}] Traffic rule removed: {rule_name}")
        except Exception as e:
            QMessageBox.warning(main_window, "Error",
                                f"Failed to remove rule: {e}")


def refresh_traffic_rules(main_window, widget):
    """به‌روزرسانی جدول قوانین"""
    try:
        service = get_traffic_service()
        rules = service.traffic_shaping.rules

        table = widget.rules_table
        table.setRowCount(len(rules))

        for i, rule in enumerate(rules):
            table.setItem(i, 0, QTableWidgetItem(rule.name))
            table.setItem(i, 1, QTableWidgetItem(rule.priority.name))
            table.setItem(i, 2, QTableWidgetItem(rule.source_pattern))
            table.setItem(i, 3, QTableWidgetItem(rule.destination_pattern))
            table.setItem(i, 4, QTableWidgetItem(
                f"{rule.bandwidth_limit} KB/s"))
            table.setItem(i, 5, QTableWidgetItem(
                "Yes" if rule.enabled else "No"))

    except Exception as e:
        print(f"[{LogLevel.ERROR}] Failed to refresh traffic rules: {e}")


def apply_load_balancing_strategy(main_window, strategy_name: str):
    """اعمال استراتژی Load Balancing"""
    try:
        service = get_traffic_service()
        strategy = LoadBalancingStrategy(strategy_name)
        service.set_load_balancing_strategy(strategy)
        print(f"[{LogLevel.INFO}] Load balancing strategy applied: {strategy_name}")
    except Exception as e:
        QMessageBox.warning(main_window, "Error",
                            f"Failed to apply strategy: {e}")


def add_server_to_balancer(main_window, widget):
    """اضافه کردن سرور به Load Balancer"""
    server_id, ok = QInputDialog.getText(
        main_window, "Add Server", "Enter Server ID:")
    if ok and server_id:
        try:
            service = get_traffic_service()
            service.add_server_to_balancer(server_id)
            refresh_server_stats(main_window, widget)
            print(f"[{LogLevel.INFO}] Server added to load balancer: {server_id}")
        except Exception as e:
            QMessageBox.warning(main_window, "Error",
                                f"Failed to add server: {e}")


def remove_server_from_balancer(main_window, widget):
    """حذف سرور از Load Balancer"""
    table = widget.servers_table
    current_row = table.currentRow()
    if current_row < 0:
        QMessageBox.warning(main_window, "Warning",
                            "Please select a server to remove")
        return

    server_id = table.item(current_row, 0).text()

    reply = QMessageBox.question(
        main_window, "Confirm", f"Are you sure you want to remove server '{server_id}'?",
        QMessageBox.Yes | QMessageBox.No
    )

    if reply == QMessageBox.Yes:
        try:
            service = get_traffic_service()
            service.remove_server_from_balancer(server_id)
            refresh_server_stats(main_window, widget)
            print(
                f"[{LogLevel.INFO}] Server removed from load balancer: {server_id}")
        except Exception as e:
            QMessageBox.warning(main_window, "Error",
                                f"Failed to remove server: {e}")


def refresh_server_stats(main_window, widget):
    """به‌روزرسانی آمار سرورها"""
    try:
        service = get_traffic_service()
        stats = service.load_balancer.get_server_stats()

        table = widget.servers_table
        table.setRowCount(len(stats))

        for i, (server_id, server_stats) in enumerate(stats.items()):
            table.setItem(i, 0, QTableWidgetItem(server_id))
            table.setItem(i, 1, QTableWidgetItem(
                str(server_stats.active_connections)))
            table.setItem(i, 2, QTableWidgetItem(
                str(server_stats.total_requests)))
            table.setItem(i, 3, QTableWidgetItem(
                f"{server_stats.response_time:.1f} ms"))
            table.setItem(i, 4, QTableWidgetItem(
                f"{server_stats.error_rate:.2%}"))

    except Exception as e:
        print(f"[{LogLevel.ERROR}] Failed to refresh server stats: {e}")


def update_traffic_analytics(main_window, widget):
    """به‌روزرسانی Analytics"""
    try:
        service = get_traffic_service()
        analysis = service.traffic_analyzer.get_traffic_analysis()

        if analysis:
            # به‌روزرسانی نمودار
            widget.chart_widget.add_data_point(
                analysis.get('current_bandwidth', 0))

            # به‌روزرسانی معیارها
            widget.bandwidth_value.setText(
                f"{analysis.get('current_bandwidth', 0):.1f} MB/s")
            widget.connections_value.setText(
                str(analysis.get('total_samples', 0)))
            widget.response_time_value.setText(
                f"{analysis.get('average_response_time', 0):.1f} ms")
            widget.error_rate_value.setText(
                f"{analysis.get('average_error_rate', 0):.2%}")

    except Exception as e:
        print(f"[{LogLevel.ERROR}] Failed to update analytics: {e}")


# Import اضافی
