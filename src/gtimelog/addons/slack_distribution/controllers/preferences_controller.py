from gtimelog.models import Controller


class PreferencesController(Controller):
    """Preferences controller for slack distribution addon."""

    _inherit = 'prefs.controller'

    def initialize(self, dialog):
        """Bind slack distribution preferences."""
        super().initialize(dialog)
        builder = dialog.builder
        gs = dialog.gsettings

        slack_entry = builder.get_object('slack_time_repartition_entry')
        if slack_entry is None:
            return

        proportional_entry = builder.get_object('proportional_repartition_entry')

        gs.bind('slack-time-repartition', slack_entry, 'active', self.gi().Gio.SettingsBindFlags.DEFAULT)
        if proportional_entry:
            gs.bind('proportional-repartition', proportional_entry, 'active', self.gi().Gio.SettingsBindFlags.DEFAULT)
