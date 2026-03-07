from gtimelog.models import Controller


class GSettingsMigrator(Controller):
    """Timelog settings migration controller."""

    _inherit = 'gsettings.migrator'

    def migrate(self, old_settings):
        """Migrate timelog settings from old config."""
        super().migrate(old_settings)
        vm = old_settings.virtual_midnight
        self.gsettings.set_value('virtual-midnight', self.gi().GLib.Variant('(ii)', (vm.hour, vm.minute)))
        self.gsettings.set_int('rounding-time', old_settings.rounding_time)
        self.gsettings.set_boolean('rounding-time-force-above', old_settings.rounding_time_force_above)
        if old_settings.summary_view:
            self.gsettings.set_string('detail-level', 'summary')
        elif old_settings.chronological:
            self.gsettings.set_string('detail-level', 'chronological')
        else:
            self.gsettings.set_string('detail-level', 'grouped')
