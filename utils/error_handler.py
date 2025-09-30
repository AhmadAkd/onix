"""
Centralized Error Handling for Onix
Provides comprehensive error handling and logging
"""

import traceback
import functools
from typing import Callable, Any, Optional, Dict
from constants import LogLevel


class ErrorHandler:
    """Centralized error handling and logging system."""

    def __init__(self, log_callback: Optional[Callable[[str, LogLevel], None]] = None):
        self.log_callback = log_callback
        self._error_counts = {}
        self._max_errors_per_type = 10
        self._error_threshold = 5

    def log(self, message: str, level: LogLevel = LogLevel.INFO):
        """Log a message using the callback."""
        if self.log_callback:
            self.log_callback(message, level)

    def handle_error(self, error: Exception, context: str = "",
                     error_type: str = "general",
                     critical: bool = False) -> bool:
        """
        Handle an error with proper logging and counting.

        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
            error_type: Type of error for counting purposes
            critical: Whether this is a critical error

        Returns:
            bool: True if error was handled, False if too many errors
        """
        try:
            # Count errors by type
            if error_type not in self._error_counts:
                self._error_counts[error_type] = 0

            self._error_counts[error_type] += 1

            # Check if we've exceeded the error threshold
            if self._error_counts[error_type] > self._max_errors_per_type:
                if self._error_counts[error_type] == self._max_errors_per_type + 1:
                    self.log(
                        f"Too many {error_type} errors ({self._max_errors_per_type}), "
                        "suppressing further error messages",
                        LogLevel.WARNING
                    )
                return False

            # Prepare error message
            error_msg = f"{context}: {str(error)}" if context else str(error)

            # Add traceback for critical errors or debug mode
            if critical:
                error_msg += f"\nTraceback: {traceback.format_exc()}"

            # Log the error
            log_level = LogLevel.ERROR if critical else LogLevel.WARNING
            self.log(error_msg, log_level)

            return True

        except Exception as e:
            # Fallback logging if error handler itself fails
            print(f"Error in error handler: {e}")
            return False

    def get_error_count(self, error_type: str = None) -> Dict[str, int]:
        """Get error counts by type."""
        if error_type:
            return {error_type: self._error_counts.get(error_type, 0)}
        return self._error_counts.copy()

    def reset_error_count(self, error_type: str = None):
        """Reset error counts."""
        if error_type:
            self._error_counts.pop(error_type, None)
        else:
            self._error_counts.clear()

    def is_error_threshold_exceeded(self, error_type: str) -> bool:
        """Check if error threshold is exceeded for a type."""
        return self._error_counts.get(error_type, 0) > self._error_threshold


def safe_execute(func: Callable, *args, error_handler: ErrorHandler = None,
                 context: str = "", error_type: str = "function",
                 critical: bool = False, default_return: Any = None, **kwargs):
    """
    Safely execute a function with error handling.

    Args:
        func: Function to execute
        *args: Function arguments
        error_handler: Error handler instance
        context: Context for error logging
        error_type: Type of error for counting
        critical: Whether errors are critical
        default_return: Value to return on error
        **kwargs: Function keyword arguments

    Returns:
        Function result or default_return on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if error_handler:
            error_handler.handle_error(e, context, error_type, critical)
        return default_return


def error_handler_decorator(error_handler: ErrorHandler = None,
                            context: str = "", error_type: str = "decorated_function",
                            critical: bool = False, default_return: Any = None):
    """
    Decorator for automatic error handling.

    Args:
        error_handler: Error handler instance
        context: Context for error logging
        error_type: Type of error for counting
        critical: Whether errors are critical
        default_return: Value to return on error
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return safe_execute(
                func, *args,
                error_handler=error_handler,
                context=context or f"Function {func.__name__}",
                error_type=error_type,
                critical=critical,
                default_return=default_return,
                **kwargs
            )
        return wrapper
    return decorator


class NetworkErrorHandler(ErrorHandler):
    """Specialized error handler for network operations."""

    def __init__(self, log_callback: Optional[Callable[[str, LogLevel], None]] = None):
        super().__init__(log_callback)
        self._connection_errors = 0
        self._timeout_errors = 0
        self._dns_errors = 0

    def handle_network_error(self, error: Exception, operation: str = "") -> bool:
        """Handle network-specific errors."""
        error_type = "network"

        # Categorize network errors
        if "timeout" in str(error).lower():
            error_type = "timeout"
            self._timeout_errors += 1
        elif "dns" in str(error).lower() or "name resolution" in str(error).lower():
            error_type = "dns"
            self._dns_errors += 1
        elif "connection" in str(error).lower():
            error_type = "connection"
            self._connection_errors += 1

        context = f"Network operation: {operation}" if operation else "Network operation"
        return self.handle_error(error, context, error_type, critical=False)

    def get_network_error_stats(self) -> Dict[str, int]:
        """Get network error statistics."""
        return {
            "connection_errors": self._connection_errors,
            "timeout_errors": self._timeout_errors,
            "dns_errors": self._dns_errors,
            "total_errors": sum(self._error_counts.values())
        }


class UIErrorHandler(ErrorHandler):
    """Specialized error handler for UI operations."""

    def __init__(self, log_callback: Optional[Callable[[str, LogLevel], None]] = None):
        super().__init__(log_callback)
        self._ui_errors = 0
        self._rendering_errors = 0

    def handle_ui_error(self, error: Exception, widget_name: str = "",
                        operation: str = "") -> bool:
        """Handle UI-specific errors."""
        error_type = "ui"

        # Categorize UI errors
        if "rendering" in str(error).lower() or "paint" in str(error).lower():
            error_type = "rendering"
            self._rendering_errors += 1
        else:
            self._ui_errors += 1

        context = f"UI {widget_name}: {operation}" if widget_name and operation else f"UI: {operation}"
        return self.handle_error(error, context, error_type, critical=False)

    def get_ui_error_stats(self) -> Dict[str, int]:
        """Get UI error statistics."""
        return {
            "ui_errors": self._ui_errors,
            "rendering_errors": self._rendering_errors,
            "total_errors": sum(self._error_counts.values())
        }


# Global error handler instance
_global_error_handler = None


def get_global_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def set_global_error_handler(error_handler: ErrorHandler):
    """Set the global error handler instance."""
    global _global_error_handler
    _global_error_handler = error_handler
