from gtimelog.addons import registry
from gtimelog.addons.office_hours.views.footer import render_extended_footer, setup_footer_observers
from gtimelog.models import Controller


class ApplicationController(Controller):
    """Application controller for office hours reactive callbacks."""

    _inherit = 'app.controller'

    def startup(self, app):
        """Register office-hours reactive callbacks on startup."""
        super().startup(app)
        registry.register_hook('log_footer', render_extended_footer)
        registry.register_hook('log_view_init', setup_footer_observers)
