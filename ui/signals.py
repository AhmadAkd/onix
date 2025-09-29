from PySide6.QtCore import QObject, Signal


class ManagerSignals(QObject):
    """
    A collection of signals to facilitate communication between manager classes (background threads)
    and the main UI thread (PySideUI). This ensures thread-safe UI updates.
    """
    # Server testing and updates
    ping_result = Signal(dict, int, str)  # config, ping, test_type
    ping_started = Signal(dict)  # config
    health_check_progress = Signal(int, int)  # current, total
    servers_updated = Signal()  # Signal that server list has changed

    # Subscription updates
    update_started = Signal()
    update_finished = Signal(object)  # error object or None
    save_requested = Signal()

    # Connection status
    status_changed = Signal(str, str)  # status_text, color
    connected = Signal(int)  # latency
    stopped = Signal()
    ip_updated = Signal(str)  # ip_address
    speed_updated = Signal(float, float)  # up_speed, down_speed

    # General UI communication
    log_message = Signal(str, object)  # message, level
    show_info_message = Signal(str, str)  # title, message
    show_warning_message = Signal(str, str)  # title, message
    show_error_message = Signal(str, str)  # title, message
    ask_yes_no_question = Signal(str, str)  # title, question
    schedule_task_signal = Signal(int, object, object)  # delay_ms, func, args
