from . import services  # noqa: F401

try:
    from . import controllers  # noqa: F401
except ValueError as exc:
    if "Cannot inherit 'reports'" not in str(exc):
        raise
