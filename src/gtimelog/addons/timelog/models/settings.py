import datetime
import os

from gtimelog.addons.base.models.time_utils import parse_time
from gtimelog.models import Model


class Settings(Model):
    """Timelog addon settings: virtual midnight, rounding, log view options."""

    _inherit = 'settings'

    # Timelog-specific defaults
    chronological = True
    summary_view = False
    virtual_midnight = datetime.time(2, 0)
    rounding_time = 0
    rounding_time_force_above = False

    def get_timelog_file(self):
        """Return path to timelog.txt file."""
        return os.path.join(self.get_data_dir(), 'timelog.txt')

    def _config_timelog(self, config):
        """Add timelog settings to config."""
        config.set('gtimelog', 'chronological', str(self.chronological))
        config.set('gtimelog', 'summary_view', str(self.summary_view))
        config.set('gtimelog', 'virtual_midnight', self.virtual_midnight.strftime('%H:%M'))
        config.set('gtimelog', 'rounding_time', str(self.rounding_time))
        config.set('gtimelog', 'rounding_time_force_above', str(self.rounding_time_force_above))

    def _load_timelog(self, config):
        """Load timelog settings from config."""
        self.chronological = config.getboolean('gtimelog', 'chronological')
        self.summary_view = config.getboolean('gtimelog', 'summary_view')
        self.virtual_midnight = parse_time(config.get('gtimelog', 'virtual_midnight'))
        self.rounding_time = config.getint('gtimelog', 'rounding_time')
        self.rounding_time_force_above = config.getboolean('gtimelog', 'rounding_time_force_above')

    def _config(self):
        """Extend config with timelog-specific settings."""
        config = super()._config()
        self._config_timelog(config)
        return config

    def load(self, filename=None):
        """Extend load with timelog-specific settings."""
        loaded_files = super().load(filename)
        if loaded_files:
            # Only load timelog-specific settings if the config file exists
            config = self._config()
            config.read(loaded_files)
            self._load_timelog(config)
        return loaded_files
