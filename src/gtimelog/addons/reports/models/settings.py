import os

from gtimelog.models import Model


class Settings(Model):
    """Reports addon settings: report style, report log file path."""

    _inherit = 'settings'

    # Reports-specific defaults
    report_style = 'plain'

    def get_report_log_file(self):
        """Return path to sentreports.log file."""
        return os.path.join(self.get_data_dir(), 'sentreports.log')

    def _config_reports(self, config):
        """Add reports settings to config."""
        config.set('gtimelog', 'report_style', str(self.report_style))

    def _load_reports(self, config):
        """Load reports settings from config."""
        self.report_style = config.get('gtimelog', 'report_style')

    def _config(self):
        """Extend config with reports-specific settings."""
        config = super()._config()
        self._config_reports(config)
        return config

    def load(self, filename=None):
        """Extend load with reports-specific settings."""
        loaded_files = super().load(filename)
        if loaded_files:
            # Only load reports-specific settings if the config file exists
            config = self._config()
            config.read(loaded_files)
            self._load_reports(config)
        return loaded_files
