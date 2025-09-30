"""
AI-Powered Optimization Service for Onix
Provides intelligent optimization, predictive failover, and traffic analysis
"""

import time
import threading
import json
import statistics
import math
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass
from collections import deque, defaultdict
from constants import LogLevel
import numpy as np


@dataclass
class PerformanceMetrics:
    """Performance metrics for AI analysis."""
    timestamp: float
    server_id: str
    ping: float
    download_speed: float
    upload_speed: float
    packet_loss: float
    jitter: float
    cpu_usage: float
    memory_usage: float
    network_usage: float
    connection_stability: float


@dataclass
class OptimizationRecommendation:
    """AI-generated optimization recommendation."""
    recommendation_type: str
    priority: int  # 1-5, 5 being highest
    description: str
    expected_improvement: float
    confidence: float
    parameters: Dict[str, Any]
    timestamp: float


@dataclass
class TrafficPattern:
    """Traffic pattern analysis result."""
    pattern_type: str
    confidence: float
    peak_hours: List[int]
    low_usage_hours: List[int]
    seasonal_trends: Dict[str, float]
    anomaly_score: float


class AIPerformanceAnalyzer:
    """AI-powered performance analyzer."""

    def __init__(self, log_callback: Optional[Callable[[str, LogLevel], None]] = None):
        self.log = log_callback or (
            lambda msg, level: print(f"[{level}] {msg}"))
        self.metrics_history: deque = deque(maxlen=1000)
        self.patterns: Dict[str, TrafficPattern] = {}
        self.recommendations: List[OptimizationRecommendation] = []
        self.anomaly_threshold = 2.0  # Standard deviations
        self.learning_rate = 0.1
        self.is_learning = True
        self._analysis_thread = None
        self._stop_analysis = threading.Event()

    def add_metrics(self, metrics: PerformanceMetrics) -> None:
        """Add new performance metrics for analysis."""
        try:
            self.metrics_history.append(metrics)

            # Trigger real-time analysis
            if len(self.metrics_history) >= 10:
                self._analyze_realtime()

        except Exception as e:
            self.log(f"Error adding metrics: {e}", LogLevel.ERROR)

    def _analyze_realtime(self) -> None:
        """Perform real-time analysis on recent metrics."""
        try:
            if len(self.metrics_history) < 5:
                return

            recent_metrics = list(
                self.metrics_history)[-20:]  # Last 20 metrics

            # Detect anomalies
            anomalies = self._detect_anomalies(recent_metrics)
            if anomalies:
                self._handle_anomalies(anomalies)

            # Update patterns
            self._update_traffic_patterns(recent_metrics)

            # Generate recommendations
            self._generate_recommendations(recent_metrics)

        except Exception as e:
            self.log(f"Error in real-time analysis: {e}", LogLevel.ERROR)

    def _detect_anomalies(self, metrics: List[PerformanceMetrics]) -> List[Dict[str, Any]]:
        """Detect performance anomalies using statistical analysis."""
        try:
            anomalies = []

            if len(metrics) < 5:
                return anomalies

            # Group metrics by server
            server_metrics = defaultdict(list)
            for metric in metrics:
                server_metrics[metric.server_id].append(metric)

            for server_id, server_data in server_metrics.items():
                if len(server_data) < 3:
                    continue

                # Calculate Z-scores for key metrics
                pings = [m.ping for m in server_data]
                speeds = [m.download_speed for m in server_data]
                packet_losses = [m.packet_loss for m in server_data]

                ping_mean = statistics.mean(pings)
                ping_std = statistics.stdev(pings) if len(pings) > 1 else 0

                speed_mean = statistics.mean(speeds)
                speed_std = statistics.stdev(speeds) if len(speeds) > 1 else 0

                # Check for anomalies
                latest = server_data[-1]

                if ping_std > 0:
                    ping_z_score = abs((latest.ping - ping_mean) / ping_std)
                    if ping_z_score > self.anomaly_threshold:
                        anomalies.append({
                            'server_id': server_id,
                            'metric': 'ping',
                            'value': latest.ping,
                            'z_score': ping_z_score,
                            'severity': 'high' if ping_z_score > 3 else 'medium'
                        })

                if speed_std > 0:
                    speed_z_score = abs(
                        (latest.download_speed - speed_mean) / speed_std)
                    if speed_z_score > self.anomaly_threshold:
                        anomalies.append({
                            'server_id': server_id,
                            'metric': 'download_speed',
                            'value': latest.download_speed,
                            'z_score': speed_z_score,
                            'severity': 'high' if speed_z_score > 3 else 'medium'
                        })

            return anomalies

        except Exception as e:
            self.log(f"Error detecting anomalies: {e}", LogLevel.ERROR)
            return []

    def _handle_anomalies(self, anomalies: List[Dict[str, Any]]) -> None:
        """Handle detected anomalies."""
        try:
            for anomaly in anomalies:
                if anomaly['severity'] == 'high':
                    self.log(
                        f"High severity anomaly detected: {anomaly}", LogLevel.WARNING)

                    # Generate immediate recommendation
                    recommendation = OptimizationRecommendation(
                        recommendation_type="immediate_action",
                        priority=5,
                        description=f"High {anomaly['metric']} anomaly detected on server {anomaly['server_id']}",
                        expected_improvement=0.2,
                        confidence=0.8,
                        parameters={
                            'server_id': anomaly['server_id'],
                            'metric': anomaly['metric'],
                            'z_score': anomaly['z_score']
                        },
                        timestamp=time.time()
                    )
                    self.recommendations.append(recommendation)

        except Exception as e:
            self.log(f"Error handling anomalies: {e}", LogLevel.ERROR)

    def _update_traffic_patterns(self, metrics: List[PerformanceMetrics]) -> None:
        """Update traffic patterns based on metrics."""
        try:
            if len(metrics) < 10:
                return

            # Analyze time-based patterns
            hours = [time.localtime(m.timestamp).tm_hour for m in metrics]
            hour_counts = defaultdict(int)
            for hour in hours:
                hour_counts[hour] += 1

            # Find peak and low usage hours
            sorted_hours = sorted(hour_counts.items(),
                                  key=lambda x: x[1], reverse=True)
            peak_hours = [h for h, c in sorted_hours[:3]]
            low_hours = [h for h, c in sorted_hours[-3:]]

            # Calculate anomaly score
            mean_usage = statistics.mean(hour_counts.values())
            std_usage = statistics.stdev(
                hour_counts.values()) if len(hour_counts) > 1 else 0
            anomaly_score = 0
            if std_usage > 0:
                anomaly_score = max(
                    0, (max(hour_counts.values()) - mean_usage) / std_usage)

            # Update pattern
            pattern = TrafficPattern(
                pattern_type="hourly_usage",
                confidence=0.7,
                peak_hours=peak_hours,
                low_usage_hours=low_hours,
                seasonal_trends={},
                anomaly_score=anomaly_score
            )

            self.patterns["hourly_usage"] = pattern

        except Exception as e:
            self.log(f"Error updating traffic patterns: {e}", LogLevel.ERROR)

    def _generate_recommendations(self, metrics: List[PerformanceMetrics]) -> None:
        """Generate optimization recommendations."""
        try:
            if len(metrics) < 5:
                return

            # Clear old recommendations
            current_time = time.time()
            self.recommendations = [
                r for r in self.recommendations if current_time - r.timestamp < 3600]  # Keep for 1 hour

            # Analyze performance trends
            recent_pings = [m.ping for m in metrics[-10:]]
            recent_speeds = [m.download_speed for m in metrics[-10:]]

            # Ping optimization recommendation
            if len(recent_pings) >= 3:
                ping_trend = self._calculate_trend(recent_pings)
                if ping_trend > 0.1:  # Increasing ping trend
                    recommendation = OptimizationRecommendation(
                        recommendation_type="ping_optimization",
                        priority=3,
                        description="Ping latency is increasing. Consider switching servers or optimizing connection.",
                        expected_improvement=0.15,
                        confidence=0.6,
                        parameters={'trend': ping_trend,
                                    'current_ping': recent_pings[-1]},
                        timestamp=current_time
                    )
                    self.recommendations.append(recommendation)

            # Speed optimization recommendation
            if len(recent_speeds) >= 3:
                speed_trend = self._calculate_trend(recent_speeds)
                if speed_trend < -0.1:  # Decreasing speed trend
                    recommendation = OptimizationRecommendation(
                        recommendation_type="speed_optimization",
                        priority=4,
                        description="Download speed is decreasing. Consider server load balancing or protocol optimization.",
                        expected_improvement=0.25,
                        confidence=0.7,
                        parameters={'trend': speed_trend,
                                    'current_speed': recent_speeds[-1]},
                        timestamp=current_time
                    )
                    self.recommendations.append(recommendation)

            # Server load balancing recommendation
            server_performance = self._analyze_server_performance(metrics)
            if server_performance:
                best_server = max(server_performance.items(),
                                  key=lambda x: x[1])
                worst_server = min(
                    server_performance.items(), key=lambda x: x[1])

                # Significant performance difference
                if best_server[1] - worst_server[1] > 0.3:
                    recommendation = OptimizationRecommendation(
                        recommendation_type="load_balancing",
                        priority=2,
                        description=f"Consider redistributing load from {worst_server[0]} to {best_server[0]}",
                        expected_improvement=0.2,
                        confidence=0.8,
                        parameters={
                            'best_server': best_server[0],
                            'worst_server': worst_server[0],
                            'performance_diff': best_server[1] - worst_server[1]
                        },
                        timestamp=current_time
                    )
                    self.recommendations.append(recommendation)

        except Exception as e:
            self.log(f"Error generating recommendations: {e}", LogLevel.ERROR)

    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend of a series of values."""
        try:
            if len(values) < 2:
                return 0.0

            n = len(values)
            x = list(range(n))
            y = values

            # Calculate slope using linear regression
            x_mean = sum(x) / n
            y_mean = sum(y) / n

            numerator = sum((x[i] - x_mean) * (y[i] - y_mean)
                            for i in range(n))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

            if denominator == 0:
                return 0.0

            slope = numerator / denominator
            return slope

        except Exception:
            return 0.0

    def _analyze_server_performance(self, metrics: List[PerformanceMetrics]) -> Dict[str, float]:
        """Analyze performance of different servers."""
        try:
            server_metrics = defaultdict(list)
            for metric in metrics:
                server_metrics[metric.server_id].append(metric)

            server_scores = {}
            for server_id, server_data in server_metrics.items():
                if len(server_data) < 2:
                    continue

                # Calculate composite performance score
                avg_ping = statistics.mean([m.ping for m in server_data])
                avg_speed = statistics.mean(
                    [m.download_speed for m in server_data])
                avg_packet_loss = statistics.mean(
                    [m.packet_loss for m in server_data])

                # Normalize scores (higher is better)
                ping_score = max(0, 1 - (avg_ping / 100))  # 100ms = 0 score
                speed_score = min(1, avg_speed / 100)  # 100 Mbps = 1 score
                packet_loss_score = max(
                    0, 1 - (avg_packet_loss / 10))  # 10% = 0 score

                composite_score = (ping_score * 0.4 +
                                   speed_score * 0.4 + packet_loss_score * 0.2)
                server_scores[server_id] = composite_score

            return server_scores

        except Exception as e:
            self.log(
                f"Error analyzing server performance: {e}", LogLevel.ERROR)
            return {}

    def get_recommendations(self, limit: int = 10) -> List[OptimizationRecommendation]:
        """Get current optimization recommendations."""
        try:
            # Sort by priority and timestamp
            sorted_recommendations = sorted(
                self.recommendations,
                key=lambda x: (x.priority, -x.timestamp),
                reverse=True
            )
            return sorted_recommendations[:limit]

        except Exception as e:
            self.log(f"Error getting recommendations: {e}", LogLevel.ERROR)
            return []

    def get_traffic_patterns(self) -> Dict[str, TrafficPattern]:
        """Get current traffic patterns."""
        return self.patterns.copy()

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for dashboard."""
        try:
            if not self.metrics_history:
                return {}

            recent_metrics = list(
                self.metrics_history)[-50:]  # Last 50 metrics

            summary = {
                'total_metrics': len(self.metrics_history),
                'recent_metrics': len(recent_metrics),
                'avg_ping': statistics.mean([m.ping for m in recent_metrics]),
                'avg_download_speed': statistics.mean([m.download_speed for m in recent_metrics]),
                'avg_upload_speed': statistics.mean([m.upload_speed for m in recent_metrics]),
                'avg_packet_loss': statistics.mean([m.packet_loss for m in recent_metrics]),
                'active_recommendations': len(self.recommendations),
                'traffic_patterns': len(self.patterns),
                'anomaly_count': len([m for m in recent_metrics if m.connection_stability < 0.5])
            }

            return summary

        except Exception as e:
            self.log(f"Error getting performance summary: {e}", LogLevel.ERROR)
            return {}

    def start_analysis(self) -> None:
        """Start background analysis."""
        if self._analysis_thread and self._analysis_thread.is_alive():
            return

        self._stop_analysis.clear()
        self._analysis_thread = threading.Thread(
            target=self._analysis_loop, daemon=True)
        self._analysis_thread.start()

        self.log("Started AI performance analysis", LogLevel.INFO)

    def stop_analysis(self) -> None:
        """Stop background analysis."""
        self._stop_analysis.set()
        if self._analysis_thread and self._analysis_thread.is_alive():
            self._analysis_thread.join(timeout=2)

        self.log("Stopped AI performance analysis", LogLevel.INFO)

    def _analysis_loop(self) -> None:
        """Main analysis loop."""
        while not self._stop_analysis.is_set():
            try:
                # Perform deep analysis every 5 minutes
                if len(self.metrics_history) >= 20:
                    self._deep_analysis()

                time.sleep(300)  # 5 minutes

            except Exception as e:
                self.log(f"Error in analysis loop: {e}", LogLevel.ERROR)
                time.sleep(60)

    def _deep_analysis(self) -> None:
        """Perform deep analysis on historical data."""
        try:
            # Analyze long-term trends
            all_metrics = list(self.metrics_history)
            if len(all_metrics) < 50:
                return

            # Group by time periods
            hourly_metrics = defaultdict(list)
            for metric in all_metrics:
                hour = time.localtime(metric.timestamp).tm_hour
                hourly_metrics[hour].append(metric)

            # Analyze hourly patterns
            for hour, metrics in hourly_metrics.items():
                if len(metrics) < 5:
                    continue

                avg_ping = statistics.mean([m.ping for m in metrics])
                avg_speed = statistics.mean(
                    [m.download_speed for m in metrics])

                # Update hourly pattern
                if f"hour_{hour}" not in self.patterns:
                    self.patterns[f"hour_{hour}"] = TrafficPattern(
                        pattern_type=f"hourly_pattern_{hour}",
                        confidence=0.5,
                        peak_hours=[hour],
                        low_usage_hours=[],
                        seasonal_trends={},
                        anomaly_score=0
                    )

        except Exception as e:
            self.log(f"Error in deep analysis: {e}", LogLevel.ERROR)


class PredictiveFailover:
    """AI-powered predictive failover system."""

    def __init__(self, log_callback: Optional[Callable[[str, LogLevel], None]] = None):
        self.log = log_callback or (
            lambda msg, level: print(f"[{level}] {msg}"))
        self.failure_predictions: Dict[str, float] = {}
        self.server_health_scores: Dict[str, float] = {}
        self.failover_threshold = 0.7
        self.prediction_window = 300  # 5 minutes

    def update_server_health(self, server_id: str, metrics: PerformanceMetrics) -> None:
        """Update server health score based on metrics."""
        try:
            # Calculate health score (0-1, higher is better)
            ping_score = max(0, 1 - (metrics.ping / 200))  # 200ms = 0 score
            speed_score = min(1, metrics.download_speed /
                              100)  # 100 Mbps = 1 score
            stability_score = metrics.connection_stability
            packet_loss_score = max(
                0, 1 - (metrics.packet_loss / 5))  # 5% = 0 score

            health_score = (ping_score * 0.3 + speed_score * 0.3 +
                            stability_score * 0.2 + packet_loss_score * 0.2)

            # Apply exponential moving average
            if server_id in self.server_health_scores:
                self.server_health_scores[server_id] = (
                    0.7 *
                    self.server_health_scores[server_id] + 0.3 * health_score
                )
            else:
                self.server_health_scores[server_id] = health_score

            # Predict failure probability
            self._predict_failure(server_id, health_score)

        except Exception as e:
            self.log(f"Error updating server health: {e}", LogLevel.ERROR)

    def _predict_failure(self, server_id: str, current_health: float) -> None:
        """Predict failure probability for a server."""
        try:
            # Simple prediction based on health trend
            if server_id in self.server_health_scores:
                health_trend = current_health - \
                    self.server_health_scores[server_id]

                # If health is declining rapidly, increase failure probability
                if health_trend < -0.1:
                    failure_prob = min(1.0, 0.5 + abs(health_trend) * 2)
                else:
                    failure_prob = max(0.0, 0.1 - current_health * 0.1)
            else:
                failure_prob = 0.1

            self.failure_predictions[server_id] = failure_prob

        except Exception as e:
            self.log(f"Error predicting failure: {e}", LogLevel.ERROR)

    def should_failover(self, server_id: str) -> bool:
        """Check if server should be failed over."""
        return self.failure_predictions.get(server_id, 0) > self.failover_threshold

    def get_best_alternative(self, current_server_id: str, available_servers: List[str]) -> Optional[str]:
        """Get the best alternative server for failover."""
        try:
            if not available_servers:
                return None

            # Filter out current server
            alternatives = [
                s for s in available_servers if s != current_server_id]
            if not alternatives:
                return None

            # Find server with highest health score
            best_server = max(
                alternatives, key=lambda s: self.server_health_scores.get(s, 0.5))

            return best_server

        except Exception as e:
            self.log(f"Error getting best alternative: {e}", LogLevel.ERROR)
            return None

    def get_failure_predictions(self) -> Dict[str, float]:
        """Get current failure predictions for all servers."""
        return self.failure_predictions.copy()

    def get_health_scores(self) -> Dict[str, float]:
        """Get current health scores for all servers."""
        return self.server_health_scores.copy()
