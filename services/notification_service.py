"""
Notification Service for Onix
Provides system notifications and alerts
"""

import time
from typing import Callable, Optional, Dict, Any, List
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QSystemTrayIcon
from constants import LogLevel


class NotificationService(QObject):
    """Service for managing notifications."""

    notification_sent = Signal(str, str)  # title, message

    def __init__(self, log_callback: Callable[[str, LogLevel], None],
                 tray_icon: Optional[QSystemTrayIcon] = None):
        super().__init__()
        self.log = log_callback
        self.tray_icon = tray_icon
        self._notifications_enabled = True
        self._notification_history = []
        self._max_history = 100

    def enable_notifications(self, enabled: bool = True):
        """Enable or disable notifications."""
        self._notifications_enabled = enabled
        self.log(
            f"Notifications {'enabled' if enabled else 'disabled'}", LogLevel.INFO)

    def is_notifications_enabled(self) -> bool:
        """Check if notifications are enabled."""
        return self._notifications_enabled

    def send_notification(self, title: str, message: str,
                          notification_type: str = "info",
                          duration: int = 5000) -> bool:
        """Send a notification."""
        if not self._notifications_enabled:
            return False

        try:
            # Add to history
            self._add_to_history(title, message, notification_type)

            # Send system notification
            if self.tray_icon and self.tray_icon.isVisible():
                icon_type = self._get_icon_type(notification_type)
                self.tray_icon.showMessage(title, message, icon_type, duration)

            # Emit signal
            self.notification_sent.emit(title, message)

            self.log(f"Notification sent: {title}", LogLevel.INFO)
            return True

        except Exception as e:
            self.log(f"Failed to send notification: {e}", LogLevel.ERROR)
            return False

    def send_connection_notification(self, server_name: str, connected: bool):
        """Send connection status notification."""
        if connected:
            self.send_notification(
                "Connected",
                f"Successfully connected to {server_name}",
                "success",
                3000
            )
        else:
            self.send_notification(
                "Disconnected",
                f"Disconnected from {server_name}",
                "warning",
                3000
            )

    def send_error_notification(self, error_message: str):
        """Send error notification."""
        self.send_notification(
            "Error",
            error_message,
            "error",
            5000
        )

    def send_speed_notification(self, download_speed: float, upload_speed: float):
        """Send speed test notification."""
        self.send_notification(
            "Speed Test Complete",
            f"Download: {download_speed/1024/1024:.2f} MB/s, Upload: {upload_speed/1024/1024:.2f} MB/s",
            "info",
            4000
        )

    def send_security_notification(self, message: str):
        """Send security-related notification."""
        self.send_notification(
            "Security Alert",
            message,
            "warning",
            6000
        )

    def send_update_notification(self, update_type: str, details: str = ""):
        """Send update notification."""
        self.send_notification(
            "Update Available",
            f"{update_type} update is available. {details}",
            "info",
            5000
        )

    def get_notification_history(self) -> List[Dict[str, Any]]:
        """Get notification history."""
        return self._notification_history.copy()

    def clear_notification_history(self):
        """Clear notification history."""
        self._notification_history.clear()
        self.log("Notification history cleared", LogLevel.INFO)

    def _add_to_history(self, title: str, message: str, notification_type: str):
        """Add notification to history."""
        notification = {
            "timestamp": time.time(),
            "title": title,
            "message": message,
            "type": notification_type
        }

        self._notification_history.append(notification)

        # Keep only recent notifications
        if len(self._notification_history) > self._max_history:
            self._notification_history = self._notification_history[-self._max_history:]

    def _get_icon_type(self, notification_type: str) -> QSystemTrayIcon.MessageIcon:
        """Get appropriate icon type for notification."""
        icon_map = {
            "info": QSystemTrayIcon.Information,
            "success": QSystemTrayIcon.Information,
            "warning": QSystemTrayIcon.Warning,
            "error": QSystemTrayIcon.Critical
        }
        return icon_map.get(notification_type, QSystemTrayIcon.Information)


class AlertManager:
    """Manager for various types of alerts."""

    def __init__(self, log_callback: Callable[[str, LogLevel], None]):
        self.log = log_callback
        self._alerts = {}
        self._alert_callbacks = {}

    def register_alert(self, alert_id: str, condition: Callable[[], bool],
                       message: str, alert_type: str = "warning",
                       callback: Optional[Callable[[], None]] = None):
        """Register an alert condition."""
        self._alerts[alert_id] = {
            "condition": condition,
            "message": message,
            "type": alert_type,
            "active": False
        }

        if callback:
            self._alert_callbacks[alert_id] = callback

        self.log(f"Registered alert: {alert_id}", LogLevel.INFO)

    def unregister_alert(self, alert_id: str):
        """Unregister an alert."""
        if alert_id in self._alerts:
            del self._alerts[alert_id]
            if alert_id in self._alert_callbacks:
                del self._alert_callbacks[alert_id]
            self.log(f"Unregistered alert: {alert_id}", LogLevel.INFO)

    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check all registered alerts."""
        triggered_alerts = []

        for alert_id, alert_data in self._alerts.items():
            try:
                if alert_data["condition"]():
                    if not alert_data["active"]:
                        alert_data["active"] = True
                        triggered_alerts.append({
                            "id": alert_id,
                            "message": alert_data["message"],
                            "type": alert_data["type"]
                        })

                        # Call callback if registered
                        if alert_id in self._alert_callbacks:
                            self._alert_callbacks[alert_id]()

                else:
                    alert_data["active"] = False

            except Exception as e:
                self.log(
                    f"Error checking alert {alert_id}: {e}", LogLevel.ERROR)

        return triggered_alerts

    def get_active_alerts(self) -> List[str]:
        """Get list of active alert IDs."""
        return [alert_id for alert_id, data in self._alerts.items() if data["active"]]


class PerformanceDashboard:
    """Dashboard for performance monitoring and alerts."""

    def __init__(self, log_callback: Callable[[str, LogLevel], None]):
        self.log = log_callback
        self._metrics = {}
        self._thresholds = {}
        self._alert_manager = AlertManager(log_callback)
        self._setup_default_alerts()

    def update_metric(self, metric_name: str, value: float):
        """Update a performance metric."""
        self._metrics[metric_name] = {
            "value": value,
            "timestamp": time.time()
        }

    def set_threshold(self, metric_name: str, threshold: float,
                      condition: str = "greater"):
        """Set threshold for a metric."""
        self._thresholds[metric_name] = {
            "threshold": threshold,
            "condition": condition
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return self._metrics.copy()

    def get_metric_history(self, metric_name: str, duration: int = 3600) -> List[Dict[str, Any]]:
        """Get metric history for specified duration in seconds."""
        current_time = time.time()
        cutoff_time = current_time - duration

        # This would typically come from a database or persistent storage
        # For now, return current metric if it exists
        if metric_name in self._metrics:
            metric = self._metrics[metric_name]
            if metric["timestamp"] >= cutoff_time:
                return [metric]
        return []

    def _setup_default_alerts(self):
        """Setup default performance alerts."""
        # High CPU usage alert
        self._alert_manager.register_alert(
            "high_cpu",
            lambda: self._metrics.get("cpu_usage", {}).get("value", 0) > 80,
            "High CPU usage detected",
            "warning"
        )

        # High memory usage alert
        self._alert_manager.register_alert(
            "high_memory",
            lambda: self._metrics.get("memory_usage", {}).get("value", 0) > 85,
            "High memory usage detected",
            "warning"
        )

        # Low connection speed alert
        self._alert_manager.register_alert(
            "low_speed",
            lambda: self._metrics.get("download_speed", {}).get(
                "value", 0) < 1000000,  # 1 MB/s
            "Low connection speed detected",
            "info"
        )

        # High ping alert
        self._alert_manager.register_alert(
            "high_ping",
            lambda: self._metrics.get("ping", {}).get("value", 0) > 500,
            "High ping detected",
            "warning"
        )

    def check_performance_alerts(self) -> List[Dict[str, Any]]:
        """Check performance-related alerts."""
        return self._alert_manager.check_alerts()
