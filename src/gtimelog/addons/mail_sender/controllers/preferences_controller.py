from gtimelog.models import Controller


class PreferencesController(Controller):
    """Preferences controller for mail sender addon."""

    _inherit = 'prefs.controller'

    def initialize(self, dialog):
        """Bind mail sender preferences."""
        from gtimelog.addons.mail_sender.models.secrets import set_smtp_password, start_smtp_password_lookup

        super().initialize(dialog)
        builder = dialog.builder
        gs = dialog.gsettings

        protocol_combo = builder.get_object('protocol_combo')
        if protocol_combo is None:
            return

        server_entry = builder.get_object('server_entry')
        port_entry = builder.get_object('port_entry')
        username_entry = builder.get_object('username_entry')
        password_entry = builder.get_object('password_entry')

        dialog.port_entry = port_entry
        dialog.username_entry = username_entry
        dialog.password_entry = password_entry

        gs.bind('mail-protocol', protocol_combo, 'active-id', self.gi().Gio.SettingsBindFlags.DEFAULT)
        gs.bind('smtp-server', server_entry, 'text', self.gi().Gio.SettingsBindFlags.DEFAULT)
        gs.bind('smtp-username', username_entry, 'text', self.gi().Gio.SettingsBindFlags.DEFAULT)

        def smtp_port_changed(*args):
            port = gs.get_int('smtp-port')
            if port == 0:
                mail_protocol = gs.get_string('mail-protocol')
                mail_protocols = self.env['mail_sender'].MAIL_PROTOCOLS
                default_port = mail_protocols[mail_protocol].factory.default_port
                port_entry.set_text(f'auto ({default_port})')
            else:
                port_entry.set_text(str(port))

        def smtp_port_set(*args):
            text = port_entry.get_text()
            if not text or text.lower().startswith('auto'):
                text = '0'
            try:
                port = int(text)
                if not 0 <= port <= 65535:
                    raise ValueError('value out of range')
            except ValueError:
                smtp_port_changed()
            else:
                gs.set_int('smtp-port', port)

        def refresh_password_field(*args):
            server = gs.get_string('smtp-server')
            username = gs.get_string('smtp-username')
            if username:
                start_smtp_password_lookup(server, username, lambda pw: password_entry.set_text(pw))
            else:
                password_entry.set_text('')

        def update_password(*args):
            server = gs.get_string('smtp-server')
            username = gs.get_string('smtp-username')
            password = password_entry.get_text()
            if username:
                set_smtp_password(server, username, password)

        gs.connect('changed::smtp-port', smtp_port_changed)
        gs.connect('changed::mail-protocol', smtp_port_changed)
        smtp_port_changed()
        port_entry.connect('focus-out-event', smtp_port_set)

        refresh_password_field()
        server_entry.connect('focus-out-event', refresh_password_field)
        username_entry.connect('focus-out-event', refresh_password_field)
        password_entry.connect('focus-out-event', update_password)
