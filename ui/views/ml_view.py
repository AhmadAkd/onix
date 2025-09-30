"""
Machine Learning Dashboard View
نمایش و مدیریت یادگیری ماشین
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
    QProgressBar,
    QTextEdit,
    QComboBox,
    QSpinBox,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QDoubleSpinBox,
    QListWidget,
    QListWidgetItem,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from services.ml_optimization import get_ml_service
from constants import LogLevel
import time
import json
from typing import Dict, Any
from collections import deque


class ModelTrainingDialog(QDialog):
    """دیالوگ آموزش مدل"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """راه‌اندازی UI"""
        self.setWindowTitle("Train ML Model")
        self.setModal(True)
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        # فرم تنظیمات
        form_layout = QFormLayout()

        # نام مدل
        self.name_input = QLineEdit()
        self.name_input.setText("performance_model")
        form_layout.addRow("Model Name:", self.name_input)

        # نوع مدل
        self.type_combo = QComboBox()
        self.type_combo.addItems(["linear", "polynomial", "simple"])
        form_layout.addRow("Model Type:", self.type_combo)

        # ویژگی‌های ورودی
        self.features_input = QLineEdit()
        self.features_input.setText("bandwidth,connections,response_time")
        self.features_input.setPlaceholderText("Comma-separated feature names")
        form_layout.addRow("Features:", self.features_input)

        # تعداد داده آموزش
        self.data_count_input = QSpinBox()
        self.data_count_input.setRange(10, 1000)
        self.data_count_input.setValue(100)
        form_layout.addRow("Training Data Count:", self.data_count_input)

        layout.addLayout(form_layout)

        # پیش‌نمایش داده
        preview_group = QGroupBox("Data Preview")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_text = QTextEdit()
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setReadOnly(True)
        preview_layout.addWidget(self.preview_text)

        generate_button = QPushButton("Generate Sample Data")
        generate_button.clicked.connect(self.generate_sample_data)
        preview_layout.addWidget(generate_button)

        layout.addWidget(preview_group)

        # دکمه‌ها
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def generate_sample_data(self):
        """تولید داده نمونه"""
        try:
            features = [f.strip() for f in self.features_input.text().split(",")]
            count = self.data_count_input.value()

            sample_data = []
            for i in range(min(count, 20)):  # نمایش حداکثر 20 نمونه
                data_point = {}
                for feature in features:
                    if feature == "bandwidth":
                        data_point[feature] = round(100 + i * 5 + (i % 3) * 10, 2)
                    elif feature == "connections":
                        data_point[feature] = 50 + i * 2 + (i % 5) * 3
                    elif feature == "response_time":
                        data_point[feature] = round(50 + i * 0.5 + (i % 4) * 2, 1)
                    else:
                        data_point[feature] = round(10 + i * 0.1, 2)

                sample_data.append(data_point)

            self.preview_text.setText(json.dumps(sample_data, indent=2))

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to generate sample data: {e}")

    def get_training_config(self) -> Dict[str, Any]:
        """دریافت پیکربندی آموزش"""
        return {
            "name": self.name_input.text(),
            "type": self.type_combo.currentText(),
            "features": [f.strip() for f in self.features_input.text().split(",")],
            "data_count": self.data_count_input.value(),
        }


class MLChartWidget(QWidget):
    """ویجت نمودار ML"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self.data_points = deque(maxlen=100)
        self.prediction_points = deque(maxlen=100)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_chart)
        self.update_timer.start(1000)

    def add_data_point(self, actual: float, predicted: float = None):
        """اضافه کردن نقطه داده"""
        self.data_points.append(
            {"timestamp": time.time(), "actual": actual, "predicted": predicted}
        )

        if predicted is not None:
            self.prediction_points.append(
                {"timestamp": time.time(), "predicted": predicted}
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
        actual_values = [p["actual"] for p in self.data_points if "actual" in p]
        predicted_values = [
            p["predicted"] for p in self.prediction_points if "predicted" in p
        ]

        if not actual_values:
            return

        all_values = actual_values + predicted_values
        min_val = min(all_values)
        max_val = max(all_values)
        if max_val == min_val:
            max_val = min_val + 1

        # رسم نمودار
        width = self.width()
        height = self.height()
        margin = 20

        # رسم خط داده‌های واقعی
        painter.setPen(QPen(QColor(59, 130, 246), 2))
        self._draw_line(
            painter, self.data_points, "actual", min_val, max_val, width, height, margin
        )

        # رسم خط پیش‌بینی‌ها
        if predicted_values:
            painter.setPen(QPen(QColor(239, 68, 68), 2, Qt.DashLine))
            self._draw_line(
                painter,
                self.prediction_points,
                "predicted",
                min_val,
                max_val,
                width,
                height,
                margin,
            )

        # رسم نقاط
        painter.setBrush(QBrush(QColor(59, 130, 246)))
        for i, point in enumerate(self.data_points):
            x = margin + (i / (len(self.data_points) - 1)) * (width - 2 * margin)
            y = (
                height
                - margin
                - ((point["actual"] - min_val) / (max_val - min_val))
                * (height - 2 * margin)
            )
            painter.drawEllipse(x - 3, y - 3, 6, 6)

    def _draw_line(
        self, painter, points, value_key, min_val, max_val, width, height, margin
    ):
        """رسم خط"""
        if len(points) < 2:
            return

        line_points = []
        for i, point in enumerate(points):
            if value_key in point:
                x = margin + (i / (len(points) - 1)) * (width - 2 * margin)
                y = (
                    height
                    - margin
                    - ((point[value_key] - min_val) / (max_val - min_val))
                    * (height - 2 * margin)
                )
                line_points.append((x, y))

        for i in range(len(line_points) - 1):
            painter.drawLine(
                line_points[i][0],
                line_points[i][1],
                line_points[i + 1][0],
                line_points[i + 1][1],
            )


def create_ml_view(main_window) -> QWidget:
    """ایجاد ویو ML Dashboard"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # عنوان اصلی
    title = QLabel("Machine Learning Dashboard")
    title.setFont(QFont("Arial", 16, QFont.Bold))
    title.setAlignment(Qt.AlignCenter)
    layout.addWidget(title)

    # تب‌ها
    tab_widget = QTabWidget()

    # تب Models
    models_tab = create_models_tab(main_window)
    tab_widget.addTab(models_tab, "Models")

    # تب Training
    training_tab = create_training_tab(main_window)
    tab_widget.addTab(training_tab, "Training")

    # تب Predictions
    predictions_tab = create_predictions_tab(main_window)
    tab_widget.addTab(predictions_tab, "Predictions")

    # تب Analytics
    analytics_tab = create_analytics_tab(main_window)
    tab_widget.addTab(analytics_tab, "Analytics")

    layout.addWidget(tab_widget)

    return widget


def create_models_tab(main_window) -> QWidget:
    """ایجاد تب Models"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # دکمه‌های کنترل
    control_layout = QHBoxLayout()

    train_button = QPushButton("Train New Model")
    train_button.clicked.connect(lambda: train_new_model(main_window, widget))
    control_layout.addWidget(train_button)

    refresh_button = QPushButton("Refresh Models")
    refresh_button.clicked.connect(lambda: refresh_models(main_window, widget))
    control_layout.addWidget(refresh_button)

    delete_button = QPushButton("Delete Model")
    delete_button.clicked.connect(lambda: delete_model(main_window, widget))
    control_layout.addWidget(delete_button)

    layout.addLayout(control_layout)

    # جدول مدل‌ها
    models_group = QGroupBox("Trained Models")
    models_layout = QVBoxLayout(models_group)

    models_table = QTableWidget(0, 5)
    models_table.setHorizontalHeaderLabels(
        ["Name", "Type", "Accuracy", "Features", "Last Trained"]
    )
    models_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    models_layout.addWidget(models_table)

    layout.addWidget(models_group)

    # ذخیره رفرنس‌ها
    widget.models_table = models_table

    # بارگذاری مدل‌های موجود
    refresh_models(main_window, widget)

    return widget


def create_training_tab(main_window) -> QWidget:
    """ایجاد تب Training"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # تنظیمات آموزش
    config_group = QGroupBox("Training Configuration")
    config_layout = QGridLayout(config_group)

    # نوع مدل
    config_layout.addWidget(QLabel("Model Type:"), 0, 0)
    model_type_combo = QComboBox()
    model_type_combo.addItems(["linear", "polynomial", "simple"])
    config_layout.addWidget(model_type_combo, 0, 1)

    # تعداد داده
    config_layout.addWidget(QLabel("Data Points:"), 1, 0)
    data_points_input = QSpinBox()
    data_points_input.setRange(10, 1000)
    data_points_input.setValue(100)
    config_layout.addWidget(data_points_input, 1, 1)

    # دکمه شروع آموزش
    start_training_button = QPushButton("Start Training")
    start_training_button.clicked.connect(lambda: start_training(main_window, widget))
    config_layout.addWidget(start_training_button, 2, 0, 1, 2)

    layout.addWidget(config_group)

    # پیش‌رفت آموزش
    progress_group = QGroupBox("Training Progress")
    progress_layout = QVBoxLayout(progress_group)

    progress_bar = QProgressBar()
    progress_bar.setVisible(False)
    progress_layout.addWidget(progress_bar)

    status_label = QLabel("Ready to train")
    progress_layout.addWidget(status_label)

    log_text = QTextEdit()
    log_text.setMaximumHeight(150)
    log_text.setReadOnly(True)
    progress_layout.addWidget(log_text)

    layout.addWidget(progress_group)

    # ذخیره رفرنس‌ها
    widget.model_type_combo = model_type_combo
    widget.data_points_input = data_points_input
    widget.progress_bar = progress_bar
    widget.status_label = status_label
    widget.log_text = log_text

    return widget


def create_predictions_tab(main_window) -> QWidget:
    """ایجاد تب Predictions"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # تنظیمات پیش‌بینی
    config_group = QGroupBox("Prediction Configuration")
    config_layout = QGridLayout(config_group)

    # انتخاب مدل
    config_layout.addWidget(QLabel("Model:"), 0, 0)
    model_combo = QComboBox()
    config_layout.addWidget(model_combo, 0, 1)

    # ویژگی‌های ورودی
    config_layout.addWidget(QLabel("Bandwidth:"), 1, 0)
    bandwidth_input = QDoubleSpinBox()
    bandwidth_input.setRange(0, 10000)
    bandwidth_input.setValue(100)
    config_layout.addWidget(bandwidth_input, 1, 1)

    config_layout.addWidget(QLabel("Connections:"), 2, 0)
    connections_input = QSpinBox()
    connections_input.setRange(0, 1000)
    connections_input.setValue(50)
    config_layout.addWidget(connections_input, 2, 1)

    config_layout.addWidget(QLabel("Response Time:"), 3, 0)
    response_time_input = QDoubleSpinBox()
    response_time_input.setRange(0, 1000)
    response_time_input.setValue(50)
    config_layout.addWidget(response_time_input, 3, 1)

    # دکمه پیش‌بینی
    predict_button = QPushButton("Make Prediction")
    predict_button.clicked.connect(lambda: make_prediction(main_window, widget))
    config_layout.addWidget(predict_button, 4, 0, 1, 2)

    layout.addWidget(config_group)

    # نتایج پیش‌بینی
    results_group = QGroupBox("Prediction Results")
    results_layout = QVBoxLayout(results_group)

    results_text = QTextEdit()
    results_text.setMaximumHeight(200)
    results_text.setReadOnly(True)
    results_layout.addWidget(results_text)

    # نمودار پیش‌بینی
    chart_widget = MLChartWidget()
    results_layout.addWidget(chart_widget)

    layout.addWidget(results_group)

    # ذخیره رفرنس‌ها
    widget.model_combo = model_combo
    widget.bandwidth_input = bandwidth_input
    widget.connections_input = connections_input
    widget.response_time_input = response_time_input
    widget.results_text = results_text
    widget.chart_widget = chart_widget

    # بارگذاری مدل‌ها
    refresh_model_combo(main_window, widget)

    return widget


def create_analytics_tab(main_window) -> QWidget:
    """ایجاد تب Analytics"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # معیارهای ML
    metrics_group = QGroupBox("ML Metrics")
    metrics_layout = QGridLayout(metrics_group)

    # برچسب‌های معیارها
    models_count_label = QLabel("Trained Models:")
    models_count_value = QLabel("0")
    metrics_layout.addWidget(models_count_label, 0, 0)
    metrics_layout.addWidget(models_count_value, 0, 1)

    training_data_label = QLabel("Training Data Points:")
    training_data_value = QLabel("0")
    metrics_layout.addWidget(training_data_label, 1, 0)
    metrics_layout.addWidget(training_data_value, 1, 1)

    accuracy_label = QLabel("Average Accuracy:")
    accuracy_value = QLabel("0%")
    metrics_layout.addWidget(accuracy_label, 2, 0)
    metrics_layout.addWidget(accuracy_value, 2, 1)

    predictions_label = QLabel("Total Predictions:")
    predictions_value = QLabel("0")
    metrics_layout.addWidget(predictions_label, 3, 0)
    metrics_layout.addWidget(predictions_value, 3, 1)

    layout.addWidget(metrics_group)

    # توصیه‌های بهینه‌سازی
    recommendations_group = QGroupBox("Optimization Recommendations")
    recommendations_layout = QVBoxLayout(recommendations_group)

    recommendations_list = QListWidget()
    recommendations_layout.addWidget(recommendations_list)

    refresh_recommendations_button = QPushButton("Refresh Recommendations")
    refresh_recommendations_button.clicked.connect(
        lambda: refresh_recommendations(main_window, widget)
    )
    recommendations_layout.addWidget(refresh_recommendations_button)

    layout.addWidget(recommendations_group)

    # تایمر به‌روزرسانی
    update_timer = QTimer()
    update_timer.timeout.connect(lambda: update_ml_analytics(main_window, widget))
    update_timer.start(5000)  # هر 5 ثانیه

    # ذخیره رفرنس‌ها
    widget.models_count_value = models_count_value
    widget.training_data_value = training_data_value
    widget.accuracy_value = accuracy_value
    widget.predictions_value = predictions_value
    widget.recommendations_list = recommendations_list
    widget.update_timer = update_timer

    return widget


# توابع کمکی


def train_new_model(main_window, widget):
    """آموزش مدل جدید"""
    dialog = ModelTrainingDialog(main_window)
    if dialog.exec() == QDialog.Accepted:
        try:
            config = dialog.get_training_config()

            # تولید داده نمونه
            service = get_ml_service()
            for i in range(config["data_count"]):
                features = {
                    "bandwidth": 100 + i * 5 + (i % 3) * 10,
                    "connections": 50 + i * 2 + (i % 5) * 3,
                    "response_time": 50 + i * 0.5 + (i % 4) * 2,
                }
                target = 80 + i * 0.3 + (i % 2) * 5  # شبیه‌سازی هدف
                service.add_performance_data(features, target)

            # آموزش مدل
            model = service.performance_predictor.train_model(
                config["name"], config["type"]
            )
            if model:
                QMessageBox.information(
                    main_window,
                    "Success",
                    f"Model '{model.name}' trained successfully!",
                )
                refresh_models(main_window, widget)
            else:
                QMessageBox.warning(main_window, "Error", "Failed to train model")

        except Exception as e:
            QMessageBox.warning(main_window, "Error", f"Training failed: {e}")


def refresh_models(main_window, widget):
    """به‌روزرسانی جدول مدل‌ها"""
    try:
        service = get_ml_service()
        models = service.performance_predictor.models

        table = widget.models_table
        table.setRowCount(len(models))

        for i, (name, model) in enumerate(models.items()):
            table.setItem(i, 0, QTableWidgetItem(model.name))
            table.setItem(i, 1, QTableWidgetItem(model.model_type))
            table.setItem(i, 2, QTableWidgetItem(f"{model.accuracy:.3f}"))
            table.setItem(i, 3, QTableWidgetItem(", ".join(model.features)))
            table.setItem(
                i,
                4,
                QTableWidgetItem(
                    time.strftime("%Y-%m-%d %H:%M", time.localtime(model.last_trained))
                ),
            )

    except Exception as e:
        print(f"[{LogLevel.ERROR}] Failed to refresh models: {e}")


def delete_model(main_window, widget):
    """حذف مدل"""
    table = widget.models_table
    current_row = table.currentRow()
    if current_row < 0:
        QMessageBox.warning(main_window, "Warning", "Please select a model to delete")
        return

    model_name = table.item(current_row, 0).text()

    reply = QMessageBox.question(
        main_window,
        "Confirm",
        f"Are you sure you want to delete model '{model_name}'?",
        QMessageBox.Yes | QMessageBox.No,
    )

    if reply == QMessageBox.Yes:
        try:
            service = get_ml_service()
            if model_name in service.performance_predictor.models:
                del service.performance_predictor.models[model_name]
                refresh_models(main_window, widget)
                print(f"[{LogLevel.INFO}] Model deleted: {model_name}")
        except Exception as e:
            QMessageBox.warning(main_window, "Error", f"Failed to delete model: {e}")


def start_training(main_window, widget):
    """شروع آموزش"""
    try:
        widget.progress_bar.setVisible(True)
        widget.status_label.setText("Training in progress...")
        widget.log_text.append("Starting model training...")

        # شبیه‌سازی آموزش
        service = get_ml_service()

        # تولید داده نمونه
        data_count = widget.data_points_input.value()
        for i in range(data_count):
            features = {
                "bandwidth": 100 + i * 5 + (i % 3) * 10,
                "connections": 50 + i * 2 + (i % 5) * 3,
                "response_time": 50 + i * 0.5 + (i % 4) * 2,
            }
            target = 80 + i * 0.3 + (i % 2) * 5
            service.add_performance_data(features, target)

            # به‌روزرسانی پیش‌رفت
            progress = int((i + 1) / data_count * 100)
            widget.progress_bar.setValue(progress)

        # آموزش مدل
        model_type = widget.model_type_combo.currentText()
        model = service.performance_predictor.train_model("auto_model", model_type)

        if model:
            widget.status_label.setText("Training completed successfully!")
            widget.log_text.append(
                f"Model trained: {model.name} (accuracy: {model.accuracy:.3f})"
            )
        else:
            widget.status_label.setText("Training failed!")
            widget.log_text.append("Failed to train model")

        widget.progress_bar.setVisible(False)

    except Exception as e:
        widget.status_label.setText("Training failed!")
        widget.log_text.append(f"Error: {e}")
        widget.progress_bar.setVisible(False)


def make_prediction(main_window, widget):
    """انجام پیش‌بینی"""
    try:
        service = get_ml_service()

        # آماده‌سازی ویژگی‌ها
        features = {
            "bandwidth": widget.bandwidth_input.value(),
            "connections": widget.connections_input.value(),
            "response_time": widget.response_time_input.value(),
        }

        # انجام پیش‌بینی
        result = service.predict_performance(features)

        if result:
            # نمایش نتیجه
            result_text = f"""
Prediction Result:
Model: {result.model_name}
Prediction: {result.prediction:.2f}
Confidence: {result.confidence:.2%}
Features Used: {', '.join(result.features_used)}
Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(result.timestamp))}
            """
            widget.results_text.setText(result_text)

            # اضافه کردن به نمودار
            widget.chart_widget.add_data_point(features["bandwidth"], result.prediction)

        else:
            widget.results_text.setText("No model available for prediction")

    except Exception as e:
        widget.results_text.setText(f"Prediction failed: {e}")


def refresh_model_combo(main_window, widget):
    """به‌روزرسانی ComboBox مدل‌ها"""
    try:
        service = get_ml_service()
        models = service.performance_predictor.models

        combo = widget.model_combo
        combo.clear()
        combo.addItems(list(models.keys()))

    except Exception as e:
        print(f"[{LogLevel.ERROR}] Failed to refresh model combo: {e}")


def refresh_recommendations(main_window, widget):
    """به‌روزرسانی توصیه‌ها"""
    try:
        service = get_ml_service()
        recommendations = service.get_optimization_recommendations()

        list_widget = widget.recommendations_list
        list_widget.clear()

        for rec in recommendations:
            item_text = (
                f"[{rec['priority'].upper()}] {rec['title']}: {rec['description']}"
            )
            item = QListWidgetItem(item_text)
            list_widget.addItem(item)

    except Exception as e:
        print(f"[{LogLevel.ERROR}] Failed to refresh recommendations: {e}")


def update_ml_analytics(main_window, widget):
    """به‌روزرسانی Analytics"""
    try:
        service = get_ml_service()
        status = service.get_service_status()

        # به‌روزرسانی معیارها
        widget.models_count_value.setText(str(status.get("models_count", 0)))
        widget.training_data_value.setText(str(status.get("training_data_count", 0)))

        # محاسبه میانگین دقت
        models = service.performance_predictor.models
        if models:
            avg_accuracy = sum(model.accuracy for model in models.values()) / len(
                models
            )
            widget.accuracy_value.setText(f"{avg_accuracy:.1%}")
        else:
            widget.accuracy_value.setText("0%")

        # به‌روزرسانی توصیه‌ها
        refresh_recommendations(main_window, widget)

    except Exception as e:
        print(f"[{LogLevel.ERROR}] Failed to update ML analytics: {e}")
