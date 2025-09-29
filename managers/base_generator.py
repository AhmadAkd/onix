from abc import ABC, abstractmethod


class BaseConfigGenerator(ABC):
    """
    Abstract base class for generating configuration files for different cores.
    """

    @abstractmethod
    def generate_config_json(self, server_config, settings):
        pass

    @abstractmethod
    def generate_test_config(self, servers, settings):
        """Generates a configuration for testing multiple servers at once."""
        pass
