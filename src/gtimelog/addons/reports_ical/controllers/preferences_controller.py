from gtimelog.models import Controller


class PreferencesController(Controller):
    """Preferences controller for reports_ical addon."""

    _inherit = 'prefs.controller'

    def initialize(self, dialog):
        """Bind iCalendar preferences."""
        super().initialize(dialog)

        show_button_checkbox = dialog.builder.get_object('show_ical_export_button_checkbox')
        attach_ical_checkbox = dialog.builder.get_object('attach_ical_checkbox')

        if show_button_checkbox is None and attach_ical_checkbox is None:
            return

        if show_button_checkbox is not None:
            dialog.gsettings.bind(
                'show-ical-export-button',
                show_button_checkbox,
                'active',
                self.gi().Gio.SettingsBindFlags.DEFAULT,
            )
        if attach_ical_checkbox is not None:
            dialog.gsettings.bind(
                'attach-ical-to-reports',
                attach_ical_checkbox,
                'active',
                self.gi().Gio.SettingsBindFlags.DEFAULT,
            )
