from gtimelog.models import Controller


class GSettingsMigrator(Controller):
    """Settings migrator for local task pane behavior."""

    _inherit = 'gsettings.migrator'

    def migrate(self, old_settings):
        """Migrate non-remote task-related settings."""
        super().migrate(old_settings)
        self.set_boolean('show-task-pane', old_settings.show_tasks)
        self.set_boolean('gtk-completion', bool(old_settings.enable_gtk_completion))
