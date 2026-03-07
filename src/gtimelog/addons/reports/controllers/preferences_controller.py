from gtimelog.models import Controller


class PreferencesController(Controller):
    """Preferences controller for reports addon."""

    _inherit = 'prefs.controller'

    def initialize(self, dialog):
        """Bind report preferences."""
        super().initialize(dialog)
        builder = dialog.builder
        gs = dialog.gsettings

        name_entry = builder.get_object('name_entry')
        sender_entry = builder.get_object('sender_entry')
        recipient_entry = builder.get_object('recipient_entry')
        attach_csv_checkbox = builder.get_object('attach_csv_checkbox')

        if name_entry:
            gs.bind('name', name_entry, 'text', self.gi().Gio.SettingsBindFlags.DEFAULT)
        if sender_entry:
            gs.bind('sender', sender_entry, 'text', self.gi().Gio.SettingsBindFlags.DEFAULT)
        if recipient_entry:
            gs.bind('list-email', recipient_entry, 'text', self.gi().Gio.SettingsBindFlags.DEFAULT)
        if attach_csv_checkbox:
            gs.bind('attach-csv-to-reports', attach_csv_checkbox, 'active', self.gi().Gio.SettingsBindFlags.DEFAULT)
