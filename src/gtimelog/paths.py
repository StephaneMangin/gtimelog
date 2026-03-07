import contextlib
import os
import subprocess
import sys

here = os.path.dirname(__file__)

SCHEMA_DIR = os.path.join(here, 'data')
if SCHEMA_DIR:
    # Have to do this before importing 'gi'.
    # Note: it has been brought to my attention that I can do
    #   source = Gio.SettingsSchemaSource.new_from_directory(SCHEMA_DIR,
    #       Gio.SettingsSchemaSource.get_default(), False)
    #   schema = source.lookup('...', False)
    # to load schemas from any location
    os.environ['GSETTINGS_SCHEMA_DIR'] = SCHEMA_DIR
    if not os.path.exists(os.path.join(SCHEMA_DIR, 'gschemas.compiled')):
        # This, too, I have to do before importing 'gi'.
        glib_compile_schemas = os.path.join(sys.prefix, 'lib', 'site-packages', 'gnome', 'glib-compile-schemas.exe')
        if not os.path.exists(glib_compile_schemas):
            glib_compile_schemas = 'glib-compile-schemas'
        with contextlib.suppress(OSError):
            subprocess.call([glib_compile_schemas, SCHEMA_DIR])


_addons_dir = os.path.join(here, 'addons')
_base_views = os.path.join(_addons_dir, 'base', 'views')
_base_data = os.path.join(_addons_dir, 'base', 'data')
_core_data = os.path.join(here, 'data')

UI_FILE = os.path.join(_base_views, 'gtimelog.ui')
MENUS_UI_FILE = os.path.join(_base_views, 'menus.ui')
ABOUT_DIALOG_UI_FILE = os.path.join(_core_data, 'about.ui')
SHORTCUTS_UI_FILE = os.path.join(_base_views, 'shortcuts.ui')
CSS_FILE = os.path.join(_base_views, 'gtimelog.css')
PREFERENCES_UI_FILE = os.path.join(_core_data, 'preferences.ui')

LOCALE_DIR = os.path.join(here, 'locale')
CONTRIBUTORS_FILE = os.path.join(_base_data, 'CONTRIBUTORS.rst')
ICON_FILE = os.path.join(_base_data, 'gtimelog.png')
ICON_LARGE_FILE = os.path.join(_base_data, 'gtimelog-large.png')
