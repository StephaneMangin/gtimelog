class _HookMeta(type):
    """Metaclass that auto-registers public methods as addon hook callbacks."""

    def __init__(cls, name, bases, namespace):
        super().__init__(name, bases, namespace)
        if name == 'Hook':
            return

        from gtimelog.addons import registry  # Lazy import to defer registry creation

        for attr_name, value in namespace.items():
            if attr_name.startswith('_') or not callable(value):
                continue
            hook_name = attr_name.split('__', 1)[0]
            registry.register_hook(hook_name, value)


class Hook(metaclass=_HookMeta):
    """Declarative hook registration."""
