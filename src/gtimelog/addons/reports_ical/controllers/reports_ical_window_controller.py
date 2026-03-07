from gtimelog.models import Controller


class ReportsIcalWindowController(Controller):
    """Window controller for iCalendar export addon."""

    _inherit = 'reports.window.controller'

    def __init__(self, window):
        super().__init__(window)
        self.download_ical_button = None

    def initialize(self, window):
        """Setup iCalendar download action and button visibility."""
        super().initialize(window)
        exports_cls = self.env['exports']
        exports_cls.setup_window_action(window)

        self.download_ical_button = self.builder.get_object('download_ical_button') if self.builder else None
        if self.download_ical_button:
            self.download_ical_button.hide()

        window.gsettings.connect('changed::show-ical-export-button', self._on_toggle_changed)
        self._sync_ical_button_visibility()

    def _on_toggle_changed(self, *_args):
        self._sync_ical_button_visibility()

    def _sync_ical_button_visibility(self):
        if self.download_ical_button is None:
            return
        show_button = self.window.gsettings.get_boolean('show-ical-export-button')
        in_report_mode = self.window.main_stack.get_visible_child_name() == 'report'
        if show_button and in_report_mode:
            self.download_ical_button.show()
        else:
            self.download_ical_button.hide()

    def on_report(self, action, parameter):
        super().on_report(action, parameter)
        self._sync_ical_button_visibility()

    def on_cancel_report(self, action=None, parameter=None):
        super().on_cancel_report(action, parameter)
        self._sync_ical_button_visibility()
