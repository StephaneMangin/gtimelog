import os

from gtimelog.models import Model


class Settings(Model):
    """Settings helpers for Planio synchronization files."""

    _inherit = 'settings'

    def get_planio_sync_cache_file(self):
        """Return provider-specific cache file used by remote-task-list mode."""
        return os.path.join(self.get_data_dir(), 'planio-remote-tasks.txt')

    def get_planio_project_mapping_file(self):
        """Return provider-specific project mapping JSON file path."""
        return os.path.join(self.get_data_dir(), 'projects_mapping.json')

    def get_task_list_cache_file(self):
        """Route task cache path to Planio file when sync URL scheme is active."""
        from gi.repository import Gio

        gsettings = Gio.Settings.new('org.gtimelog')
        if gsettings.get_string('task-list-url') == 'sync://planio':
            return self.get_planio_sync_cache_file()
        return super().get_task_list_cache_file()
