import os
import sys
from gettext import gettext as _

from gtimelog import require_version
from gtimelog.addons.base.helpers import DEBUG, log, make_option, mark_time
from gtimelog.paths import CSS_FILE, MENUS_UI_FILE, SHORTCUTS_UI_FILE

if DEBUG:
    os.environ['G_ENABLE_DIAGNOSTIC'] = '1'

require_version('Gtk', '3.0')
require_version('Gdk', '3.0')
from gi.repository import Gdk, Gio, GLib, Gtk  # noqa: E402

from gtimelog.addons import registry as addons_registry  # noqa: E402
from gtimelog.addons.base.models import Settings  # noqa: E402
from gtimelog.addons.base.views.window import Window  # noqa: E402
from gtimelog.models import component_registry  # noqa: E402
from gtimelog.core.ui.extensions import load_ui_with_extensions  # noqa: E402


class Application(Gtk.Application):
    class Actions:
        actions = (
            'shortcuts',
            'preferences',
            'about',
            'quit',
        )

        def __init__(self, app):
            app_service = component_registry.get('application.service')()

            for action_name in self.actions:
                action = app_service.create_simple_action(action_name, None)
                handler_name = 'on_' + action_name.replace('-', '_')
                handler = getattr(app, handler_name, None)
                if handler is not None:
                    action.connect('activate', handler)
                else:
                    hook_name = 'app_' + action_name.replace('-', '_')
                    action.connect(
                        'activate',
                        lambda _action, _parameter, _hook_name=hook_name: app.trigger_app_hook(_hook_name, app),
                    )
                app.add_action(action)
                setattr(self, action_name.replace('-', '_'), action)

            self.shortcuts.set_enabled(hasattr(Gtk, 'ShortcutsWindow'))

    def __init__(self):
        app_service = component_registry.get('application.service')()

        super().__init__(
            application_id='org.gtimelog',
            flags=app_service.get_application_flags().HANDLES_COMMAND_LINE,
        )
        app_service.set_application_name(_('Time Log'))
        app_service.set_prgname('gtimelog')
        self.add_main_option_entries(
            [
                make_option('--version', description=_('Show version number and exit')),
                make_option('--debug', description=_('Show debug information on the console')),
                make_option('--prefs', description=_('Open the preferences dialog')),
            ]
        )

    def check_schema(self):
        schema_source = Gio.SettingsSchemaSource.get_default()
        if schema_source.lookup('org.gtimelog', False) is None:
            sys.exit(
                _(
                    '\nWARNING: GSettings schema for org.gtimelog is missing!'
                    "  If you're running from a source checkout,"
                    " be sure to run 'make'."
                )
            )

    def create_data_directory(self):
        data_dir = Settings().get_data_dir()
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir)
            except OSError as e:
                log.error(
                    _('Could not create {directory}: {error}').format(directory=data_dir, error=e),
                    file=sys.stderr,
                )
            else:
                log.info(_('Created {directory}').format(directory=data_dir))

    def do_handle_local_options(self, options):
        if options.contains('version'):
            self.check_schema()
            gsettings = Gio.Settings.new('org.gtimelog')
            if not gsettings.get_boolean('settings-migrated'):
                pass
            else:
                pass
            return 0
        return -1

    def do_command_line(self, command_line):
        self.do_activate()
        options = command_line.get_options_dict()
        if options.contains('prefs'):
            self.on_preferences(None, None)
        return 0

    def do_startup(self):
        mark_time('in app startup')

        self.check_schema()
        self.create_data_directory()
        registry = addons_registry

        gsettings = Gio.Settings.new('org.gtimelog')
        disabled_addons = gsettings.get_strv('disabled-addons')

        registry.discover(disabled_addons=disabled_addons)
        mark_time('addons loaded')

        Gtk.Application.do_startup(self)

        mark_time('basic app startup done')

        css = Gtk.CssProvider()
        css.load_from_path(CSS_FILE)
        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(screen, css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        mark_time('CSS loaded')

        if Gtk.Settings.get_default().get_property('gtk-shell-shows-app-menu'):
            extended_menus_ui = load_ui_with_extensions(MENUS_UI_FILE, registry)
            if extended_menus_ui is not None:
                builder = Gtk.Builder.new_from_string(extended_menus_ui, -1)
            else:
                builder = Gtk.Builder.new_from_file(MENUS_UI_FILE)
            self.set_app_menu(builder.get_object('app_menu'))
            mark_time('menus loaded')

        self.actions = self.Actions(self)

        self.set_accels_for_action('win.show-menu', ['F10'])
        self.set_accels_for_action('app.shortcuts', ['<Primary>question'])
        self.set_accels_for_action('app.preferences', ['<Primary>P'])
        self.set_accels_for_action('app.quit', ['<Primary>Q'])
        controller_cls = component_registry.get('app.controller')
        controller = controller_cls(self)
        controller.startup(self)

        mark_time('app startup done')

    def on_quit(self, action, parameter):
        self.quit()

    def on_preferences(self, action, parameter):
        preferences_service = component_registry.get('application.preferences.service')()
        preferences_service.open_preferences(self)

    def on_about(self, action, parameter):
        about_service = component_registry.get('application.about.service')()
        about_service.show_about_dialog(self)

    def open_in_editor(self, filename):
        self.create_if_missing(filename)
        if os.name == 'nt':
            os.startfile(filename)  # noqa: S606
        else:
            uri = GLib.filename_to_uri(filename, None)
            Gtk.show_uri(None, uri, Gdk.CURRENT_TIME)

    def create_if_missing(self, filename):
        if not os.path.exists(filename):
            open(filename, 'a').close()

    def on_shortcuts(self, action, parameter):
        extended_shortcuts_ui = load_ui_with_extensions(SHORTCUTS_UI_FILE, addons_registry)
        if extended_shortcuts_ui is not None:
            builder = Gtk.Builder.new_from_string(extended_shortcuts_ui, -1)
        else:
            builder = Gtk.Builder.new_from_file(SHORTCUTS_UI_FILE)
        shortcuts_window = builder.get_object('shortcuts_window')
        shortcuts_window.set_transient_for(self.get_active_window())
        shortcuts_window.show_all()

    def trigger_app_hook(self, hook_name, *args, **kwargs):
        registry = addons_registry

        handled = registry.trigger_hook(hook_name, *args, **kwargs)
        if not handled:
            log.warning('No addon handled %s hook', hook_name)
        return bool(handled)

    def are_there_any_modals(self):
        return any(window.get_modal() for window in Gtk.Window.list_toplevels())

    def do_activate(self):
        mark_time('in app activate')
        window = self.get_active_window()
        if window is not None:
            window.present_with_time(GLib.get_monotonic_time() // 1000)
            window.present()
            return
        window = Window(self)
        mark_time('have window')
        self.add_window(window)
        mark_time('added window')
        window.show()
        mark_time('showed window')

        GLib.idle_add(mark_time, 'in main loop')

        mark_time('app activate done')
