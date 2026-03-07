class ComponentRegistry:
    """Unified registry for Models, Services, and Controllers.

    Supports Odoo-style inheritance: a class with ``_inherit = 'x'``
    extends the class registered under name ``'x'``.
    """

    def __init__(self):
        self._bases = {}  # _name -> original class
        self._extensions = {}  # _name -> [extension classes]
        self._cache = {}  # _name -> final merged class

    def _do_register(self, cls):
        """Called by the metaclass when a concrete Component is defined."""
        name = getattr(cls, '_name', None)
        inherit = getattr(cls, '_inherit', None)

        if name and not inherit:
            self._bases[name] = cls
            self._extensions.setdefault(name, [])
            self._cache.pop(name, None)
        elif inherit:
            if inherit not in self._bases:
                raise ValueError(f"Cannot inherit '{inherit}': not registered yet. Check addon dependency order.")
            self._extensions[inherit].append(cls)
            self._cache.pop(inherit, None)
            if name and name != inherit:
                self._bases[name] = cls
                self._extensions.setdefault(name, [])
                self._cache.pop(name, None)
        else:
            raise ValueError(f"Class {cls.__qualname__} must define '_name' or '_inherit'")

    def register(self, cls):
        """Explicitly register a class. Can be used as a decorator."""
        self._do_register(cls)
        return cls

    def get(self, name):
        """Return the final class for *name*, with all extensions applied."""
        if name in self._cache:
            return self._cache[name]

        base = self._bases.get(name)
        if base is None:
            raise KeyError(f"Component '{name}' is not registered")

        extensions = self._extensions.get(name, [])
        if not extensions:
            self._cache[name] = base
            return base

        bases = (*tuple(reversed(extensions)), base)
        merged = type(base.__name__, bases, {'_name': name})
        self._cache[name] = merged
        return merged

    def list(self, kind=None):
        """Return registered names, optionally filtered by Component subtype."""
        if kind is None:
            return list(self._bases.keys())
        return [name for name, cls in self._bases.items() if isinstance(cls, type) and issubclass(cls, kind)]

    def is_registered(self, name):
        return name in self._bases

    def reset(self):
        self._bases.clear()
        self._extensions.clear()
        self._cache.clear()


# Singleton — created before Component so the metaclass can reference it
component_registry = ComponentRegistry()
