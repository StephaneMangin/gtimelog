from gtimelog.models import Controller


class GSettingsMigrator(Controller):
    """Settings migrator for office hours addon."""

    _inherit = 'gsettings.migrator'

    def migrate(self, old_settings):
        """Migrate office hours settings."""
        super().migrate(old_settings)
        self.set_double('hours', old_settings.hours)
        self.set_double('office-hours', old_settings.office_hours)
        self.set_string('week-days', old_settings.week_days)
