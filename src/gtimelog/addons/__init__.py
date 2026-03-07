_registry = None


def __getattr__(name):
    """Lazy initialization of addon registry on first access."""
    global _registry

    if name == 'registry':
        if _registry is None:
            from gtimelog.core.registry.addons import AddonRegistry

            _registry = AddonRegistry()
        return _registry

    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
