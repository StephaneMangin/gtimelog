class Environment:
    """Odoo-style environment for accessing registered components.

    Usage:
        self.env['model.name']  # returns component class
        self.env.get('service.name')  # returns instantiated component
    """

    def __init__(self, registry, context=None):
        self._registry = registry
        self._context = context or {}
        self._instances = {}  # cache for singleton-like behavior

    def __getitem__(self, name):
        """Get component class by name."""
        return self._registry.get(name)

    def get(self, name, *args, **kwargs):
        """Get component and instantiate it with given arguments."""
        cls = self._registry.get(name)
        return cls(*args, **kwargs)
