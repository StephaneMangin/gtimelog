import locale
import os
from configparser import RawConfigParser

from gtimelog.models import Model

legacy_default_home = os.path.normpath('~/.gtimelog')
default_config_home = os.path.normpath('~/.config')
default_data_home = os.path.normpath('~/.local/share')


class Settings(Model):
    """Core settings infrastructure: path management and config file handling.

    Domain-specific settings are provided by addon extensions via _inherit.
    """

    _name = 'settings'

    # Apparently locale.getpreferredencoding() might be blank on Mac OS X
    _encoding = locale.getpreferredencoding() or 'UTF-8'

    def check_legacy_config(self):
        """Check for legacy config location and return path if found."""
        envar_home = os.environ.get('GTIMELOG_HOME')
        if envar_home is not None:
            return os.path.expanduser(envar_home)
        if os.path.isdir(os.path.expanduser(legacy_default_home)):
            return os.path.expanduser(legacy_default_home)
        return None

    # https://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html

    def get_config_dir(self):
        """Get configuration directory path (XDG_CONFIG_HOME/gtimelog)."""
        legacy = self.check_legacy_config()
        if legacy:
            return legacy
        xdg = os.environ.get('XDG_CONFIG_HOME') or default_config_home
        return os.path.join(os.path.expanduser(xdg), 'gtimelog')

    def get_data_dir(self):
        """Get data directory path (XDG_DATA_HOME/gtimelog)."""
        legacy = self.check_legacy_config()
        if legacy:
            return legacy
        xdg = os.environ.get('XDG_DATA_HOME') or default_data_home
        return os.path.join(os.path.expanduser(xdg), 'gtimelog')

    def get_config_file(self):
        """Get config file path (gtimelogrc)."""
        return os.path.join(self.get_config_dir(), 'gtimelogrc')

    def _config(self):
        """Create base config parser. Addons extend this via super()._config()."""
        config = RawConfigParser()
        config.add_section('gtimelog')
        return config

    def load(self, filename=None):
        """Load configuration from file. Addons extend this via super().load()."""
        if filename is None:
            filename = self.get_config_file()
        config = self._config()
        return config.read([filename])

    def save(self, filename):
        """Save configuration to file."""
        config = self._config()
        with open(filename, 'w') as f:
            config.write(f)
