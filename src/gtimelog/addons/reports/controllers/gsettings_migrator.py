from gtimelog.models import Controller


class GSettingsMigrator(Controller):
    """Settings migrator for reports addon."""

    _inherit = 'gsettings.migrator'
    _VALID_REPORT_STYLES = frozenset({'plain', 'categorized', 'performance'})

    def migrate(self, old_settings):
        """Migrate report-related settings."""
        super().migrate(old_settings)
        self.set_string('name', old_settings.name)
        self.set_string('sender', old_settings.sender)
        self.set_string('list-email', old_settings.email)
        report_style = old_settings.report_style
        if report_style not in self._VALID_REPORT_STYLES:
            report_style = 'plain'
        self.set_string('report-style', report_style)
