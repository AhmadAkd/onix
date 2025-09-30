"""
Utils package for Onix
Contains utility modules for error handling, performance monitoring, etc.
"""

from .error_handler import (
    ErrorHandler,
    NetworkErrorHandler,
    UIErrorHandler,
    get_global_error_handler,
    set_global_error_handler,
    safe_execute,
    error_handler_decorator
)

from .performance_monitor import (
    PerformanceMonitor,
    PerformanceOptimizer,
    get_global_performance_monitor,
    set_global_performance_monitor
)

__all__ = [
    # Error handling
    'ErrorHandler',
    'NetworkErrorHandler',
    'UIErrorHandler',
    'get_global_error_handler',
    'set_global_error_handler',
    'safe_execute',
    'error_handler_decorator',

    # Performance monitoring
    'PerformanceMonitor',
    'PerformanceOptimizer',
    'get_global_performance_monitor',
    'set_global_performance_monitor'
]
