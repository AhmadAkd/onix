"""
Zero-Trust Security Dashboard View
نمایش و مدیریت امنیت Zero-Trust
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QGroupBox,
    QGridLayout,
    QTextEdit,
    QComboBox,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QInputDialog,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from services.zero_trust_security import get_zero_trust_service, Identity, TrustLevel
from constants import LogLevel
import time
from typing import Dict, Any
from collections import deque


class IdentityDialog(QDialog):
    """دیالوگ ثبت هویت"""

    def __init__(self, parent=None, identity: Identity = None):
        super().__init__(parent)
        self.identity = identity
        self.setup_ui()

        if identity:
            self.load_identity_data()

    def setup_ui(self):
        """راه‌اندازی UI"""
        self.setWindowTitle("Register Identity")
        self.setModal(True)
        self.resize(400, 300)

        layout = QVBoxLayout(self)

        # فرم تنظیمات
        form_layout = QFormLayout()

        # ID
        self.id_input = QLineEdit()
        form_layout.addRow("Identity ID:", self.id_input)

        # نام
        self.name_input = QLineEdit()
        form_layout.addRow("Name:", self.name_input)

        # نوع
        self.type_combo = QComboBox()
        self.type_combo.addItems(["user", "device", "service"])
        form_layout.addRow("Type:", self.type_combo)

        # سطح اعتماد
        self.trust_combo = QComboBox()
        self.trust_combo.addItems([level.name for level in TrustLevel])
        form_layout.addRow("Trust Level:", self.trust_combo)

        layout.addLayout(form_layout)

        # دکمه‌ها
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def load_identity_data(self):
        """بارگذاری داده هویت"""
        if not self.identity:
            return

        self.id_input.setText(self.identity.id)
        self.name_input.setText(self.identity.name)
        self.type_combo.setCurrentText(self.identity.type)
        self.trust_combo.setCurrentText(self.identity.trust_level.name)

    def get_identity_data(self) -> Identity:
        """دریافت داده هویت"""
        return Identity(
            id=self.id_input.text(),
            name=self.name_input.text(),
            type=self.type_combo.currentText(),
            trust_level=TrustLevel[self.trust_combo.currentText()],
            last_verified=time.time(),
        )


class PolicyDialog(QDialog):
    """دیالوگ ایجاد/ویرایش سیاست"""

    def __init__(self, parent=None, policy_data: Dict[str, Any] = None):
        super().__init__(parent)
        self.policy_data = policy_data
        self.setup_ui()

        if policy_data:
            self.load_policy_data()

    def setup_ui(self):
        """راه‌اندازی UI"""
        self.setWindowTitle("Security Policy")
        self.setModal(True)
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        # فرم تنظیمات
        form_layout = QFormLayout()

        # نام سیاست
        self.name_input = QLineEdit()
        form_layout.addRow("Policy Name:", self.name_input)

        # نوع هویت
        self.identity_types_input = QLineEdit()
        self.identity_types_input.setPlaceholderText("user,device,service")
        form_layout.addRow("Identity Types:", self.identity_types_input)

        # حداقل سطح اعتماد
        self.min_trust_combo = QComboBox()
        self.min_trust_combo.addItems([level.name for level in TrustLevel])
        form_layout.addRow("Min Trust Level:", self.min_trust_combo)

        # منابع مجاز
        self.resources_input = QLineEdit()
        self.resources_input.setPlaceholderText("resource1,resource2,*")
        form_layout.addRow("Resources:", self.resources_input)

        # IP های مجاز
        self.allowed_ips_input = QLineEdit()
        self.allowed_ips_input.setPlaceholderText("192.168.1.0/24,10.0.0.0/8")
        form_layout.addRow("Allowed IPs:", self.allowed_ips_input)

        # عمل
        self.action_combo = QComboBox()
        self.action_combo.addItems(["allow", "deny", "require_verification"])
        form_layout.addRow("Action:", self.action_combo)

        layout.addLayout(form_layout)

        # دکمه‌ها
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def load_policy_data(self):
        """بارگذاری داده سیاست"""
        if not self.policy_data:
            return

        self.name_input.setText(self.policy_data.get("name", ""))
        self.identity_types_input.setText(
            ",".join(self.policy_data.get("identity_types", []))
        )
        self.min_trust_combo.setCurrentText(
            TrustLevel(self.policy_data.get("min_trust_level", 0)).name
        )
        self.resources_input.setText(",".join(self.policy_data.get("resources", [])))
        self.allowed_ips_input.setText(
            ",".join(self.policy_data.get("allowed_ips", []))
        )
        self.action_combo.setCurrentText(self.policy_data.get("action", "deny"))

    def get_policy_data(self) -> Dict[str, Any]:
        """دریافت داده سیاست"""
        return {
            "name": self.name_input.text(),
            "identity_types": [
                t.strip()
                for t in self.identity_types_input.text().split(",")
                if t.strip()
            ],
            "min_trust_level": TrustLevel[self.min_trust_combo.currentText()].value,
            "resources": [
                r.strip() for r in self.resources_input.text().split(",") if r.strip()
            ],
            "allowed_ips": [
                ip.strip()
                for ip in self.allowed_ips_input.text().split(",")
                if ip.strip()
            ],
            "action": self.action_combo.currentText(),
        }


class SecurityChartWidget(QWidget):
    """ویجت نمودار امنیتی"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self.data_points = deque(maxlen=100)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_chart)
        self.update_timer.start(2000)

    def add_data_point(self, value: float, label: str = ""):
        """اضافه کردن نقطه داده"""
        self.data_points.append(
            {"timestamp": time.time(), "value": value, "label": label}
        )

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
        values = [p["value"] for p in self.data_points]
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

        painter.setPen(QPen(QColor(239, 68, 68), 2))

        points = []
        for i, point in enumerate(self.data_points):
            x = margin + (i / (len(self.data_points) - 1)) * (width - 2 * margin)
            y = (
                height
                - margin
                - ((point["value"] - min_val) / (max_val - min_val))
                * (height - 2 * margin)
            )
            points.append((x, y))

        for i in range(len(points) - 1):
            painter.drawLine(
                points[i][0], points[i][1], points[i + 1][0], points[i + 1][1]
            )

        # رسم نقاط
        painter.setBrush(QBrush(QColor(239, 68, 68)))
        for x, y in points:
            painter.drawEllipse(x - 2, y - 2, 4, 4)


def create_zero_trust_view(main_window) -> QWidget:
    """ایجاد ویو Zero-Trust Dashboard"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # عنوان اصلی
    title = QLabel("Zero-Trust Security Dashboard")
    title.setFont(QFont("Arial", 16, QFont.Bold))
    title.setAlignment(Qt.AlignCenter)
    layout.addWidget(title)

    # تب‌ها
    tab_widget = QTabWidget()

    # تب Identities
    identities_tab = create_identities_tab(main_window)
    tab_widget.addTab(identities_tab, "Identities")

    # تب Policies
    policies_tab = create_policies_tab(main_window)
    tab_widget.addTab(policies_tab, "Policies")

    # تب Access Control
    access_tab = create_access_control_tab(main_window)
    tab_widget.addTab(access_tab, "Access Control")

    # تب Security Events
    events_tab = create_security_events_tab(main_window)
    tab_widget.addTab(events_tab, "Security Events")

    # تب Analytics
    analytics_tab = create_security_analytics_tab(main_window)
    tab_widget.addTab(analytics_tab, "Analytics")

    layout.addWidget(tab_widget)

    return widget


def create_identities_tab(main_window) -> QWidget:
    """ایجاد تب Identities"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # دکمه‌های کنترل
    control_layout = QHBoxLayout()

    add_identity_button = QPushButton("Add Identity")
    add_identity_button.clicked.connect(lambda: add_identity(main_window, widget))
    control_layout.addWidget(add_identity_button)

    verify_identity_button = QPushButton("Verify Identity")
    verify_identity_button.clicked.connect(lambda: verify_identity(main_window, widget))
    control_layout.addWidget(verify_identity_button)

    refresh_button = QPushButton("Refresh")
    refresh_button.clicked.connect(lambda: refresh_identities(main_window, widget))
    control_layout.addWidget(refresh_button)

    layout.addLayout(control_layout)

    # جدول هویت‌ها
    identities_group = QGroupBox("Registered Identities")
    identities_layout = QVBoxLayout(identities_group)

    identities_table = QTableWidget(0, 5)
    identities_table.setHorizontalHeaderLabels(
        ["ID", "Name", "Type", "Trust Level", "Last Verified"]
    )
    identities_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    identities_layout.addWidget(identities_table)

    layout.addWidget(identities_group)

    # ذخیره رفرنس‌ها
    widget.identities_table = identities_table

    # بارگذاری هویت‌های موجود
    refresh_identities(main_window, widget)

    return widget


def create_policies_tab(main_window) -> QWidget:
    """ایجاد تب Policies"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # دکمه‌های کنترل
    control_layout = QHBoxLayout()

    add_policy_button = QPushButton("Add Policy")
    add_policy_button.clicked.connect(lambda: add_policy(main_window, widget))
    control_layout.addWidget(add_policy_button)

    edit_policy_button = QPushButton("Edit Policy")
    edit_policy_button.clicked.connect(lambda: edit_policy(main_window, widget))
    control_layout.addWidget(edit_policy_button)

    delete_policy_button = QPushButton("Delete Policy")
    delete_policy_button.clicked.connect(lambda: delete_policy(main_window, widget))
    control_layout.addWidget(delete_policy_button)

    refresh_button = QPushButton("Refresh")
    refresh_button.clicked.connect(lambda: refresh_policies(main_window, widget))
    control_layout.addWidget(refresh_button)

    layout.addLayout(control_layout)

    # جدول سیاست‌ها
    policies_group = QGroupBox("Security Policies")
    policies_layout = QVBoxLayout(policies_group)

    policies_table = QTableWidget(0, 4)
    policies_table.setHorizontalHeaderLabels(
        ["Name", "Identity Types", "Min Trust Level", "Action"]
    )
    policies_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    policies_layout.addWidget(policies_table)

    layout.addWidget(policies_group)

    # ذخیره رفرنس‌ها
    widget.policies_table = policies_table

    # بارگذاری سیاست‌های موجود
    refresh_policies(main_window, widget)

    return widget


def create_access_control_tab(main_window) -> QWidget:
    """ایجاد تب Access Control"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # تنظیمات درخواست دسترسی
    request_group = QGroupBox("Access Request")
    request_layout = QGridLayout(request_group)

    # Identity ID
    request_layout.addWidget(QLabel("Identity ID:"), 0, 0)
    identity_id_input = QLineEdit()
    request_layout.addWidget(identity_id_input, 0, 1)

    # Resource
    request_layout.addWidget(QLabel("Resource:"), 1, 0)
    resource_input = QLineEdit()
    resource_input.setText("api/data")
    request_layout.addWidget(resource_input, 1, 1)

    # Action
    request_layout.addWidget(QLabel("Action:"), 2, 0)
    action_input = QLineEdit()
    action_input.setText("read")
    request_layout.addWidget(action_input, 2, 1)

    # Source IP
    request_layout.addWidget(QLabel("Source IP:"), 3, 0)
    source_ip_input = QLineEdit()
    source_ip_input.setText("192.168.1.100")
    request_layout.addWidget(source_ip_input, 3, 1)

    # User Agent
    request_layout.addWidget(QLabel("User Agent:"), 4, 0)
    user_agent_input = QLineEdit()
    user_agent_input.setText("Mozilla/5.0...")
    request_layout.addWidget(user_agent_input, 4, 1)

    # دکمه درخواست
    request_access_button = QPushButton("Request Access")
    request_access_button.clicked.connect(lambda: request_access(main_window, widget))
    request_layout.addWidget(request_access_button, 5, 0, 1, 2)

    layout.addWidget(request_group)

    # نتایج دسترسی
    results_group = QGroupBox("Access Results")
    results_layout = QVBoxLayout(results_group)

    results_text = QTextEdit()
    results_text.setMaximumHeight(150)
    results_text.setReadOnly(True)
    results_layout.addWidget(results_text)

    layout.addWidget(results_group)

    # لاگ دسترسی‌ها
    log_group = QGroupBox("Access Log")
    log_layout = QVBoxLayout(log_group)

    log_table = QTableWidget(0, 4)
    log_table.setHorizontalHeaderLabels(["Identity", "Resource", "Allowed", "Reason"])
    log_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    log_layout.addWidget(log_table)

    refresh_log_button = QPushButton("Refresh Log")
    refresh_log_button.clicked.connect(lambda: refresh_access_log(main_window, widget))
    log_layout.addWidget(refresh_log_button)

    layout.addWidget(log_group)

    # ذخیره رفرنس‌ها
    widget.identity_id_input = identity_id_input
    widget.resource_input = resource_input
    widget.action_input = action_input
    widget.source_ip_input = source_ip_input
    widget.user_agent_input = user_agent_input
    widget.results_text = results_text
    widget.log_table = log_table

    return widget


def create_security_events_tab(main_window) -> QWidget:
    """ایجاد تب Security Events"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # فیلترها
    filter_group = QGroupBox("Filters")
    filter_layout = QHBoxLayout(filter_group)

    filter_layout.addWidget(QLabel("Severity:"))
    severity_combo = QComboBox()
    severity_combo.addItems(["All", "Low", "Medium", "High", "Critical"])
    filter_layout.addWidget(severity_combo)

    filter_layout.addWidget(QLabel("Type:"))
    type_combo = QComboBox()
    type_combo.addItems(
        ["All", "threat_detected", "access_denied", "verification_failed"]
    )
    filter_layout.addWidget(type_combo)

    filter_button = QPushButton("Filter")
    filter_button.clicked.connect(lambda: filter_events(main_window, widget))
    filter_layout.addWidget(filter_button)

    layout.addWidget(filter_group)

    # جدول رویدادها
    events_group = QGroupBox("Security Events")
    events_layout = QVBoxLayout(events_group)

    events_table = QTableWidget(0, 5)
    events_table.setHorizontalHeaderLabels(
        ["Time", "Type", "Severity", "Identity", "Description"]
    )
    events_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    events_layout.addWidget(events_table)

    refresh_events_button = QPushButton("Refresh Events")
    refresh_events_button.clicked.connect(
        lambda: refresh_security_events(main_window, widget)
    )
    events_layout.addWidget(refresh_events_button)

    layout.addWidget(events_group)

    # ذخیره رفرنس‌ها
    widget.severity_combo = severity_combo
    widget.type_combo = type_combo
    widget.events_table = events_table

    # بارگذاری رویدادها
    refresh_security_events(main_window, widget)

    return widget


def create_security_analytics_tab(main_window) -> QWidget:
    """ایجاد تب Analytics"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # نمودار امنیتی
    chart_group = QGroupBox("Security Chart")
    chart_layout = QVBoxLayout(chart_group)

    chart_widget = SecurityChartWidget()
    chart_layout.addWidget(chart_widget)

    layout.addWidget(chart_group)

    # معیارهای امنیتی
    metrics_group = QGroupBox("Security Metrics")
    metrics_layout = QGridLayout(metrics_group)

    # برچسب‌های معیارها
    identities_label = QLabel("Registered Identities:")
    identities_value = QLabel("0")
    metrics_layout.addWidget(identities_label, 0, 0)
    metrics_layout.addWidget(identities_value, 0, 1)

    policies_label = QLabel("Active Policies:")
    policies_value = QLabel("0")
    metrics_layout.addWidget(policies_label, 1, 0)
    metrics_layout.addWidget(policies_value, 1, 1)

    events_label = QLabel("Security Events:")
    events_value = QLabel("0")
    metrics_layout.addWidget(events_label, 2, 0)
    metrics_layout.addWidget(events_value, 2, 1)

    threats_label = QLabel("Threat Patterns:")
    threats_value = QLabel("0")
    metrics_layout.addWidget(threats_label, 3, 0)
    metrics_layout.addWidget(threats_value, 3, 1)

    layout.addWidget(metrics_group)

    # تایمر به‌روزرسانی
    update_timer = QTimer()
    update_timer.timeout.connect(lambda: update_security_analytics(main_window, widget))
    update_timer.start(3000)  # هر 3 ثانیه

    # ذخیره رفرنس‌ها
    widget.chart_widget = chart_widget
    widget.identities_value = identities_value
    widget.policies_value = policies_value
    widget.events_value = events_value
    widget.threats_value = threats_value
    widget.update_timer = update_timer

    return widget


# توابع کمکی
def add_identity(main_window, widget):
    """اضافه کردن هویت"""
    dialog = IdentityDialog(main_window)
    if dialog.exec() == QDialog.Accepted:
        try:
            identity = dialog.get_identity_data()
            service = get_zero_trust_service()
            if service.register_identity(identity):
                QMessageBox.information(
                    main_window,
                    "Success",
                    f"Identity '{identity.name}' registered successfully!",
                )
                refresh_identities(main_window, widget)
            else:
                QMessageBox.warning(main_window, "Error", "Failed to register identity")
        except Exception as e:
            QMessageBox.warning(main_window, "Error", f"Registration failed: {e}")


def verify_identity(main_window, widget):
    """تأیید هویت"""
    identity_id, ok = QInputDialog.getText(
        main_window, "Verify Identity", "Enter Identity ID:"
    )
    if ok and identity_id:
        try:
            service = get_zero_trust_service()
            credentials = {"password": "valid_password"}  # شبیه‌سازی
            verified, trust_level = service.verify_identity(identity_id, credentials)

            if verified:
                QMessageBox.information(
                    main_window,
                    "Success",
                    f"Identity verified! Trust Level: {trust_level.name}",
                )
            else:
                QMessageBox.warning(
                    main_window, "Failed", "Identity verification failed"
                )

            refresh_identities(main_window, widget)
        except Exception as e:
            QMessageBox.warning(main_window, "Error", f"Verification failed: {e}")


def refresh_identities(main_window, widget):
    """به‌روزرسانی جدول هویت‌ها"""
    try:
        service = get_zero_trust_service()
        identities = service.identity_verifier.identities

        table = widget.identities_table
        table.setRowCount(len(identities))

        for i, (identity_id, identity) in enumerate(identities.items()):
            table.setItem(i, 0, QTableWidgetItem(identity.id))
            table.setItem(i, 1, QTableWidgetItem(identity.name))
            table.setItem(i, 2, QTableWidgetItem(identity.type))
            table.setItem(i, 3, QTableWidgetItem(identity.trust_level.name))
            table.setItem(
                i,
                4,
                QTableWidgetItem(
                    time.strftime(
                        "%Y-%m-%d %H:%M", time.localtime(identity.last_verified)
                    )
                ),
            )

    except Exception as e:
        print(f"[{LogLevel.ERROR}] Failed to refresh identities: {e}")


def add_policy(main_window, widget):
    """اضافه کردن سیاست"""
    dialog = PolicyDialog(main_window)
    if dialog.exec() == QDialog.Accepted:
        try:
            policy_data = dialog.get_policy_data()
            service = get_zero_trust_service()
            service.policy_engine.add_policy(policy_data["name"], policy_data)
            QMessageBox.information(
                main_window,
                "Success",
                f"Policy '{policy_data['name']}' added successfully!",
            )
            refresh_policies(main_window, widget)
        except Exception as e:
            QMessageBox.warning(main_window, "Error", f"Failed to add policy: {e}")


def edit_policy(main_window, widget):
    """ویرایش سیاست"""
    table = widget.policies_table
    current_row = table.currentRow()
    if current_row < 0:
        QMessageBox.warning(main_window, "Warning", "Please select a policy to edit")
        return

    policy_name = table.item(current_row, 0).text()
    QMessageBox.information(main_window, "Info", f"Edit policy: {policy_name}")


def delete_policy(main_window, widget):
    """حذف سیاست"""
    table = widget.policies_table
    current_row = table.currentRow()
    if current_row < 0:
        QMessageBox.warning(main_window, "Warning", "Please select a policy to delete")
        return

    policy_name = table.item(current_row, 0).text()

    reply = QMessageBox.question(
        main_window,
        "Confirm",
        f"Are you sure you want to delete policy '{policy_name}'?",
        QMessageBox.Yes | QMessageBox.No,
    )

    if reply == QMessageBox.Yes:
        try:
            service = get_zero_trust_service()
            if policy_name in service.policy_engine.policies:
                del service.policy_engine.policies[policy_name]
                refresh_policies(main_window, widget)
                print(f"[{LogLevel.INFO}] Policy deleted: {policy_name}")
        except Exception as e:
            QMessageBox.warning(main_window, "Error", f"Failed to delete policy: {e}")


def refresh_policies(main_window, widget):
    """به‌روزرسانی جدول سیاست‌ها"""
    try:
        service = get_zero_trust_service()
        policies = service.policy_engine.policies

        table = widget.policies_table
        table.setRowCount(len(policies))

        for i, (policy_name, policy) in enumerate(policies.items()):
            table.setItem(i, 0, QTableWidgetItem(policy_name))
            table.setItem(
                i, 1, QTableWidgetItem(", ".join(policy.get("identity_types", [])))
            )
            table.setItem(
                i,
                2,
                QTableWidgetItem(TrustLevel(policy.get("min_trust_level", 0)).name),
            )
            table.setItem(i, 3, QTableWidgetItem(policy.get("action", "deny")))

    except Exception as e:
        print(f"[{LogLevel.ERROR}] Failed to refresh policies: {e}")


def request_access(main_window, widget):
    """درخواست دسترسی"""
    try:
        service = get_zero_trust_service()

        # آماده‌سازی درخواست
        identity_id = widget.identity_id_input.text()
        resource = widget.resource_input.text()
        action = widget.action_input.text()
        source_ip = widget.source_ip_input.text()
        user_agent = widget.user_agent_input.text()

        if not identity_id:
            QMessageBox.warning(main_window, "Warning", "Please enter Identity ID")
            return

        # درخواست دسترسی
        allowed, reason = service.request_access(
            identity_id, resource, action, source_ip, user_agent
        )

        # نمایش نتیجه
        result_text = f"""
Access Request Result:
Identity: {identity_id}
Resource: {resource}
Action: {action}
Source IP: {source_ip}
Allowed: {allowed}
Reason: {reason}
Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}
        """
        widget.results_text.setText(result_text)

        # به‌روزرسانی لاگ
        refresh_access_log(main_window, widget)

    except Exception as e:
        widget.results_text.setText(f"Access request failed: {e}")


def refresh_access_log(main_window, widget):
    """به‌روزرسانی لاگ دسترسی"""
    try:
        service = get_zero_trust_service()
        access_log = list(service.access_log)[-50:]  # آخرین 50 ورودی

        table = widget.log_table
        table.setRowCount(len(access_log))

        for i, log_entry in enumerate(access_log):
            request = log_entry["request"]
            table.setItem(i, 0, QTableWidgetItem(request["identity_id"]))
            table.setItem(i, 1, QTableWidgetItem(request["resource"]))
            table.setItem(
                i, 2, QTableWidgetItem("Yes" if log_entry["allowed"] else "No")
            )
            table.setItem(i, 3, QTableWidgetItem(log_entry["reason"]))

    except Exception as e:
        print(f"[{LogLevel.ERROR}] Failed to refresh access log: {e}")


def filter_events(main_window, widget):
    """فیلتر رویدادها"""
    # پیاده‌سازی فیلتر
    refresh_security_events(main_window, widget)


def refresh_security_events(main_window, widget):
    """به‌روزرسانی رویدادهای امنیتی"""
    try:
        service = get_zero_trust_service()
        events = list(service.security_events)[-50:]  # آخرین 50 رویداد

        table = widget.events_table
        table.setRowCount(len(events))

        for i, event in enumerate(events):
            table.setItem(
                i,
                0,
                QTableWidgetItem(
                    time.strftime("%H:%M:%S", time.localtime(event.timestamp))
                ),
            )
            table.setItem(i, 1, QTableWidgetItem(event.type))
            table.setItem(i, 2, QTableWidgetItem(event.severity))
            table.setItem(i, 3, QTableWidgetItem(event.identity_id))
            table.setItem(i, 4, QTableWidgetItem(event.description))

    except Exception as e:
        print(f"[{LogLevel.ERROR}] Failed to refresh security events: {e}")


def update_security_analytics(main_window, widget):
    """به‌روزرسانی Analytics"""
    try:
        service = get_zero_trust_service()
        status = service.get_security_status()

        # به‌روزرسانی معیارها
        widget.identities_value.setText(str(status.get("registered_identities", 0)))
        widget.policies_value.setText(str(status.get("active_policies", 0)))
        widget.events_value.setText(str(status.get("security_events", 0)))
        widget.threats_value.setText(str(status.get("threat_patterns", 0)))

        # به‌روزرسانی نمودار
        widget.chart_widget.add_data_point(status.get("security_events", 0), "Events")

    except Exception as e:
        print(f"[{LogLevel.ERROR}] Failed to update security analytics: {e}")
