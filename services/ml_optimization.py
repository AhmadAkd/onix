"""
Machine Learning Optimization Service
سرویس بهینه‌سازی مبتنی بر یادگیری ماشین
"""

import threading
import time
import numpy as np
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass
from collections import deque, defaultdict
from constants import LogLevel
import random


@dataclass
class MLModel:
    """مدل یادگیری ماشین"""

    name: str
    model_type: str
    accuracy: float
    last_trained: float
    features: List[str]
    predictions: Dict[str, Any] = None

    def __post_init__(self):
        if self.predictions is None:
            self.predictions = {}


@dataclass
class TrainingData:
    """داده‌های آموزش"""

    timestamp: float
    features: Dict[str, float]
    target: float
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class PredictionResult:
    """نتیجه پیش‌بینی"""

    model_name: str
    prediction: float
    confidence: float
    timestamp: float
    features_used: List[str]


class AnomalyDetector:
    """تشخیص ناهنجاری"""

    def __init__(self):
        self.data_history = deque(maxlen=1000)
        self.threshold_multiplier = 2.0
        self.is_trained = False
        self.stats = {}

    def add_data_point(self, features: Dict[str, float]):
        """اضافه کردن نقطه داده"""
        self.data_history.append(
            {"timestamp": time.time(), "features": features.copy()}
        )

        # به‌روزرسانی آمار
        self._update_stats()

    def _update_stats(self):
        """به‌روزرسانی آمار"""
        if len(self.data_history) < 10:
            return

        # محاسبه آمار برای هر ویژگی
        for feature_name in self.data_history[0]["features"].keys():
            values = [point["features"][feature_name] for point in self.data_history]

            self.stats[feature_name] = {
                "mean": np.mean(values),
                "std": np.std(values),
                "min": np.min(values),
                "max": np.max(values),
            }

        self.is_trained = True

    def detect_anomaly(
        self, features: Dict[str, float]
    ) -> Tuple[bool, float, Dict[str, Any]]:
        """تشخیص ناهنجاری"""
        if not self.is_trained:
            return False, 0.0, {}

        anomaly_score = 0.0
        anomalies = {}

        for feature_name, value in features.items():
            if feature_name not in self.stats:
                continue

            stats = self.stats[feature_name]
            z_score = abs((value - stats["mean"]) / (stats["std"] + 1e-8))

            if z_score > self.threshold_multiplier:
                anomaly_score += z_score
                anomalies[feature_name] = {
                    "value": value,
                    "expected_mean": stats["mean"],
                    "z_score": z_score,
                    "is_anomaly": True,
                }

        is_anomaly = anomaly_score > len(features) * 0.5
        confidence = min(1.0, anomaly_score / len(features))

        return is_anomaly, confidence, anomalies


class PerformancePredictor:
    """پیش‌بین عملکرد"""

    def __init__(self):
        self.models = {}
        self.training_data = deque(maxlen=5000)
        self.is_training = False

    def add_training_data(
        self, features: Dict[str, float], target: float, metadata: Dict[str, Any] = None
    ):
        """اضافه کردن داده آموزش"""
        self.training_data.append(
            TrainingData(
                timestamp=time.time(),
                features=features.copy(),
                target=target,
                metadata=metadata or {},
            )
        )

    def train_model(self, model_name: str, model_type: str = "linear") -> MLModel:
        """آموزش مدل"""
        if len(self.training_data) < 10:
            return None

        self.is_training = True

        try:
            # آماده‌سازی داده‌ها
            X = []
            y = []
            feature_names = []

            for data in self.training_data:
                features = list(data.features.values())
                X.append(features)
                y.append(data.target)

            if not feature_names:
                feature_names = list(self.training_data[0].features.keys())

            X = np.array(X)
            y = np.array(y)

            # آموزش مدل ساده
            if model_type == "linear":
                model = self._train_linear_model(X, y)
            elif model_type == "polynomial":
                model = self._train_polynomial_model(X, y)
            else:
                model = self._train_simple_model(X, y)

            # ایجاد مدل
            ml_model = MLModel(
                name=model_name,
                model_type=model_type,
                accuracy=model.get("accuracy", 0.8),
                last_trained=time.time(),
                features=feature_names,
                predictions=model,
            )

            self.models[model_name] = ml_model
            print(
                f"[{LogLevel.INFO}] Model trained: {model_name} (accuracy: {ml_model.accuracy:.3f})"
            )

            return ml_model

        except Exception as e:
            print(f"[{LogLevel.ERROR}] Model training failed: {e}")
            return None
        finally:
            self.is_training = False

    def _train_linear_model(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """آموزش مدل خطی"""
        # رگرسیون خطی ساده
        X_with_bias = np.column_stack([np.ones(X.shape[0]), X])
        coefficients = np.linalg.lstsq(X_with_bias, y, rcond=None)[0]

        # محاسبه دقت
        predictions = X_with_bias @ coefficients
        mse = np.mean((y - predictions) ** 2)
        accuracy = max(0, 1 - mse / np.var(y))

        return {"coefficients": coefficients.tolist(), "accuracy": accuracy, "mse": mse}

    def _train_polynomial_model(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """آموزش مدل چندجمله‌ای"""
        # درجه 2 چندجمله‌ای
        X_poly = np.column_stack([X, X**2])
        X_with_bias = np.column_stack([np.ones(X_poly.shape[0]), X_poly])

        coefficients = np.linalg.lstsq(X_with_bias, y, rcond=None)[0]

        # محاسبه دقت
        predictions = X_with_bias @ coefficients
        mse = np.mean((y - predictions) ** 2)
        accuracy = max(0, 1 - mse / np.var(y))

        return {
            "coefficients": coefficients.tolist(),
            "accuracy": accuracy,
            "mse": mse,
            "degree": 2,
        }

    def _train_simple_model(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """آموزش مدل ساده (میانگین)"""
        mean_value = np.mean(y)
        std_value = np.std(y)

        # محاسبه دقت
        predictions = np.full_like(y, mean_value)
        mse = np.mean((y - predictions) ** 2)
        accuracy = max(0, 1 - mse / np.var(y))

        return {"mean": mean_value, "std": std_value, "accuracy": accuracy, "mse": mse}

    def predict(
        self, model_name: str, features: Dict[str, float]
    ) -> Optional[PredictionResult]:
        """پیش‌بینی با مدل"""
        if model_name not in self.models:
            return None

        model = self.models[model_name]

        try:
            # آماده‌سازی ویژگی‌ها
            feature_values = [features.get(f, 0.0) for f in model.features]

            if model.model_type == "linear":
                prediction = self._predict_linear(model.predictions, feature_values)
            elif model.model_type == "polynomial":
                prediction = self._predict_polynomial(model.predictions, feature_values)
            else:
                prediction = self._predict_simple(model.predictions, feature_values)

            # محاسبه اعتماد
            confidence = min(1.0, model.accuracy)

            return PredictionResult(
                model_name=model_name,
                prediction=prediction,
                confidence=confidence,
                timestamp=time.time(),
                features_used=model.features,
            )

        except Exception as e:
            print(f"[{LogLevel.ERROR}] Prediction failed: {e}")
            return None

    def _predict_linear(
        self, model_data: Dict[str, Any], features: List[float]
    ) -> float:
        """پیش‌بینی خطی"""
        coefficients = model_data["coefficients"]
        X_with_bias = [1.0] + features
        return sum(c * x for c, x in zip(coefficients, X_with_bias))

    def _predict_polynomial(
        self, model_data: Dict[str, Any], features: List[float]
    ) -> float:
        """پیش‌بینی چندجمله‌ای"""
        coefficients = model_data["coefficients"]
        X_poly = features + [f**2 for f in features]
        X_with_bias = [1.0] + X_poly
        return sum(c * x for c, x in zip(coefficients, X_with_bias))

    def _predict_simple(
        self, model_data: Dict[str, Any], features: List[float]
    ) -> float:
        """پیش‌بینی ساده"""
        return model_data["mean"]


class TrafficAnalyzer:
    """تحلیلگر ترافیک ML"""

    def __init__(self):
        self.patterns = {}
        self.traffic_history = deque(maxlen=10000)
        self.is_analyzing = False

    def add_traffic_data(self, data: Dict[str, Any]):
        """اضافه کردن داده ترافیک"""
        self.traffic_history.append({"timestamp": time.time(), "data": data.copy()})

    def analyze_patterns(self) -> Dict[str, Any]:
        """تحلیل الگوهای ترافیک"""
        if len(self.traffic_history) < 100:
            return {}

        self.is_analyzing = True

        try:
            # استخراج ویژگی‌ها
            features = self._extract_features()

            # تحلیل الگوها
            patterns = {
                "peak_hours": self._find_peak_hours(),
                "bandwidth_trends": self._analyze_bandwidth_trends(),
                "connection_patterns": self._analyze_connection_patterns(),
                "anomaly_periods": self._find_anomaly_periods(),
                "predictions": self._generate_predictions(features),
            }

            self.patterns = patterns
            return patterns

        except Exception as e:
            print(f"[{LogLevel.ERROR}] Pattern analysis failed: {e}")
            return {}
        finally:
            self.is_analyzing = False

    def _extract_features(self) -> Dict[str, float]:
        """استخراج ویژگی‌ها"""
        if not self.traffic_history:
            return {}

        # ویژگی‌های زمانی
        timestamps = [point["timestamp"] for point in self.traffic_history]
        hours = [time.localtime(ts).tm_hour for ts in timestamps]

        # ویژگی‌های ترافیک
        bandwidth_values = [
            point["data"].get("bandwidth", 0) for point in self.traffic_history
        ]
        connection_counts = [
            point["data"].get("connections", 0) for point in self.traffic_history
        ]

        return {
            "avg_bandwidth": np.mean(bandwidth_values) if bandwidth_values else 0,
            "max_bandwidth": np.max(bandwidth_values) if bandwidth_values else 0,
            "bandwidth_variance": np.var(bandwidth_values) if bandwidth_values else 0,
            "avg_connections": np.mean(connection_counts) if connection_counts else 0,
            "max_connections": np.max(connection_counts) if connection_counts else 0,
            "peak_hour": max(set(hours), key=hours.count) if hours else 0,
            "data_points": len(self.traffic_history),
        }

    def _find_peak_hours(self) -> List[int]:
        """پیدا کردن ساعات پیک"""
        if not self.traffic_history:
            return []

        # گروه‌بندی بر اساس ساعت
        hourly_data = defaultdict(list)
        for point in self.traffic_history:
            hour = time.localtime(point["timestamp"]).tm_hour
            hourly_data[hour].append(point["data"].get("bandwidth", 0))

        # محاسبه میانگین برای هر ساعت
        hourly_avg = {}
        for hour, values in hourly_data.items():
            hourly_avg[hour] = np.mean(values) if values else 0

        # پیدا کردن ساعات پیک (بالاتر از 80% حداکثر)
        if not hourly_avg:
            return []

        max_avg = max(hourly_avg.values())
        threshold = max_avg * 0.8

        peak_hours = [hour for hour, avg in hourly_avg.items() if avg >= threshold]
        return sorted(peak_hours)

    def _analyze_bandwidth_trends(self) -> Dict[str, Any]:
        """تحلیل روند پهنای باند"""
        if len(self.traffic_history) < 10:
            return {}

        bandwidth_values = [
            point["data"].get("bandwidth", 0) for point in self.traffic_history
        ]

        # محاسبه روند
        x = np.arange(len(bandwidth_values))
        slope, intercept = np.polyfit(x, bandwidth_values, 1)

        return {
            "trend": (
                "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
            ),
            "slope": slope,
            "correlation": (
                np.corrcoef(x, bandwidth_values)[0, 1]
                if len(bandwidth_values) > 1
                else 0
            ),
        }

    def _analyze_connection_patterns(self) -> Dict[str, Any]:
        """تحلیل الگوهای اتصال"""
        if not self.traffic_history:
            return {}

        connection_counts = [
            point["data"].get("connections", 0) for point in self.traffic_history
        ]

        return {
            "avg_connections": np.mean(connection_counts),
            "max_connections": np.max(connection_counts),
            "connection_variance": np.var(connection_counts),
            "stability": 1
            - (np.std(connection_counts) / (np.mean(connection_counts) + 1e-8)),
        }

    def _find_anomaly_periods(self) -> List[Dict[str, Any]]:
        """پیدا کردن دوره‌های ناهنجاری"""
        if len(self.traffic_history) < 50:
            return []

        bandwidth_values = [
            point["data"].get("bandwidth", 0) for point in self.traffic_history
        ]
        mean_bandwidth = np.mean(bandwidth_values)
        std_bandwidth = np.std(bandwidth_values)

        anomalies = []
        for i, (point, bandwidth) in enumerate(
            zip(self.traffic_history, bandwidth_values)
        ):
            if abs(bandwidth - mean_bandwidth) > 2 * std_bandwidth:
                anomalies.append(
                    {
                        "timestamp": point["timestamp"],
                        "bandwidth": bandwidth,
                        "severity": abs(bandwidth - mean_bandwidth) / std_bandwidth,
                    }
                )

        return anomalies

    def _generate_predictions(self, features: Dict[str, float]) -> Dict[str, Any]:
        """تولید پیش‌بینی‌ها"""
        predictions = {}

        # پیش‌بینی پهنای باند آینده
        if "avg_bandwidth" in features:
            predictions["next_hour_bandwidth"] = features[
                "avg_bandwidth"
            ] * random.uniform(0.8, 1.2)

        # پیش‌بینی اتصالات آینده
        if "avg_connections" in features:
            predictions["next_hour_connections"] = int(
                features["avg_connections"] * random.uniform(0.9, 1.1)
            )

        return predictions


class MLOptimizationService:
    """سرویس بهینه‌سازی ML"""

    def __init__(self, log_callback: Callable = None):
        self.log = log_callback or print
        self.anomaly_detector = AnomalyDetector()
        self.performance_predictor = PerformancePredictor()
        self.traffic_analyzer = TrafficAnalyzer()

        self.is_running = False
        self._analysis_timer = None
        self._training_timer = None

    def start(self):
        """شروع سرویس"""
        if self.is_running:
            return

        self.is_running = True
        self._start_analysis_timer()
        self._start_training_timer()
        self.log(f"[{LogLevel.INFO}] ML optimization service started")

    def stop(self):
        """توقف سرویس"""
        if not self.is_running:
            return

        self.is_running = False
        self._stop_analysis_timer()
        self._stop_training_timer()
        self.log(f"[{LogLevel.INFO}] ML optimization service stopped")

    def _start_analysis_timer(self):
        """شروع تایمر تحلیل"""
        self._analysis_timer = threading.Timer(60, self._perform_analysis)  # هر دقیقه
        self._analysis_timer.daemon = True
        self._analysis_timer.start()

    def _stop_analysis_timer(self):
        """توقف تایمر تحلیل"""
        if self._analysis_timer:
            self._analysis_timer.cancel()
            self._analysis_timer = None

    def _start_training_timer(self):
        """شروع تایمر آموزش"""
        self._training_timer = threading.Timer(
            300, self._perform_training
        )  # هر 5 دقیقه
        self._training_timer.daemon = True
        self._training_timer.start()

    def _stop_training_timer(self):
        """توقف تایمر آموزش"""
        if self._training_timer:
            self._training_timer.cancel()
            self._training_timer = None

    def _perform_analysis(self):
        """انجام تحلیل"""
        try:
            # تحلیل الگوهای ترافیک
            patterns = self.traffic_analyzer.analyze_patterns()
            if patterns:
                self.log(
                    f"[{LogLevel.INFO}] Traffic patterns analyzed: {len(patterns)} patterns found"
                )

            # راه‌اندازی مجدد تایمر
            if self.is_running:
                self._start_analysis_timer()

        except Exception as e:
            self.log(f"[{LogLevel.ERROR}] Analysis error: {e}")

    def _perform_training(self):
        """انجام آموزش"""
        try:
            # آموزش مدل‌های جدید
            if len(self.performance_predictor.training_data) >= 50:
                model = self.performance_predictor.train_model(
                    "performance_model", "linear"
                )
                if model:
                    self.log(f"[{LogLevel.INFO}] Model retrained: {model.name}")

            # راه‌اندازی مجدد تایمر
            if self.is_running:
                self._start_training_timer()

        except Exception as e:
            self.log(f"[{LogLevel.ERROR}] Training error: {e}")

    def add_performance_data(
        self, features: Dict[str, float], target: float, metadata: Dict[str, Any] = None
    ):
        """اضافه کردن داده عملکرد"""
        self.performance_predictor.add_training_data(features, target, metadata)

        # بررسی ناهنجاری
        is_anomaly, confidence, anomalies = self.anomaly_detector.detect_anomaly(
            features
        )
        if is_anomaly:
            self.log(f"[{LogLevel.WARNING}] Performance anomaly detected: {anomalies}")

    def add_traffic_data(self, data: Dict[str, Any]):
        """اضافه کردن داده ترافیک"""
        self.traffic_analyzer.add_traffic_data(data)

        # استخراج ویژگی‌ها برای تشخیص ناهنجاری
        features = {
            "bandwidth": data.get("bandwidth", 0),
            "connections": data.get("connections", 0),
            "response_time": data.get("response_time", 0),
        }
        self.anomaly_detector.add_data_point(features)

    def predict_performance(
        self, features: Dict[str, float]
    ) -> Optional[PredictionResult]:
        """پیش‌بینی عملکرد"""
        return self.performance_predictor.predict("performance_model", features)

    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """دریافت توصیه‌های بهینه‌سازی"""
        recommendations = []

        try:
            # تحلیل الگوها
            patterns = self.traffic_analyzer.patterns

            # توصیه بر اساس ساعات پیک
            if "peak_hours" in patterns and patterns["peak_hours"]:
                recommendations.append(
                    {
                        "type": "scheduling",
                        "priority": "high",
                        "title": "Peak Hour Optimization",
                        "description": f"Consider load balancing during peak hours: {patterns['peak_hours']}",
                        "action": "adjust_load_balancing",
                    }
                )

            # توصیه بر اساس روند پهنای باند
            if "bandwidth_trends" in patterns:
                trend = patterns["bandwidth_trends"].get("trend", "stable")
                if trend == "increasing":
                    recommendations.append(
                        {
                            "type": "capacity",
                            "priority": "medium",
                            "title": "Bandwidth Scaling",
                            "description": "Bandwidth usage is increasing. Consider scaling up resources.",
                            "action": "scale_bandwidth",
                        }
                    )

            # توصیه بر اساس ناهنجاری‌ها
            if "anomaly_periods" in patterns and patterns["anomaly_periods"]:
                recommendations.append(
                    {
                        "type": "monitoring",
                        "priority": "high",
                        "title": "Anomaly Detection",
                        "description": f"Detected {len(patterns['anomaly_periods'])} anomaly periods. Review system health.",
                        "action": "investigate_anomalies",
                    }
                )

        except Exception as e:
            self.log(f"[{LogLevel.ERROR}] Recommendation generation failed: {e}")

        return recommendations

    def get_service_status(self) -> Dict[str, Any]:
        """دریافت وضعیت سرویس"""
        return {
            "is_running": self.is_running,
            "anomaly_detector_trained": self.anomaly_detector.is_trained,
            "models_count": len(self.performance_predictor.models),
            "training_data_count": len(self.performance_predictor.training_data),
            "traffic_data_count": len(self.traffic_analyzer.traffic_history),
            "patterns_analyzed": len(self.traffic_analyzer.patterns),
        }

    def cleanup(self):
        """پاکسازی منابع"""
        self.stop()
        self.performance_predictor.training_data.clear()
        self.traffic_analyzer.traffic_history.clear()
        self.log(f"[{LogLevel.INFO}] ML optimization service cleaned up")


# نمونه سراسری
_ml_service = None


def get_ml_service() -> MLOptimizationService:
    """دریافت نمونه سراسری سرویس ML"""
    global _ml_service
    if _ml_service is None:
        _ml_service = MLOptimizationService()
    return _ml_service
