from gtimelog.models import Controller


class ApplicationController(Controller):
    """Application controller for reports addon."""

    _inherit = 'app.controller'

    def startup(self, app):
        """Setup report accelerators."""
        super().startup(app)
        app.set_accels_for_action('win.report', ['<Primary>D'])
        app.set_accels_for_action('win.cancel-report', ['Escape'])
        app.set_accels_for_action('win.send-report', ['<Primary>Return'])
