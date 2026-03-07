import datetime
import logging
from gettext import gettext as _

from gtimelog.addons import registry as addons_registry
from gtimelog.addons.base.helpers import format_duration, mark_time, swap_widget
from gtimelog.addons.base.models.time_utils import virtual_day
from gtimelog.models import Controller, component_registry

log = logging.getLogger('gtimelog')


class WindowController(Controller):
    """Timelog window initialization controller."""

    _inherit = 'window.controller'

    def initialize(self, window):
        """Set up timelog widgets and actions."""
        from gtimelog.addons.timelog.views.log_view import LogView
        from gtimelog.addons.timelog.views.task_entry import TaskEntry

        super().initialize(window)

        task_entry = TaskEntry()
        swap_widget(window.builder, 'task_entry', task_entry)
        task_entry.grab_focus()
        window.task_entry = task_entry

        log_view = LogView()
        swap_widget(window.builder, 'log_view', log_view)
        window.log_view = log_view

        add_button = window.builder.get_object('add_button')
        add_button.grab_default()
        window.add_button = add_button

        window.search_bar = window.builder.get_object('search_bar')
        window.time_label = window.builder.get_object('time_label')
        window.timelog = None
        window.detail_level = 'chronological'
        window.time_range = 'day'
        window.log_order = 'start-time'
        window.filter_text = ''
        window.grouped_entries_ordering_source = None

        # Generic extension point for addons that need extra window state.
        self.augment_window_state(window)
        addons_registry.trigger_hook('timelog_window_state', window)

        task_entry.timelog = window.timelog
        log_view.timelog = window.timelog
        log_view.grouped_entries_ordering_source = window.grouped_entries_ordering_source
        log_view.detail_level = window.detail_level
        log_view.time_range = window.time_range
        log_view.log_order = window.log_order
        log_view.filter_text = window.filter_text

        # Generic extension point for addons that need to configure LogView.
        self.configure_log_view(window, log_view)
        addons_registry.trigger_hook('timelog_log_view_configure', window, log_view)

        self._register_property_actions(window)
        self._bind_properties(window, task_entry, log_view)
        self._register_actions(window)
        self._register_signals(window, task_entry)

        window.gsettings.connect('changed::virtual-midnight', self._virtual_midnight_changed, window)

        window.date = None
        self.gi().GLib.idle_add(self._load_log, window)
        self._tick(window, True)
        self.gi().GLib.timeout_add_seconds(1, self._tick, window)
        mark_time('timelog addon initialized')

    def augment_window_state(self, window):
        """Extension point for addons to enrich window state.

        Parent implementation is intentionally empty and keeps timelog
        independent from child-addon concepts.
        """

    def configure_log_view(self, window, log_view):
        """Extension point for addons to configure LogView behavior.

        Parent implementation is intentionally empty and keeps timelog
        independent from child-addon concepts.
        """

    def bind_settings(self, window):
        """Bind timelog-related GSettings."""
        super().bind_settings(window)
        gs = window.gsettings
        self._set_detail_level(window, gs.get_string('detail-level'))
        self._set_log_order(window, gs.get_string('log-order'))
        gs.bind('rounding-time', window.log_view, 'rounding-time', self.gi().Gio.SettingsBindFlags.DEFAULT)
        gs.bind(
            'rounding-time-force-above',
            window.log_view,
            'rounding-time-force-above',
            self.gi().Gio.SettingsBindFlags.DEFAULT,
        )

    @staticmethod
    def window_focus_reload(window):
        WindowController._check_reload(window)

    def _register_property_actions(self, window):
        detail_level = self.gi().Gio.SimpleAction.new_stateful(
            'detail-level',
            self.gi().GLib.VariantType.new('s'),
            self.gi().GLib.Variant('s', window.detail_level),
        )
        detail_level.connect('activate', self._on_detail_level_action, window)
        window.add_action(detail_level)
        window.actions.detail_level = detail_level

        time_range = self.gi().Gio.SimpleAction.new_stateful(
            'time-range',
            self.gi().GLib.VariantType.new('s'),
            self.gi().GLib.Variant('s', window.time_range),
        )
        time_range.connect('activate', self._on_time_range_action, window)
        window.add_action(time_range)
        window.actions.time_range = time_range

        log_order = self.gi().Gio.SimpleAction.new_stateful(
            'log-order',
            self.gi().GLib.VariantType.new('s'),
            self.gi().GLib.Variant('s', window.log_order),
        )
        log_order.connect('activate', self._on_log_order_action, window)
        window.add_action(log_order)
        window.actions.log_order = log_order

        property_action = self.gi().Gio.PropertyAction
        show_search_bar = property_action.new('show-search-bar', window.search_bar, 'search-mode-enabled')
        window.add_action(show_search_bar)
        window.actions.show_search_bar = show_search_bar

    def _bind_properties(self, window, task_entry, log_view):
        window.bind_property('showing_today', log_view, 'showing_today', self.gi().GObject.BindingFlags.DEFAULT)
        window.bind_property('date', log_view, 'date', self.gi().GObject.BindingFlags.DEFAULT)
        task_entry.bind_property('text', log_view, 'current_task', self.gi().GObject.BindingFlags.DEFAULT)
        window.bind_property('subtitle', window.headerbar, 'subtitle', self.gi().GObject.BindingFlags.DEFAULT)

    def _register_actions(self, window):
        action_defs = [
            ('go-back', self._on_go_back),
            ('go-forward', self._on_go_forward),
            ('go-home', self._on_go_home),
            ('focus-task-entry', self._on_focus_task_entry),
            ('add-entry', self._on_add_entry),
            ('edit-last-entry', self._on_edit_last_entry),
        ]
        for name, handler in action_defs:
            action = self.gi().Gio.SimpleAction.new(name, None)
            action.connect('activate', handler, window)
            window.add_action(action)
            setattr(window.actions, name.replace('-', '_'), action)

        window.actions.add_entry.set_enabled(False)

    def _register_signals(self, window, task_entry):
        search_entry = window.builder.get_object('search_entry')
        search_entry.connect('search-changed', self._on_search_changed, window)

        task_entry.connect('changed', self._task_entry_changed, window)

    @staticmethod
    def _set_detail_level(window, value):
        gi = WindowController.gi()
        WindowController._domain_policy().validate_detail_level(value)
        window.detail_level = value
        window.log_view.detail_level = value
        action = getattr(window.actions, 'detail_level', None)
        if action is not None and action.get_state().get_string() != value:
            action.set_state(gi.GLib.Variant('s', value))
        window.notify('subtitle')

    @staticmethod
    def _set_time_range(window, value):
        gi = WindowController.gi()
        WindowController._domain_policy().validate_time_range(value)
        window.time_range = value
        window.log_view.time_range = value
        report_view = getattr(window, 'report_view', None)
        if report_view is not None:
            report_view.time_range = value
        action = getattr(window.actions, 'time_range', None)
        if action is not None and action.get_state().get_string() != value:
            action.set_state(gi.GLib.Variant('s', value))
        window.notify('subtitle')

    @staticmethod
    def _set_log_order(window, value):
        gi = WindowController.gi()
        window.log_order = value
        window.log_view.log_order = value
        action = getattr(window.actions, 'log_order', None)
        if action is not None and action.get_state().get_string() != value:
            action.set_state(gi.GLib.Variant('s', value))

    def _on_detail_level_action(self, action, parameter, window):
        if parameter is None:
            return
        value = parameter.get_string()
        self._set_detail_level(window, value)
        if window.gsettings.get_string('detail-level') != value:
            window.gsettings.set_string('detail-level', value)

    def _on_time_range_action(self, action, parameter, window):
        if parameter is None:
            return
        value = parameter.get_string()
        self._set_time_range(window, value)

    def _on_log_order_action(self, action, parameter, window):
        if parameter is None:
            return
        value = parameter.get_string()
        self._set_log_order(window, value)
        if window.gsettings.get_string('log-order') != value:
            window.gsettings.set_string('log-order', value)

    @staticmethod
    def _domain_policy():
        return component_registry.get('domain.timelog.policy')()

    @staticmethod
    def _timelog_app_service():
        return component_registry.get('application.timelog.service')()

    @staticmethod
    def _get_virtual_midnight(window):
        return WindowController._timelog_app_service().get_virtual_midnight(window.gsettings)

    @staticmethod
    def _get_now():
        return datetime.datetime.now().replace(second=0, microsecond=0)

    @staticmethod
    def _get_last_time(window):
        if window.timelog is None:
            return None
        return window.timelog.window.last_time()

    @staticmethod
    def _enable_add_entry(window):
        enabled = WindowController._domain_policy().is_add_entry_enabled(
            window.timelog is not None,
            window.task_entry.get_text(),
        )
        window.actions.add_entry.set_enabled(enabled)

    @staticmethod
    def _load_log(window):
        from gtimelog.addons.timelog.models import TimeLog
        from gtimelog.models import component_registry

        gi = WindowController.gi()
        mark_time('loading timelog')
        settings_cls = component_registry.get('settings')
        timelog = WindowController._timelog_app_service().build_timelog(
            window.gsettings,
            settings_cls().get_timelog_file(),
            TimeLog,
        )
        mark_time('timelog loaded')
        window.timelog = timelog
        WindowController._propagate_timelog(window)
        WindowController._tick(window, True)
        WindowController._enable_add_entry(window)
        mark_time('timelog presented')

        def _on_file_changed(_monitor, file, _other_file, event_type):
            log.debug('watch on %s reports %s', file.get_path(), event_type.value_nick.upper())
            if event_type == gi.Gio.FileMonitorEvent.CHANGES_DONE_HINT:
                WindowController._check_reload(window)
            else:
                gi.GLib.timeout_add_seconds(1, WindowController._check_reload, window)

        window.watch_file(timelog.filename, _on_file_changed)

    @staticmethod
    def _check_reload(window):
        if window.timelog and window.timelog.check_reload():
            WindowController._notify_timelog_consumers(window)
            WindowController._tick(window, True)

    @staticmethod
    def _propagate_timelog(window):
        task_entry = getattr(window, 'task_entry', None)
        if task_entry is not None:
            task_entry.timelog = window.timelog
        log_view = getattr(window, 'log_view', None)
        if log_view is not None:
            log_view.timelog = window.timelog
        report_view = getattr(window, 'report_view', None)
        if report_view is not None:
            report_view.timelog = window.timelog

    @staticmethod
    def _notify_timelog_consumers(window):
        task_entry = getattr(window, 'task_entry', None)
        if task_entry is not None:
            task_entry.notify('timelog')
        log_view = getattr(window, 'log_view', None)
        if log_view is not None:
            log_view.notify('timelog')
        report_view = getattr(window, 'report_view', None)
        if report_view is not None:
            report_view.notify('timelog')

    @staticmethod
    def _virtual_midnight_changed(gsettings, _key, window):
        if window.timelog:
            window.timelog.virtual_midnight = WindowController._get_virtual_midnight(window)

    @staticmethod
    def _tick(window, force_update=False):
        now = WindowController._get_now()
        if not force_update and now == window.last_tick:
            return True
        window.last_tick = now
        last_time = WindowController._get_last_time(window)
        if last_time is None:
            window.time_label.set_text(now.strftime(_('%H:%M')))
        else:
            window.time_label.set_text(format_duration(now - last_time))
        window.log_view.now = now
        if window.showing_today and virtual_day(now, WindowController._get_virtual_midnight(window)) != window.date:
            window.date = None
        return True

    @staticmethod
    def _on_go_back(action, parameter, window):
        window.date = WindowController._timelog_app_service().previous_date(window.date, window.time_range)

    @staticmethod
    def _on_go_forward(action, parameter, window):
        window.date = WindowController._timelog_app_service().next_date(window.date, window.time_range)

    @staticmethod
    def _on_go_home(action, parameter, window):
        window.date = WindowController._timelog_app_service().home_date()

    @staticmethod
    def _on_focus_task_entry(action, parameter, window):
        window.task_entry.grab_focus()

    @staticmethod
    def _on_edit_last_entry(action, parameter, window):
        text = window.timelog.remove_last_entry()
        if text is not None:
            window.date = None
            WindowController._notify_timelog_consumers(window)
            WindowController._tick(window, True)
            window.task_entry.set_text(text)
        window.task_entry.grab_focus()
        window.task_entry.select_region(-1, -1)

    @staticmethod
    def _on_add_entry(action, parameter, window):
        mark_time()
        mark_time('on_add_entry')
        entry, now = WindowController._timelog_app_service().prepare_entry_for_append(
            window.task_entry.get_text(),
            window.timelog.parse_correction,
        )
        if not entry:
            return
        mark_time('adding the entry')
        if WindowController._timelog_app_service().should_reset_date_after_append(window.showing_today):
            window.date = None
            mark_time('jumped to today')

        previous_day = window.timelog.day
        window.timelog.append(entry, now)
        mark_time('appended')
        same_day = window.timelog.day == previous_day
        window.log_view.entry_added(same_day)
        mark_time('log_view updated')
        window.task_entry.entry_added()
        window.task_entry.set_text('')
        window.task_entry.grab_focus()
        mark_time('focus grabbed')
        WindowController._tick(window, True)
        mark_time('label updated')

        addons_registry.trigger_hook('entry_added', window, entry)

    @staticmethod
    def _on_search_changed(search_entry, window):
        filter_text = search_entry.get_text()
        window.filter_text = filter_text
        window.log_view.filter_text = filter_text

    @staticmethod
    def _task_entry_changed(widget, window):
        WindowController._enable_add_entry(window)
