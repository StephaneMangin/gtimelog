from gtimelog.models import Controller


class WindowController(Controller):
    """Base window setup coordinator.

    Addons extend this to contribute widgets, actions, and bindings
    to the Window during initialization.
    """

    _name = 'window.controller'

    def __init__(self, window):
        self.window = window

    def initialize(self, window):
        """Initialize window components (widgets, actions, etc.).

        Called during window creation. Override in addons to set up
        domain-specific UI elements.
        """

    def bind_settings(self, window):
        """Bind GSettings to window/widget properties.

        Called after initialize(). Override in addons to bind
        domain-specific settings.
        """
