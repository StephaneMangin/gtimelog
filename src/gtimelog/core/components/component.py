from .environment import Environment
from .registry import component_registry


class _ComponentMeta(type):
    """Metaclass that auto-registers Component subclasses."""

    def __init__(cls, name, bases, namespace):
        super().__init__(name, bases, namespace)
        if name in ('Component', 'Model', 'Service', 'Controller'):
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
    _gi_modules_cache = None  # Shared across all Component instances

    @property
    def env(self):
        """Odoo-style environment for accessing components."""
        if not hasattr(self, '_env'):
            self._env = Environment(component_registry)
        return self._env

    @classmethod
    def gi(cls):
        """Get lazy-loaded GTK/GObject introspection modules."""
        if cls._gi_modules_cache is None:
            from types import SimpleNamespace

            from gi.repository import Gdk, GdkPixbuf, Gio, GLib, GObject, Gtk

            try:
                from gtimelog import require_version

                require_version('Soup', '3.0')
                from gi.repository import Soup as soup_module  # noqa: N813
            except (ImportError, ValueError):
                soup_module = None

            cls._gi_modules_cache = SimpleNamespace(
                Gdk=Gdk,
                GdkPixbuf=GdkPixbuf,
                Gio=Gio,
                GLib=GLib,
                GObject=GObject,
                Gtk=Gtk,
                Soup=soup_module,
            )
        return cls._gi_modules_cache


class Model(Component):
    """Data model — persistent or in-memory data structures."""


class Service(Component):
    """Service — groups related functions/constants under a name."""


class Controller(Component):
    """Controller — business logic orchestrator."""

    def __init__(self, window=None):
        self.window = window
