from abc import ABC, abstractmethod


class SettingsPort(ABC):
    """Contract for reading and writing application settings."""

    @abstractmethod
    def get_boolean(self, key):
        """Return a boolean setting value."""

    @abstractmethod
    def get_int(self, key):
        """Return an integer setting value."""

    @abstractmethod
    def get_string(self, key):
        """Return a string setting value."""


class StoragePort(ABC):
    """Contract for persistent file storage paths and writes."""

    @abstractmethod
    def get_timelog_file(self):
        """Return timelog file path."""

    @abstractmethod
    def get_task_list_file(self):
        """Return local task list file path."""

    @abstractmethod
    def get_task_list_cache_file(self):
        """Return remote task list cache file path."""


class TaskProviderPort(ABC):
    """Contract for retrieving task list content from remote sources."""

    @abstractmethod
    def fetch_tasks(self, url):
        """Return task list content from URL."""


class ReportingPort(ABC):
    """Contract for report delivery/export integrations."""

    @abstractmethod
    def send_report(self, sender, recipient, subject, body, _attachment=None):
        """Send one report payload through the integration backend."""
