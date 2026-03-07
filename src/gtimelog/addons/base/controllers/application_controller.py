from gtimelog.models import Controller


class ApplicationController(Controller):
    """Base application setup coordinator.

    Addons extend this to contribute to application startup
    (keyboard shortcuts, actions, etc.).
    """

    _name = 'app.controller'

    def __init__(self, app):
        self.app = app

    def startup(self, app):
        """Execute startup tasks (shortcuts, actions, etc.).

        Called during app startup. Override in addons to register
        domain-specific keyboard shortcuts and actions.
        """
