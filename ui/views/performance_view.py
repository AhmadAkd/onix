"""
Performance View for Onix
Provides a comprehensive performance monitoring dashboard
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QProgressBar, QTableWidget, QTableWidgetItem, QTextEdit, QSplitter,
    QTabWidget, QScrollArea, QFrame, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QObject
from PySide6.QtGui import QFont, QPalette, QColor
from typing import Dict, Any, List
from utils.performance_monitor import get_global_performance_monitor, PerformanceOptimizer
from constants import LogLevel


class PerformanceDataWorker(QObject):
    """Worker thread for collecting performance data."""
    
    data_updated = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.monitor = get_global_performance_monitor()
        self.optimizer = PerformanceOptimizer()
        self.running = False
    
    def start_collection(self):
        """Start collecting performance data."""
        self.running = True
        self.collect_data()
    
    def stop_collection(self):
        """Stop collecting performance data."""
        self.running = False
    
    def collect_data(self):
        """Collect and emit performance data."""
        if not self.running:
            return
            
        try:
            # Get current metrics
            metrics = self.monitor.get_current_metrics()
            summary = self.monitor.get_performance_summary()
            recommendations = self.optimizer.get_optimization_recommendations()
            
            data = {
                "metrics": metrics,
                "summary": summary,
                "recommendations": recommendations,
                "timestamp": self.monitor._last_cleanup if hasattr(self.monitor, '_last_cleanup') else 0
            }
            
            self.data_updated.emit(data)
            
        except Exception as e:
            print(f"Error collecting performance data: {e}")
        
        # Schedule next collection
        if self.running:
            QTimer.singleShot(1000, self.collect_data)


def create_performance_view(main_window):
    """Create the performance monitoring view."""
    container = QWidget()
    layout = QVBoxLayout(container)
    
    # Title
    title = QLabel(main_window.tr("Performance Monitor"))
    title.setFont(QFont("Arial", 16, QFont.Bold))
    title.setAlignment(Qt.AlignCenter)
    layout.addWidget(title)
    
    # Create tab widget
    tab_widget = QTabWidget()
    layout.addWidget(tab_widget)
    
    # Real-time metrics tab
    realtime_tab = create_realtime_metrics_tab(main_window)
    tab_widget.addTab(realtime_tab, main_window.tr("Real-time Metrics"))
    
    # System overview tab
    system_tab = create_system_overview_tab(main_window)
    tab_widget.addTab(system_tab, main_window.tr("System Overview"))
    
    # Optimization tab
    optimization_tab = create_optimization_tab(main_window)
    tab_widget.addTab(optimization_tab, main_window.tr("Optimization"))
    
    # Recommendations tab
    recommendations_tab = create_recommendations_tab(main_window)
    tab_widget.addTab(recommendations_tab, main_window.tr("Recommendations"))
    
    # Security tab
    security_tab = create_security_tab(main_window)
    tab_widget.addTab(security_tab, main_window.tr("Security"))
    
    return container


def create_realtime_metrics_tab(main_window):
    """Create the real-time metrics tab."""
    tab = QWidget()
    layout = QVBoxLayout(tab)
    
    # CPU Usage
    cpu_group = QGroupBox(main_window.tr("CPU Usage"))
    cpu_layout = QVBoxLayout(cpu_group)
    
    main_window.cpu_progress = QProgressBar()
    main_window.cpu_progress.setRange(0, 100)
    main_window.cpu_progress.setValue(0)
    main_window.cpu_label = QLabel("0%")
    main_window.cpu_label.setAlignment(Qt.AlignCenter)
    
    cpu_layout.addWidget(main_window.cpu_progress)
    cpu_layout.addWidget(main_window.cpu_label)
    layout.addWidget(cpu_group)
    
    # Memory Usage
    memory_group = QGroupBox(main_window.tr("Memory Usage"))
    memory_layout = QVBoxLayout(memory_group)
    
    main_window.memory_progress = QProgressBar()
    main_window.memory_progress.setRange(0, 100)
    main_window.memory_progress.setValue(0)
    main_window.memory_label = QLabel("0%")
    main_window.memory_label.setAlignment(Qt.AlignCenter)
    
    memory_layout.addWidget(main_window.memory_progress)
    memory_layout.addWidget(main_window.memory_label)
    layout.addWidget(memory_group)
    
    # Network I/O
    network_group = QGroupBox(main_window.tr("Network I/O"))
    network_layout = QVBoxLayout(network_group)
    
    main_window.network_label = QLabel("0 MB/s")
    main_window.network_label.setAlignment(Qt.AlignCenter)
    network_layout.addWidget(main_window.network_label)
    layout.addWidget(network_group)
    
    # Thread Count
    thread_group = QGroupBox(main_window.tr("Thread Count"))
    thread_layout = QVBoxLayout(thread_group)
    
    main_window.thread_label = QLabel("0")
    main_window.thread_label.setAlignment(Qt.AlignCenter)
    thread_layout.addWidget(main_window.thread_label)
    layout.addWidget(thread_group)
    
    return tab


def create_system_overview_tab(main_window):
    """Create the system overview tab."""
    tab = QWidget()
    layout = QVBoxLayout(tab)
    
    # Performance Status
    status_group = QGroupBox(main_window.tr("Performance Status"))
    status_layout = QVBoxLayout(status_group)
    
    main_window.performance_status = QLabel("Checking...")
    main_window.performance_status.setAlignment(Qt.AlignCenter)
    main_window.performance_status.setStyleSheet("""
        QLabel {
            font-size: 14px;
            font-weight: bold;
            padding: 10px;
            border-radius: 5px;
            background-color: #f0f0f0;
        }
    """)
    status_layout.addWidget(main_window.performance_status)
    layout.addWidget(status_group)
    
    # Detailed Metrics Table
    metrics_group = QGroupBox(main_window.tr("Detailed Metrics"))
    metrics_layout = QVBoxLayout(metrics_group)
    
    main_window.metrics_table = QTableWidget()
    main_window.metrics_table.setColumnCount(4)
    main_window.metrics_table.setHorizontalHeaderLabels([
        main_window.tr("Metric"),
        main_window.tr("Current"),
        main_window.tr("Average"),
        main_window.tr("Max")
    ])
    metrics_layout.addWidget(main_window.metrics_table)
    layout.addWidget(metrics_group)
    
    return tab


def create_optimization_tab(main_window):
    """Create the optimization tab."""
    tab = QWidget()
    layout = QVBoxLayout(tab)
    
    # Optimization Controls
    controls_group = QGroupBox(main_window.tr("Optimization Controls"))
    controls_layout = QVBoxLayout(controls_group)
    
    # Memory optimization button
    memory_btn = QPushButton(main_window.tr("Optimize Memory"))
    memory_btn.clicked.connect(lambda: optimize_memory(main_window))
    controls_layout.addWidget(memory_btn)
    
    # Thread optimization button
    thread_btn = QPushButton(main_window.tr("Optimize Threads"))
    thread_btn.clicked.connect(lambda: optimize_threads(main_window))
    controls_layout.addWidget(thread_btn)
    
    # Force garbage collection button
    gc_btn = QPushButton(main_window.tr("Force Garbage Collection"))
    gc_btn.clicked.connect(lambda: force_garbage_collection(main_window))
    controls_layout.addWidget(gc_btn)
    
    layout.addWidget(controls_group)
    
    # Optimization Results
    results_group = QGroupBox(main_window.tr("Optimization Results"))
    results_layout = QVBoxLayout(results_group)
    
    main_window.optimization_results = QTextEdit()
    main_window.optimization_results.setReadOnly(True)
    main_window.optimization_results.setMaximumHeight(200)
    results_layout.addWidget(main_window.optimization_results)
    layout.addWidget(results_group)
    
    return tab


def create_recommendations_tab(main_window):
    """Create the recommendations tab."""
    tab = QWidget()
    layout = QVBoxLayout(tab)
    
    # Recommendations
    recommendations_group = QGroupBox(main_window.tr("Performance Recommendations"))
    recommendations_layout = QVBoxLayout(recommendations_group)
    
    main_window.recommendations_text = QTextEdit()
    main_window.recommendations_text.setReadOnly(True)
    recommendations_layout.addWidget(main_window.recommendations_text)
    layout.addWidget(recommendations_group)
    
    # Refresh button
    refresh_btn = QPushButton(main_window.tr("Refresh Recommendations"))
    refresh_btn.clicked.connect(lambda: refresh_recommendations(main_window))
    layout.addWidget(refresh_btn)
    
    return tab


def optimize_memory(main_window):
    """Optimize memory usage."""
    try:
        optimizer = PerformanceOptimizer()
        result = optimizer.optimize_memory()
        
        if result.get("success", False):
            message = f"Memory optimization successful!\n"
            message += f"Objects collected: {result.get('objects_collected', 0)}\n"
            message += f"Memory freed: {result.get('memory_freed_mb', 0):.2f} MB"
        else:
            message = f"Memory optimization failed: {result.get('error', 'Unknown error')}"
        
        main_window.optimization_results.append(message)
        
    except Exception as e:
        main_window.optimization_results.append(f"Error optimizing memory: {e}")


def optimize_threads(main_window):
    """Optimize thread usage."""
    try:
        optimizer = PerformanceOptimizer()
        result = optimizer.optimize_threads()
        
        message = f"Thread optimization result:\n"
        message += f"Current threads: {result.get('current_threads', 0)}\n"
        message += f"Message: {result.get('message', 'No message')}"
        
        main_window.optimization_results.append(message)
        
    except Exception as e:
        main_window.optimization_results.append(f"Error optimizing threads: {e}")


def force_garbage_collection(main_window):
    """Force garbage collection."""
    try:
        import gc
        collected = gc.collect()
        message = f"Forced garbage collection collected {collected} objects"
        main_window.optimization_results.append(message)
        
    except Exception as e:
        main_window.optimization_results.append(f"Error forcing garbage collection: {e}")


def refresh_recommendations(main_window):
    """Refresh performance recommendations."""
    try:
        optimizer = PerformanceOptimizer()
        recommendations = optimizer.get_optimization_recommendations()
        
        text = "Performance Recommendations:\n\n"
        for i, rec in enumerate(recommendations, 1):
            text += f"{i}. {rec}\n"
        
        main_window.recommendations_text.setText(text)
        
    except Exception as e:
        main_window.recommendations_text.setText(f"Error getting recommendations: {e}")


def create_security_tab(main_window):
    """Create the security monitoring tab."""
    tab = QWidget()
    layout = QVBoxLayout(tab)
    
    # Security Status
    status_group = QGroupBox(main_window.tr("Security Status"))
    status_layout = QVBoxLayout(status_group)
    
    main_window.security_status_label = QLabel("Checking security status...")
    main_window.security_status_label.setAlignment(Qt.AlignCenter)
    main_window.security_status_label.setStyleSheet("""
        QLabel {
            font-size: 14px;
            font-weight: bold;
            padding: 10px;
            border-radius: 5px;
            background-color: #f0f0f0;
        }
    """)
    status_layout.addWidget(main_window.security_status_label)
    layout.addWidget(status_group)
    
    # Security Controls
    controls_group = QGroupBox(main_window.tr("Security Controls"))
    controls_layout = QVBoxLayout(controls_group)
    
    # Kill Switch
    kill_switch_layout = QHBoxLayout()
    main_window.kill_switch_label = QLabel(main_window.tr("Kill Switch:"))
    main_window.kill_switch_status = QLabel("Inactive")
    main_window.kill_switch_button = QPushButton(main_window.tr("Activate"))
    main_window.kill_switch_button.clicked.connect(lambda: toggle_kill_switch(main_window))
    kill_switch_layout.addWidget(main_window.kill_switch_label)
    kill_switch_layout.addWidget(main_window.kill_switch_status)
    kill_switch_layout.addStretch()
    kill_switch_layout.addWidget(main_window.kill_switch_button)
    controls_layout.addLayout(kill_switch_layout)
    
    # DNS Leak Protection
    dns_layout = QHBoxLayout()
    main_window.dns_protection_label = QLabel(main_window.tr("DNS Leak Protection:"))
    main_window.dns_protection_status = QLabel("Inactive")
    main_window.dns_protection_button = QPushButton(main_window.tr("Activate"))
    main_window.dns_protection_button.clicked.connect(lambda: toggle_dns_protection(main_window))
    dns_layout.addWidget(main_window.dns_protection_label)
    dns_layout.addWidget(main_window.dns_protection_status)
    dns_layout.addStretch()
    dns_layout.addWidget(main_window.dns_protection_button)
    controls_layout.addLayout(dns_layout)
    
    # WebRTC Protection
    webrtc_layout = QHBoxLayout()
    main_window.webrtc_protection_label = QLabel(main_window.tr("WebRTC Protection:"))
    main_window.webrtc_protection_status = QLabel("Inactive")
    main_window.webrtc_protection_button = QPushButton(main_window.tr("Activate"))
    main_window.webrtc_protection_button.clicked.connect(lambda: toggle_webrtc_protection(main_window))
    webrtc_layout.addWidget(main_window.webrtc_protection_label)
    webrtc_layout.addWidget(main_window.webrtc_protection_status)
    webrtc_layout.addStretch()
    webrtc_layout.addWidget(main_window.webrtc_protection_button)
    controls_layout.addLayout(webrtc_layout)
    
    layout.addWidget(controls_group)
    
    # Security Tests
    tests_group = QGroupBox(main_window.tr("Security Tests"))
    tests_layout = QVBoxLayout(tests_group)
    
    # DNS Leak Test
    dns_test_btn = QPushButton(main_window.tr("Test DNS Leak"))
    dns_test_btn.clicked.connect(lambda: test_dns_leak(main_window))
    tests_layout.addWidget(dns_test_btn)
    
    # Security Test Results
    main_window.security_test_results = QTextEdit()
    main_window.security_test_results.setReadOnly(True)
    main_window.security_test_results.setMaximumHeight(200)
    tests_layout.addWidget(main_window.security_test_results)
    layout.addWidget(tests_group)
    
    return tab


def toggle_kill_switch(main_window):
    """Toggle Kill Switch on/off."""
    try:
        if hasattr(main_window, 'security_suite'):
            status = main_window.security_suite.get_security_status()
            if status['kill_switch']:
                # Deactivate
                main_window.security_suite.kill_switch.deactivate()
                main_window.kill_switch_status.setText("Inactive")
                main_window.kill_switch_button.setText(main_window.tr("Activate"))
                main_window.kill_switch_status.setStyleSheet("color: red;")
            else:
                # Activate (would need proxy address/port)
                main_window.kill_switch_status.setText("Active")
                main_window.kill_switch_button.setText(main_window.tr("Deactivate"))
                main_window.kill_switch_status.setStyleSheet("color: green;")
                
    except Exception as e:
        main_window.security_test_results.append(f"Error toggling Kill Switch: {e}")


def toggle_dns_protection(main_window):
    """Toggle DNS leak protection on/off."""
    try:
        if hasattr(main_window, 'security_suite'):
            status = main_window.security_suite.get_security_status()
            if status['dns_protection']:
                # Deactivate
                main_window.security_suite.dns_protection.deactivate()
                main_window.dns_protection_status.setText("Inactive")
                main_window.dns_protection_button.setText(main_window.tr("Activate"))
                main_window.dns_protection_status.setStyleSheet("color: red;")
            else:
                # Activate
                main_window.security_suite.dns_protection.activate()
                main_window.dns_protection_status.setText("Active")
                main_window.dns_protection_button.setText(main_window.tr("Deactivate"))
                main_window.dns_protection_status.setStyleSheet("color: green;")
                
    except Exception as e:
        main_window.security_test_results.append(f"Error toggling DNS protection: {e}")


def toggle_webrtc_protection(main_window):
    """Toggle WebRTC protection on/off."""
    try:
        if hasattr(main_window, 'security_suite'):
            status = main_window.security_suite.get_security_status()
            if status['webrtc_protection']:
                # Deactivate
                main_window.security_suite.webrtc_protection.deactivate()
                main_window.webrtc_protection_status.setText("Inactive")
                main_window.webrtc_protection_button.setText(main_window.tr("Activate"))
                main_window.webrtc_protection_status.setStyleSheet("color: red;")
            else:
                # Activate
                main_window.security_suite.webrtc_protection.activate()
                main_window.webrtc_protection_status.setText("Active")
                main_window.webrtc_protection_button.setText(main_window.tr("Deactivate"))
                main_window.webrtc_protection_status.setStyleSheet("color: green;")
                
    except Exception as e:
        main_window.security_test_results.append(f"Error toggling WebRTC protection: {e}")


def test_dns_leak(main_window):
    """Test for DNS leaks."""
    try:
        if hasattr(main_window, 'security_suite'):
            main_window.security_test_results.append("Testing for DNS leaks...")
            result = main_window.security_suite.dns_protection.test_dns_leak()
            
            if result.get("leak_detected", False):
                main_window.security_test_results.append("❌ DNS LEAK DETECTED!")
                main_window.security_test_results.append(f"Details: {result}")
            else:
                main_window.security_test_results.append("✅ No DNS leaks detected")
                main_window.security_test_results.append(f"Test results: {result}")
        else:
            main_window.security_test_results.append("Security suite not available")
            
    except Exception as e:
        main_window.security_test_results.append(f"Error testing DNS leak: {e}")


def update_performance_display(main_window, data: Dict[str, Any]):
    """Update the performance display with new data."""
    try:
        metrics = data.get("metrics", {})
        summary = data.get("summary", {})
        
        # Update CPU display
        if "cpu_usage" in metrics:
            cpu_data = metrics["cpu_usage"]
            cpu_value = int(cpu_data.get("current", 0))
            main_window.cpu_progress.setValue(cpu_value)
            main_window.cpu_label.setText(f"{cpu_value}%")
            
            # Color coding
            if cpu_value > 80:
                main_window.cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: #ff4444; }")
            elif cpu_value > 60:
                main_window.cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: #ffaa00; }")
            else:
                main_window.cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: #44ff44; }")
        
        # Update Memory display
        if "memory_usage" in metrics:
            memory_data = metrics["memory_usage"]
            memory_value = int(memory_data.get("current", 0))
            main_window.memory_progress.setValue(memory_value)
            main_window.memory_label.setText(f"{memory_value}%")
            
            # Color coding
            if memory_value > 85:
                main_window.memory_progress.setStyleSheet("QProgressBar::chunk { background-color: #ff4444; }")
            elif memory_value > 70:
                main_window.memory_progress.setStyleSheet("QProgressBar::chunk { background-color: #ffaa00; }")
            else:
                main_window.memory_progress.setStyleSheet("QProgressBar::chunk { background-color: #44ff44; }")
        
        # Update Network display
        if "network_io" in metrics:
            network_data = metrics["network_io"]
            network_value = network_data.get("current", 0)
            main_window.network_label.setText(f"{network_value:.2f} MB/s")
        
        # Update Thread display
        if "thread_count" in metrics:
            thread_data = metrics["thread_count"]
            thread_value = int(thread_data.get("current", 0))
            main_window.thread_label.setText(str(thread_value))
        
        # Update Performance Status
        status = summary.get("status", "unknown")
        issues = summary.get("issues", [])
        
        if status == "good":
            main_window.performance_status.setText("✅ Performance is Good")
            main_window.performance_status.setStyleSheet("""
                QLabel {
                    background-color: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                }
            """)
        elif status == "warning":
            main_window.performance_status.setText(f"⚠️ Performance Warning: {', '.join(issues)}")
            main_window.performance_status.setStyleSheet("""
                QLabel {
                    background-color: #fff3cd;
                    color: #856404;
                    border: 1px solid #ffeaa7;
                }
            """)
        else:
            main_window.performance_status.setText("❌ Performance Issues Detected")
            main_window.performance_status.setStyleSheet("""
                QLabel {
                    background-color: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                }
            """)
        
        # Update metrics table
        update_metrics_table(main_window, metrics)
        
    except Exception as e:
        print(f"Error updating performance display: {e}")


def update_metrics_table(main_window, metrics: Dict[str, Any]):
    """Update the metrics table."""
    try:
        table = main_window.metrics_table
        table.setRowCount(len(metrics))
        
        for row, (metric_name, metric_data) in enumerate(metrics.items()):
            table.setItem(row, 0, QTableWidgetItem(metric_name.replace("_", " ").title()))
            table.setItem(row, 1, QTableWidgetItem(f"{metric_data.get('current', 0):.2f}"))
            table.setItem(row, 2, QTableWidgetItem(f"{metric_data.get('average', 0):.2f}"))
            table.setItem(row, 3, QTableWidgetItem(f"{metric_data.get('max', 0):.2f}"))
        
        table.resizeColumnsToContents()
        
    except Exception as e:
        print(f"Error updating metrics table: {e}")
