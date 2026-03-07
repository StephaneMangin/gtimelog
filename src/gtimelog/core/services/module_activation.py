from gtimelog.models import Service


class ModuleActivationApplicationService(Service):
    """Orchestrates addon toggle decisions and dependency constraints."""

    _name = 'application.module.activation.service'

    def __init__(self, addon_registry):
        self.addon_registry = addon_registry

    def list_toggleable_modules(self):
        """Return sorted addon names that can be toggled by users."""
        return self.addon_registry.list_toggleable_addons()

    def get_module_manifest(self, addon):
        """Return addon manifest for presentation metadata."""
        return self.addon_registry.get_manifest(addon)

    def compute_effective_disabled(self, disabled_addons):
        """Return dependency-consistent disabled addon set."""
        return self.addon_registry.compute_effective_disabled(disabled_addons)

    def apply_toggle(self, addon, active, current_disabled):
        """Apply one toggle decision and return (effective_disabled, required_by)."""
        disabled_addons = set(current_disabled)
        if active:
            disabled_addons.discard(addon)
        else:
            disabled_addons.add(addon)

        effective_disabled = self.compute_effective_disabled(disabled_addons)
        if addon not in effective_disabled and not active:
            required_by = self.addon_registry.get_required_by_enabled(addon, disabled_addons)
            return set(current_disabled), required_by
        return effective_disabled, []
