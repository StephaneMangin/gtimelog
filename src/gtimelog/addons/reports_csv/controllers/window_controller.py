from gtimelog.models import Controller


class WindowController(Controller):
    """Window controller for CSV export addon."""

    _inherit = 'window.controller'

    def initialize(self, window):
        """Setup CSV download action and dialog."""
        super().initialize(window)
        exports_cls = self.env['exports']
        exports_cls.setup_window_action(window)
