from gtimelog.addons import registry
from gtimelog.addons.timelog.controllers.window_controller import WindowController
from gtimelog.addons.timelog.views.timelog_application_orchestrator import TimelogApplicationOrchestrator
from gtimelog.models import Controller


class ApplicationController(Controller):
    """Timelog application initialization controller."""

    _inherit = 'app.controller'

    def startup(self, app):
        """Set up timelog keyboard shortcuts."""
        super().startup(app)
        TimelogApplicationOrchestrator(app).startup()
        registry.register_hook('window_focus', WindowController.window_focus_reload)
