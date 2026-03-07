from gtimelog.models import Model


class Settings(Model):
    """Mail sender addon settings: email, name, mailer, editor, spreadsheet."""

    _inherit = 'settings'

    # Mail sender-specific defaults
    email = 'activity-list@example.com'
    name = 'Anonymous'
    sender = ''
    editor = 'xdg-open'
    mailer = 'x-terminal-emulator -e "mutt -H %s"'
    spreadsheet = 'xdg-open %s'
    show_tray_icon = False
    prefer_app_indicator = True
    start_in_tray = False

    def _config_mail_sender(self, config):
        """Add mail sender settings to config."""
        config.set('gtimelog', 'list-email', self.email)
        config.set('gtimelog', 'name', self.name)
        config.set('gtimelog', 'sender', self.sender)
        config.set('gtimelog', 'editor', self.editor)
        config.set('gtimelog', 'mailer', self.mailer)
        config.set('gtimelog', 'spreadsheet', self.spreadsheet)
        config.set('gtimelog', 'show_tray_icon', str(self.show_tray_icon))
        config.set('gtimelog', 'prefer_app_indicator', str(self.prefer_app_indicator))
        config.set('gtimelog', 'start_in_tray', str(self.start_in_tray))

    def _load_mail_sender(self, config):
        """Load mail sender settings from config."""
        self.email = config.get('gtimelog', 'list-email')
        self.name = config.get('gtimelog', 'name')
        self.sender = config.get('gtimelog', 'sender')
        self.editor = config.get('gtimelog', 'editor')
        self.mailer = config.get('gtimelog', 'mailer')
        self.spreadsheet = config.get('gtimelog', 'spreadsheet')
        self.show_tray_icon = config.getboolean('gtimelog', 'show_tray_icon')
        self.prefer_app_indicator = config.getboolean('gtimelog', 'prefer_app_indicator')
        self.start_in_tray = config.getboolean('gtimelog', 'start_in_tray')

    def _config(self):
        """Extend config with mail sender-specific settings."""
        config = super()._config()
        self._config_mail_sender(config)
        return config

    def load(self, filename=None):
        """Extend load with mail sender-specific settings."""
        loaded_files = super().load(filename)
        if loaded_files:
            # Only load mail sender-specific settings if the config file exists
            config = self._config()
            config.read(loaded_files)
            self._load_mail_sender(config)
        return loaded_files
