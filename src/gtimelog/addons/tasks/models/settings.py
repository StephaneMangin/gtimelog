import os

from gtimelog.models import Model


class Settings(Model):
    """Task addon settings: task list URL, task pane visibility, completion mode."""

    _inherit = 'settings'

    # Task-specific defaults
    show_tasks = True
    task_list_url = ''
    edit_task_list_cmd = ''
    enable_gtk_completion = True  # False enables gvim-style completion

    def get_task_list_file(self):
        """Return path to tasks.txt file."""
        return os.path.join(self.get_data_dir(), 'tasks.txt')

    def get_task_list_cache_file(self):
        """Return path to remote-tasks.txt cache file."""
        return os.path.join(self.get_data_dir(), 'remote-tasks.txt')

    def _config_tasks(self, config):
        """Add task settings to config."""
        config.set('gtimelog', 'show_tasks', str(self.show_tasks))
        config.set('gtimelog', 'task_list_url', self.task_list_url)
        config.set('gtimelog', 'edit_task_list_cmd', self.edit_task_list_cmd)
        config.set('gtimelog', 'gtk-completion', str(self.enable_gtk_completion))

    def _load_tasks(self, config):
        """Load task settings from config."""
        self.show_tasks = config.getboolean('gtimelog', 'show_tasks')
        self.task_list_url = config.get('gtimelog', 'task_list_url')
        self.edit_task_list_cmd = config.get('gtimelog', 'edit_task_list_cmd')
        self.enable_gtk_completion = config.getboolean('gtimelog', 'gtk-completion')

    def _config(self):
        """Extend config with task-specific settings."""
        config = super()._config()
        self._config_tasks(config)
        return config

    def load(self, filename=None):
        """Extend load with task-specific settings."""
        loaded_files = super().load(filename)
        if loaded_files:
            # Only load task-specific settings if the config file exists
            config = self._config()
            config.read(loaded_files)
            self._load_tasks(config)
        return loaded_files
