import logging
from gettext import gettext as _

from gtimelog import require_version

require_version('Secret', '1')
from gi.repository import Secret  # noqa: E402

log = logging.getLogger('gtimelog.secrets.smtp')


def start_smtp_password_lookup(server, username, callback):
    schema = Secret.get_schema(Secret.SchemaType.COMPAT_NETWORK)
    attrs = {'user': username, 'server': server, 'protocol': 'smtp'}

    def password_callback(_source, result):
        password = Secret.password_lookup_finish(result)
        if password:
            log.debug('Found the SMTP password in the keyring.')
        else:
            log.debug('Did not find the SMTP password in the keyring.')
        callback(password or '')

    log.debug('Looking up the SMTP password for %s@%s in the keyring.', username, server)
    Secret.password_lookup(schema, attrs, cancellable=None, callback=password_callback)


def set_smtp_password(server, username, password):
    schema = Secret.get_schema(Secret.SchemaType.COMPAT_NETWORK)
    attrs = {'user': username, 'server': server, 'protocol': 'smtp'}
    label = '{user}@{server}'.format_map(attrs)

    def callback(_source, result):
        if not Secret.password_store_finish(result):
            log.error(_('Failed to store SMTP password in the keyring.'))
        else:
            log.debug('SMTP password stored in the keyring.')

    log.debug('Storing the SMTP password for %s in the keyring.', label)
    Secret.password_store(
        schema,
        attrs,
        collection=Secret.COLLECTION_DEFAULT,
        label=label,
        password=password,
        cancellable=None,
        callback=callback,
    )
