from abc import ABC, abstractmethod


class CoreManager(ABC):
    """
    Abstract base class for managing different proxy cores (like sing-box, Xray, etc.).
    """

    def __init__(self, settings, callbacks):
        self.settings = settings
        self.callbacks = callbacks
        self.is_running = False
        self.process = None

    @abstractmethod
    def start(self, config):
        """Starts the core with the given server configuration."""
        pass

    @abstractmethod
    def stop(self):
        """Stops the core process."""
        pass

    @abstractmethod
    def check_connection(self):
        """Checks if the connection through the core is successful."""
        pass

    def log(self, message, level):
        self.callbacks.get("log", lambda msg, lvl: None)(message, level)
