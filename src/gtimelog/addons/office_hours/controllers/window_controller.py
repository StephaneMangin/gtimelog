from gtimelog.core.services.gtk import ApplicationService
from gtimelog.models import Controller


class WindowController(Controller):
    """Window controller for office hours addon."""

    _inherit = 'window.controller'

    def bind_settings(self, window):
        """Bind office hours settings to window."""
        super().bind_settings(window)
        gs = window.gsettings
        lv = window.log_view
        app_service = ApplicationService()

        # Bind office-hours domain settings to generic timelog extension fields.
        app_service.bind_settings(gs, 'hours', lv, 'expected-work-hours')
        app_service.bind_settings(gs, 'office-hours', lv, 'expected-presence-hours')
        app_service.bind_settings(gs, 'week-days', lv, 'expected-workdays')
