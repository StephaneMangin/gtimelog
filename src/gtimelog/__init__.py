import gettext
import locale
import logging
import signal
import sys

__version__ = '0.13.0.dev0'


# Re-export the core framework from models.py so that existing code like
# ``from gtimelog import Model, Hook, component_registry`` keeps working.
import gtimelog.core
import gtimelog.domain
import gtimelog.platform  # noqa: F401
from gtimelog.models import (  # noqa: F401
    Component,
    ComponentRegistry,
    Controller,
    Hook,
    Model,
    Service,
    component_registry,
)


def require_version(namespace, version):
    import gi

    try:
        gi.require_version(namespace, version)
    except ValueError:
        deb_package = f'gir1.2-{namespace.lower()}-{version}'
        sys.exit(
            f"""Typelib files for {namespace}-{version} are not available.

If you're on Ubuntu or another Debian-like distribution, please install
them with

    sudo apt install {deb_package}
"""
        )


def main():
    """Application entry-point (called by the ``gtimelog`` console script)."""
    from gtimelog.addons.base.helpers import DEBUG, mark_time
    from gtimelog.addons.base.views.application import Application
    from gtimelog.paths import LOCALE_DIR

    mark_time('in main()')

    root_logger = logging.getLogger()
    root_logger.addHandler(logging.StreamHandler())
    if DEBUG:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)

    log = logging.getLogger('gtimelog')

    gettext.bindtextdomain('gtimelog', LOCALE_DIR)
    gettext.textdomain('gtimelog')

    if hasattr(locale, 'bindtextdomain'):
        locale.bindtextdomain('gtimelog', LOCALE_DIR)
        locale.textdomain('gtimelog')
    else:  # pragma: nocover
        _ = gettext.gettext

        log.error(_('Unable to configure translations: no locale.bindtextdomain()'))

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = Application()
    mark_time('app created')
    try:
        sys.exit(app.run(sys.argv))
    finally:
        mark_time('exiting')


if __name__ == '__main__':
    main()
