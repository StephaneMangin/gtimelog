import functools
import logging
from gettext import gettext as _

from gtimelog import require_version

require_version('Gtk', '3.0')
require_version('Secret', '1')
from gi.repository import Gio, GObject, Gtk, Secret  # noqa: E402

log = logging.getLogger('gtimelog.secrets.http')


class Authenticator:
    def __init__(self):
        self.pending = []
        self.lookup_in_progress = False
        self.username = None
        self.password = None

    def find_in_keyring(self, uri, callback):
        """
        Attempt to load a username and password from the keyring.
        If the keyring is not available, return the last username
        and password entered, if any.
        """
        Secret.Service.get(
            Secret.ServiceFlags.OPEN_SESSION | Secret.ServiceFlags.LOAD_COLLECTIONS,
            cancellable=None,
            callback=functools.partial(self._find_in_keyring, uri, callback),
        )

    def _find_in_keyring(self, uri, callback, _source, result):
        service = Secret.Service.get_finish(result)
        schema = Secret.get_schema(Secret.SchemaType.COMPAT_NETWORK)
        attrs = {'server': uri.get_host(), 'protocol': uri.get_scheme(), 'port': str(uri.get_port())}
        flags = Secret.SearchFlags.UNLOCK | Secret.SearchFlags.LOAD_SECRETS

        def search_callback(_source, result):
            items = service.search_finish(result)
            if items:
                log.debug('Found the HTTP password for %s in the keyring.', items[0].get_label())
                username = items[0].get_attributes()['user']
                password = items[0].get_secret().get_text()
                if len(items) > 1:
                    log.debug('Ignoring the other %d found passwords.', len(items) - 1)
            else:
                log.debug(
                    'Did not find any HTTP passwords for %s://%s:%s in the keyring.',
                    uri.get_scheme(),
                    uri.get_host(),
                    uri.get_port(),
                )
                username = self.username
                password = self.password
            callback(username, password)

        service.search(schema, attrs, flags, cancellable=None, callback=search_callback)

    def save_to_keyring(self, uri, username, password):
        schema = Secret.get_schema(Secret.SchemaType.COMPAT_NETWORK)
        attrs = {'server': uri.get_host(), 'protocol': uri.get_scheme(), 'port': str(uri.get_port()), 'user': username}
        label = '{user}@{server}:{port}'.format_map(attrs)

        def password_stored_callback(_source, result):
            if not Secret.password_store_finish(result):
                log.error(_('Failed to store HTTP password in the keyring.'))
            else:
                log.debug('HTTP password stored in the keyring.')

        log.debug('Storing the HTTP password for %s in the keyring.', label)
        Secret.password_store(
            schema,
            attrs,
            collection=Secret.COLLECTION_DEFAULT,
            label=label,
            password=password,
            cancellable=None,
            callback=password_stored_callback,
        )

    def ask_the_user(self, auth, uri, callback):
        """
        Pop up a username/password dialog for uri
        """
        mountoperation = Gtk.MountOperation.new()

        def on_reply(m, r):
            if r == Gio.MountOperationResult.HANDLED:
                username = m.get_username()
                password = m.get_password()

                if username and password:
                    if m.get_password_save() == Gio.PasswordSave.PERMANENTLY:
                        self.save_to_keyring(uri, username, password)
                    elif m.get_password_save() == Gio.PasswordSave.FOR_SESSION:
                        self.username = username
                        self.password = password

            else:
                username = None
                password = None

            callback(username, password)

        flags = (
            Gio.AskPasswordFlags.NEED_PASSWORD
            | Gio.AskPasswordFlags.NEED_USERNAME
            | Gio.AskPasswordFlags.SAVING_SUPPORTED
        )

        mountoperation.connect('reply', on_reply)
        mountoperation.set_password_save(Gio.PasswordSave.PERMANENTLY)
        mountoperation.do_ask_password(
            mountoperation,
            _('Authentication is required for "%s"\nYou need a username and a password to access %s')
            % (auth.get_realm(), uri.get_host()),
            '',
            auth.get_realm(),
            flags,
        )

    def find_password(self, auth, uri, retrying, callback):
        def keyring_callback(username, password):
            if username is None or retrying:
                GObject.idle_add(lambda: self.ask_the_user(auth, uri, callback))
            else:
                callback(username, password)

        self.find_in_keyring(uri, keyring_callback)

    def http_auth_cb(self, message, auth, retrying, *args):
        self.pending.insert(0, (message, auth, retrying))
        self.maybe_pop_queue()
        return True

    def maybe_pop_queue(self):
        if self.lookup_in_progress:
            return

        try:
            (message, auth, retrying) = self.pending.pop()
        except IndexError:
            pass
        else:
            self.lookup_in_progress = True
            uri = message.get_uri()
            self.find_password(auth, uri, retrying, callback=functools.partial(self.http_auth_finish, message, auth))

    def http_auth_finish(self, message, auth, username, password):
        if username and password:
            auth.authenticate(username, password)
        else:
            auth.cancel()

        self.lookup_in_progress = False
        self.maybe_pop_queue()
