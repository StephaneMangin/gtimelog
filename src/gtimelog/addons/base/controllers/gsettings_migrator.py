from gtimelog.models import Controller


class GSettingsMigrator(Controller):
    """Base GSettings migration coordinator.

    Addons extend this to migrate settings from old gtimelogrc
    format to GSettings schema.
    """

    _name = 'gsettings.migrator'

    def __init__(self, gsettings, old_settings):
        self.gsettings = gsettings
        self.old_settings = old_settings

    def migrate(self, old_settings):
        """Migrate settings from old_settings to gsettings.

        Called once when settings-migrated flag is False.
        Override in addons to migrate domain-specific settings.
        """

    def set_string(self, name, value):
        """Set a string key while tolerating missing legacy values."""
        self.gsettings.set_string(name, '' if value is None else str(value))

    def set_boolean(self, name, value):
        """Set a boolean key from legacy truthy/falsy values."""
        self.gsettings.set_boolean(name, bool(value))

    def set_int(self, name, value):
        """Set an integer key from legacy numeric values."""
        self.gsettings.set_int(name, int(value))

    def set_double(self, name, value):
        """Set a floating-point key from legacy numeric values."""
        self.gsettings.set_double(name, float(value))
