from gtimelog.models import Model


class Settings(Model):
    """Office hours addon settings: target hours, office hours, week days display."""

    _inherit = 'settings'

    # Office hours-specific defaults
    hours = 8
    office_hours = 9
    week_days = '1,2,3,4,5'
    show_office_hours = True
    show_week_days = True

    def _config_office_hours(self, config):
        """Add office hours settings to config."""
        config.set('gtimelog', 'hours', str(self.hours))
        config.set('gtimelog', 'office-hours', str(self.office_hours))
        config.set('gtimelog', 'week-days', str(self.week_days))
        config.set('gtimelog', 'show_office_hours', str(self.show_office_hours))
        config.set('gtimelog', 'show_week_days', str(self.show_week_days))

    def _load_office_hours(self, config):
        """Load office hours settings from config."""
        self.hours = config.getfloat('gtimelog', 'hours')
        self.office_hours = config.getfloat('gtimelog', 'office-hours')
        # Note: week_days should be a string like '1,2,3,4,5', not a float
        # The original code had a bug using getfloat
        self.week_days = config.get('gtimelog', 'week-days')
        self.show_office_hours = config.getboolean('gtimelog', 'show_office_hours')
        self.show_week_days = config.getboolean('gtimelog', 'show_week_days')

    def _config(self):
        """Extend config with office hours-specific settings."""
        config = super()._config()
        self._config_office_hours(config)
        return config

    def load(self, filename=None):
        """Extend load with office hours-specific settings."""
        loaded_files = super().load(filename)
        if loaded_files:
            # Only load office hours-specific settings if the config file exists
            config = self._config()
            config.read(loaded_files)
            self._load_office_hours(config)
        return loaded_files
