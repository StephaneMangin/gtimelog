from gtimelog.models import Controller


class GSettingsMigrator(Controller):
    """Settings migrator for remote-task-list ownership in tasks_sync."""

    _inherit = 'gsettings.migrator'

    def migrate(self, old_settings):
        """Migrate remote task settings from legacy config to GSettings."""
        super().migrate(old_settings)
        self.set_string('task-list-url', old_settings.task_list_url)
        self.set_boolean('remote-task-list', bool(old_settings.task_list_url))
        for arg in old_settings.edit_task_list_cmd.split():
            if arg.startswith(('http://', 'https://')):
                self.set_string('task-list-edit-url', arg)
