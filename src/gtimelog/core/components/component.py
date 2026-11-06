from .environment import Environment
from .registry import component_registry


class _ComponentMeta(type):
    """Metaclass that auto-registers Component subclasses."""

    def __init__(cls, name, bases, namespace):
        super().__init__(name, bases, namespace)
        if name in ('Component', 'AbstractModel', 'Model', 'Service', 'Controller'):
            return
        _name = namespace.get('_name')
        _inherit = namespace.get('_inherit')
        if _name or _inherit:
            component_registry._do_register(cls)


class Component(metaclass=_ComponentMeta):
    """Base class for all auto-registered addon contributions."""

    _name = None
    _inherit = None
    registry = component_registry

    @property
    def env(self):
        """Odoo-style environment for accessing components."""
        if not hasattr(self, '_env'):
            self._env = Environment(component_registry)
        return self._env


class AbstractModel(Component):
    """Abstract model — shared interface and helpers, not directly usable."""


class Model(Component):
    """Data model — persistent or in-memory data structures."""


class Service(Component):
    """Service — groups related functions/constants under a name."""


class Controller(Component):
    """Controller — business logic orchestrator."""

    def __init__(self, window=None):
        self.window = window
