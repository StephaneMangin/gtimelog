from gtimelog.core.services.gtk import ApplicationService
from gtimelog.models import Controller


class PreferencesController(Controller):
    """Preferences controller for office hours addon."""

    _inherit = 'prefs.controller'

    def initialize(self, dialog):
        """Bind office hours preferences."""
        super().initialize(dialog)
        builder = dialog.builder
        gs = dialog.gsettings
        app_service = ApplicationService()

        hours_entry = builder.get_object('hours_entry')
        office_hours_entry = builder.get_object('office_hours_entry')

        if hours_entry is None:
            return

        # Use ApplicationService to centralize Gio.SettingsBindFlags access
        app_service.bind_settings(gs, 'hours', hours_entry, 'value')
        app_service.bind_settings(gs, 'office-hours', office_hours_entry, 'value')

        day_checkboxes = {
            'Monday': builder.get_object('monday_check'),
            'Tuesday': builder.get_object('tuesday_check'),
            'Wednesday': builder.get_object('wednesday_check'),
            'Thursday': builder.get_object('thursday_check'),
            'Friday': builder.get_object('friday_check'),
            'Saturday': builder.get_object('saturday_check'),
            'Sunday': builder.get_object('sunday_check'),
        }
        dialog.day_checkboxes = day_checkboxes

        def on_day_toggled(_checkbox):
            selected = [
                d
                for d in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                if day_checkboxes[d].get_active()
            ]
            gs.set_string('week-days', ','.join(selected))

        def week_days_changed(*args):
            selected = {d.strip() for d in gs.get_string('week-days').split(',') if d.strip()}
            for name, cb in day_checkboxes.items():
                cb.handler_block_by_func(on_day_toggled)
                cb.set_active(name in selected)
                cb.handler_unblock_by_func(on_day_toggled)

        for cb in day_checkboxes.values():
            cb.connect('toggled', on_day_toggled)

        gs.connect('changed::week-days', week_days_changed)
        week_days_changed()
