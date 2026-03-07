import datetime
import logging
import os
from gettext import gettext as _

from gi.repository import Gdk, Gio, GLib, GObject, Gtk

from gtimelog.addons import registry as addons_registry
from gtimelog.addons.base.helpers import copy_properties, mark_time
from gtimelog.addons.base.models import Settings
from gtimelog.addons.base.models.time_utils import virtual_day
from gtimelog.models import component_registry
from gtimelog.paths import ICON_FILE, MENUS_UI_FILE, UI_FILE
from gtimelog.core.ui.extensions import load_ui_with_extensions

log = logging.getLogger('gtimelog')


class Window(Gtk.ApplicationWindow):
    date = GObject.Property(type=object, default=None, nick='Date', blurb='Date to show (None tracks today)')

    class Actions:
        """Container for window actions (populated by addons)."""

        def __init__(self, win):
            property_action = Gio.PropertyAction

            self.show_view_menu = property_action.new('show-view-menu', win.view_button, 'active')
            win.add_action(self.show_view_menu)

            self.show_menu = property_action.new('show-menu', win.menu_button, 'active')
            win.add_action(self.show_menu)

    def __init__(self, app):
        Gtk.ApplicationWindow.__init__(self, application=app, icon_name='gtimelog')

        self._watches = {}
        self._date = None
        self._showing_today = None
        self._window_size_update_timeout = None
        self.last_tick = None
        self.app = app

        mark_time('loading ui')
        extended_ui = load_ui_with_extensions(UI_FILE, addons_registry)
        if extended_ui is not None:
            builder = Gtk.Builder.new_from_string(extended_ui, -1)
        else:
            builder = Gtk.Builder.new_from_file(UI_FILE)
        mark_time('main ui loaded')

        extended_menus_ui = load_ui_with_extensions(MENUS_UI_FILE, addons_registry)
        if extended_menus_ui is not None:
            builder.add_from_string(extended_menus_ui)
        else:
            builder.add_from_file(MENUS_UI_FILE)
        mark_time('menus loaded')
        self.builder = builder

        main_window = builder.get_object('main_window')
        main_stack = builder.get_object('main_stack')
        headerbar = builder.get_object('headerbar')
        copy_properties(main_window, self)
        if os.path.exists(ICON_FILE):
            self.set_icon_from_file(ICON_FILE)
        main_window.set_titlebar(None)
        main_window.remove(main_stack)
        self.add(main_stack)
        self.set_titlebar(headerbar)

        self.view_button = builder.get_object('view_button')
        self.menu_button = builder.get_object('menu_button')
        self.menu_button.set_menu_model(builder.get_object('window_menu'))
        self.view_button.set_menu_model(builder.get_object('view_menu'))

        self.main_stack = main_stack
        self.paned = builder.get_object('paned')
        self.headerbar = headerbar

        self.actions = self.Actions(self)

        mark_time('window created')

        self.load_settings()
        self.connect('focus-in-event', self.gained_focus)
        mark_time('window ready')
        controller_cls = component_registry.get('window.controller')
        controller = controller_cls(self)
        controller.initialize(self)
        controller.bind_settings(self)

    def load_settings(self):
        self.gsettings = Gio.Settings.new('org.gtimelog')

        x, y = self.gsettings.get_value('window-position')
        w, h = self.gsettings.get_value('window-size')
        self.resize(w, h)
        if (x, y) != (-1, -1):
            self.move(x, y)
        self.paned.connect('notify::position', self.delay_store_window_size)
        self.connect('configure-event', self.delay_store_window_size)

        if not self.gsettings.get_boolean('settings-migrated'):
            old_settings = Settings()
            loaded_files = old_settings.load()

            migrator_cls = component_registry.get('gsettings.migrator')
            migrator = migrator_cls(self.gsettings, old_settings)
            migrator.migrate(old_settings)
            self.gsettings.set_boolean('settings-migrated', True)
            if loaded_files:
                log.info(
                    _('Settings from {filename} migrated to GSettings (org.gtimelog)').format(
                        filename=old_settings.get_config_file()
                    )
                )

        mark_time('settings loaded')

    def gained_focus(self, *args):
        addons_registry.trigger_hook('window_focus', self)

    def delay_store_window_size(self, *args):
        if self._window_size_update_timeout is None:
            self._window_size_update_timeout = GLib.timeout_add(500, self.store_window_size)

    def _store_window_size(self):
        position = self.get_position()
        size = self.get_size()
        old_position = self.gsettings.get_value('window-position')
        old_size = self.gsettings.get_value('window-size')
        if tuple(size) != tuple(old_size):
            self.gsettings.set_value('window-size', GLib.Variant('(ii)', size))
        if tuple(position) != tuple(old_position):
            self.gsettings.set_value('window-position', GLib.Variant('(ii)', position))

    def store_window_size(self):
        if self.props.window is not None and not self.is_maximized_in_any_way():
            self._store_window_size()
        GLib.source_remove(self._window_size_update_timeout)
        self._window_size_update_timeout = None
        return False

    def is_maximized_in_any_way(self):
        if self.props.window is None:
            raise RuntimeError('window not realized')
        maximized_flags = Gdk.WindowState.MAXIMIZED | Gdk.WindowState.TILED | Gdk.WindowState.FULLSCREEN
        return (self.props.window.get_state() & maximized_flags) != 0

    def watch_file(self, filename, callback):
        log.debug('adding watch on %s', filename)
        gf = Gio.File.new_for_path(filename)
        gfm = gf.monitor_file(Gio.FileMonitorFlags.NONE, None)
        gfm.connect('changed', callback)
        self._watches[filename] = (gfm, None)
        if os.path.islink(filename):
            realpath = os.path.join(os.path.dirname(filename), os.readlink(filename))
            log.debug('%s is a symlink, adding a watch on %s', filename, realpath)
            self._watches[filename] = (gfm, realpath)
            if realpath not in self._watches:
                self.watch_file(realpath, callback)

    def unwatch_file(self, filename):
        while filename in self._watches:
            log.debug('removing watch on %s', filename)
            filename = self._watches.pop(filename)[1]

    @date.getter
    def date(self):
        return self._date

    @date.setter
    def date(self, new_date):
        if new_date is not None and not isinstance(new_date, datetime.date):
            new_date = None

        today = virtual_day(datetime.datetime.now(), self._get_virtual_midnight())
        if new_date is None or new_date >= today:
            new_date = today

        old_date = self._date
        old_showing_today = self._showing_today
        self._date = new_date

        if new_date == today:
            self._showing_today = True
            if hasattr(self.actions, 'go_home'):
                self.actions.go_home.set_enabled(False)
                self.actions.go_forward.set_enabled(False)
        else:
            self._showing_today = False
            if hasattr(self.actions, 'go_home'):
                self.actions.go_home.set_enabled(True)
                self.actions.go_forward.set_enabled(True)

        if old_showing_today != self._showing_today:
            self.notify('showing_today')
        if old_date != self._date:
            self.notify('subtitle')

    def _get_virtual_midnight(self):
        if self.gsettings:
            h, m = self.gsettings.get_value('virtual-midnight')
            return datetime.time(h, m)
        return datetime.time(2, 0)

    @GObject.Property(
        type=bool, default=True, nick='Showing today', blurb='Currently visible time range includes today'
    )
    def showing_today(self):
        return self._showing_today

    @GObject.Property(type=str, nick='Subtitle', blurb='Description of the visible time range')
    def subtitle(self):
        date = self.date
        if not date:
            return ''
        time_range = getattr(self, 'time_range', 'day')
        if time_range == 'day':
            return _('{0:%A, %Y-%m-%d} (week {1:0>2})').format(date, date.isocalendar()[1])
        if time_range == 'week':
            monday = date - datetime.timedelta(date.weekday())
            sunday = monday + datetime.timedelta(6)
            isoyear, isoweek = date.isocalendar()[:2]
            return _('{0}, week {1} ({2:%B %-d}-{3:%-d})').format(isoyear, isoweek, monday, sunday)
        if time_range == 'month':
            return _('{0:%B %Y}').format(date)
        return None
