"""
Performance Monitor for Onix
Provides comprehensive performance monitoring and optimization
"""

import time
import psutil
import threading
import gc
from typing import Dict, Any, List, Optional, Callable
from collections import deque
from constants import LogLevel


class PerformanceMonitor:
    """Comprehensive performance monitoring system."""
    
    def __init__(self, log_callback: Optional[Callable[[str, LogLevel], None]] = None):
        self.log = log_callback or (lambda msg, level: print(f"[{level}] {msg}"))
        self._is_monitoring = False
        self._monitor_thread = None
        self._stop_event = threading.Event()
        
        # Performance metrics
        self._metrics = {
            "cpu_usage": deque(maxlen=60),  # Last 60 seconds
            "memory_usage": deque(maxlen=60),
            "memory_available": deque(maxlen=60),
            "disk_io": deque(maxlen=60),
            "network_io": deque(maxlen=60),
            "thread_count": deque(maxlen=60),
            "gc_count": deque(maxlen=60),
        }
        
        # Performance thresholds
        self._thresholds = {
            "cpu_high": 80.0,
            "memory_high": 85.0,
            "memory_low": 10.0,
            "disk_io_high": 1000000,  # 1MB/s
            "network_io_high": 10000000,  # 10MB/s
        }
        
        # Callbacks for performance events
        self._callbacks = {
            "cpu_high": [],
            "memory_high": [],
            "memory_low": [],
            "performance_degraded": [],
        }
        
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes
        
    def start_monitoring(self) -> bool:
        """Start performance monitoring."""
        if self._is_monitoring:
            self.log("Performance monitoring is already active", LogLevel.WARNING)
            return False
            
        try:
            self._is_monitoring = True
            self._stop_event.clear()
            
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop, daemon=True
            )
            self._monitor_thread.start()
            
            self.log("Performance monitoring started", LogLevel.INFO)
            return True
            
        except Exception as e:
            self.log(f"Failed to start performance monitoring: {e}", LogLevel.ERROR)
            return False
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        if not self._is_monitoring:
            return
            
        self._stop_event.set()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2)
            
        self._is_monitoring = False
        self.log("Performance monitoring stopped", LogLevel.INFO)
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while not self._stop_event.is_set():
            try:
                # Collect performance metrics
                self._collect_metrics()
                
                # Check thresholds
                self._check_thresholds()
                
                # Periodic cleanup
                if time.time() - self._last_cleanup > self._cleanup_interval:
                    self._perform_cleanup()
                    self._last_cleanup = time.time()
                
                time.sleep(1)  # Monitor every second
                
            except Exception as e:
                self.log(f"Performance monitoring error: {e}", LogLevel.ERROR)
                time.sleep(5)
    
    def _collect_metrics(self):
        """Collect current performance metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self._metrics["cpu_usage"].append(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self._metrics["memory_usage"].append(memory.percent)
            self._metrics["memory_available"].append(memory.available)
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                disk_io_rate = (disk_io.read_bytes + disk_io.write_bytes) / 1024 / 1024  # MB
                self._metrics["disk_io"].append(disk_io_rate)
            
            # Network I/O
            net_io = psutil.net_io_counters()
            if net_io:
                net_io_rate = (net_io.bytes_sent + net_io.bytes_recv) / 1024 / 1024  # MB
                self._metrics["network_io"].append(net_io_rate)
            
            # Thread count
            thread_count = threading.active_count()
            self._metrics["thread_count"].append(thread_count)
            
            # Garbage collection count
            gc_count = sum(gc.get_count())
            self._metrics["gc_count"].append(gc_count)
            
        except Exception as e:
            self.log(f"Error collecting metrics: {e}", LogLevel.WARNING)
    
    def _check_thresholds(self):
        """Check performance thresholds and trigger callbacks."""
        try:
            # CPU threshold
            if self._metrics["cpu_usage"]:
                avg_cpu = sum(self._metrics["cpu_usage"]) / len(self._metrics["cpu_usage"])
                if avg_cpu > self._thresholds["cpu_high"]:
                    self._trigger_callbacks("cpu_high", {"cpu_usage": avg_cpu})
            
            # Memory threshold
            if self._metrics["memory_usage"]:
                avg_memory = sum(self._metrics["memory_usage"]) / len(self._metrics["memory_usage"])
                if avg_memory > self._thresholds["memory_high"]:
                    self._trigger_callbacks("memory_high", {"memory_usage": avg_memory})
                elif avg_memory < self._thresholds["memory_low"]:
                    self._trigger_callbacks("memory_low", {"memory_usage": avg_memory})
            
            # Performance degradation detection
            if self._detect_performance_degradation():
                self._trigger_callbacks("performance_degraded", self._get_current_metrics())
                
        except Exception as e:
            self.log(f"Error checking thresholds: {e}", LogLevel.WARNING)
    
    def _detect_performance_degradation(self) -> bool:
        """Detect if performance is degrading."""
        try:
            # Check if multiple metrics are high
            high_metrics = 0
            
            if self._metrics["cpu_usage"]:
                avg_cpu = sum(self._metrics["cpu_usage"]) / len(self._metrics["cpu_usage"])
                if avg_cpu > 70:  # Lower threshold for degradation detection
                    high_metrics += 1
            
            if self._metrics["memory_usage"]:
                avg_memory = sum(self._metrics["memory_usage"]) / len(self._metrics["memory_usage"])
                if avg_memory > 75:  # Lower threshold for degradation detection
                    high_metrics += 1
            
            # Check thread count (too many threads can indicate issues)
            if self._metrics["thread_count"]:
                current_threads = self._metrics["thread_count"][-1]
                if current_threads > 50:  # Arbitrary threshold
                    high_metrics += 1
            
            return high_metrics >= 2
            
        except Exception:
            return False
    
    def _trigger_callbacks(self, event_type: str, data: Dict[str, Any]):
        """Trigger callbacks for performance events."""
        try:
            for callback in self._callbacks.get(event_type, []):
                try:
                    callback(data)
                except Exception as e:
                    self.log(f"Error in performance callback: {e}", LogLevel.WARNING)
        except Exception as e:
            self.log(f"Error triggering callbacks: {e}", LogLevel.WARNING)
    
    def _perform_cleanup(self):
        """Perform periodic cleanup to maintain performance."""
        try:
            # Force garbage collection
            collected = gc.collect()
            if collected > 0:
                self.log(f"Garbage collection freed {collected} objects", LogLevel.DEBUG)
            
            # Clear old metrics to prevent memory buildup
            for metric_name, metric_deque in self._metrics.items():
                if len(metric_deque) > 30:  # Keep only last 30 entries
                    # Keep only the most recent entries
                    recent_entries = list(metric_deque)[-30:]
                    metric_deque.clear()
                    metric_deque.extend(recent_entries)
            
        except Exception as e:
            self.log(f"Error during cleanup: {e}", LogLevel.WARNING)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        try:
            metrics = {}
            
            for metric_name, metric_deque in self._metrics.items():
                if metric_deque:
                    metrics[metric_name] = {
                        "current": metric_deque[-1],
                        "average": sum(metric_deque) / len(metric_deque),
                        "min": min(metric_deque),
                        "max": max(metric_deque),
                        "count": len(metric_deque)
                    }
                else:
                    metrics[metric_name] = {
                        "current": 0,
                        "average": 0,
                        "min": 0,
                        "max": 0,
                        "count": 0
                    }
            
            return metrics
            
        except Exception as e:
            self.log(f"Error getting metrics: {e}", LogLevel.WARNING)
            return {}
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of current performance."""
        try:
            metrics = self.get_current_metrics()
            
            summary = {
                "status": "good",
                "issues": [],
                "recommendations": []
            }
            
            # Check CPU
            if metrics.get("cpu_usage", {}).get("average", 0) > self._thresholds["cpu_high"]:
                summary["status"] = "warning"
                summary["issues"].append("High CPU usage")
                summary["recommendations"].append("Close unnecessary applications")
            
            # Check Memory
            if metrics.get("memory_usage", {}).get("average", 0) > self._thresholds["memory_high"]:
                summary["status"] = "warning"
                summary["issues"].append("High memory usage")
                summary["recommendations"].append("Restart application or close other programs")
            
            # Check Thread Count
            if metrics.get("thread_count", {}).get("current", 0) > 50:
                summary["status"] = "warning"
                summary["issues"].append("High thread count")
                summary["recommendations"].append("Check for thread leaks")
            
            return summary
            
        except Exception as e:
            self.log(f"Error getting performance summary: {e}", LogLevel.WARNING)
            return {"status": "error", "issues": ["Unable to get performance data"], "recommendations": []}
    
    def register_callback(self, event_type: str, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback for performance events."""
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)
    
    def unregister_callback(self, event_type: str, callback: Callable[[Dict[str, Any]], None]):
        """Unregister a callback."""
        if event_type in self._callbacks and callback in self._callbacks[event_type]:
            self._callbacks[event_type].remove(callback)
    
    def set_threshold(self, threshold_name: str, value: float):
        """Set a performance threshold."""
        if threshold_name in self._thresholds:
            self._thresholds[threshold_name] = value
            self.log(f"Threshold {threshold_name} set to {value}", LogLevel.INFO)
        else:
            self.log(f"Unknown threshold: {threshold_name}", LogLevel.WARNING)
    
    def get_thresholds(self) -> Dict[str, float]:
        """Get current thresholds."""
        return self._thresholds.copy()
    
    def is_monitoring(self) -> bool:
        """Check if monitoring is active."""
        return self._is_monitoring


class PerformanceOptimizer:
    """Performance optimization utilities."""
    
    def __init__(self, log_callback: Optional[Callable[[str, LogLevel], None]] = None):
        self.log = log_callback or (lambda msg, level: print(f"[{level}] {msg}"))
    
    def optimize_memory(self) -> Dict[str, Any]:
        """Optimize memory usage."""
        try:
            # Force garbage collection
            before_gc = psutil.virtual_memory().used
            collected = gc.collect()
            after_gc = psutil.virtual_memory().used
            
            freed_memory = before_gc - after_gc
            
            result = {
                "objects_collected": collected,
                "memory_freed_bytes": freed_memory,
                "memory_freed_mb": freed_memory / 1024 / 1024,
                "success": True
            }
            
            self.log(f"Memory optimization freed {result['memory_freed_mb']:.2f} MB", LogLevel.INFO)
            return result
            
        except Exception as e:
            self.log(f"Memory optimization failed: {e}", LogLevel.ERROR)
            return {"success": False, "error": str(e)}
    
    def optimize_threads(self) -> Dict[str, Any]:
        """Optimize thread usage."""
        try:
            # Get current thread count
            current_threads = threading.active_count()
            
            # This is a placeholder - actual thread optimization would depend on the application
            result = {
                "current_threads": current_threads,
                "optimized": False,
                "message": "Thread optimization not implemented"
            }
            
            return result
            
        except Exception as e:
            self.log(f"Thread optimization failed: {e}", LogLevel.ERROR)
            return {"success": False, "error": str(e)}
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get performance optimization recommendations."""
        recommendations = []
        
        try:
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 80:
                recommendations.append("High memory usage detected - consider closing other applications")
            
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 80:
                recommendations.append("High CPU usage detected - consider reducing application load")
            
            # Check disk space
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                recommendations.append("Low disk space detected - consider freeing up space")
            
            # Check thread count
            thread_count = threading.active_count()
            if thread_count > 50:
                recommendations.append("High thread count detected - check for thread leaks")
            
            if not recommendations:
                recommendations.append("Performance appears to be optimal")
            
        except Exception as e:
            self.log(f"Error getting recommendations: {e}", LogLevel.WARNING)
            recommendations.append("Unable to analyze performance")
        
        return recommendations


# Global performance monitor instance
_global_performance_monitor = None

def get_global_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _global_performance_monitor
    if _global_performance_monitor is None:
        _global_performance_monitor = PerformanceMonitor()
    return _global_performance_monitor

def set_global_performance_monitor(monitor: PerformanceMonitor):
    """Set the global performance monitor instance."""
    global _global_performance_monitor
    _global_performance_monitor = monitor
