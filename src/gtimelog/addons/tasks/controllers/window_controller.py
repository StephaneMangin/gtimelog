import logging

from gtimelog.addons.base.helpers import swap_widget
from gtimelog.models import Controller

log = logging.getLogger('gtimelog')


class WindowController(Controller):
    """Window controller for tasks addon."""

    _inherit = 'window.controller'

    def __init__(self, window):
        super().__init__(window)
        self._task_list = None

    def initialize(self, window):
        """Initialize task pane and view."""
        from gtimelog.addons.tasks.views.task_list_view import TaskListView

        super().initialize(window)
        self.window = window
        builder = window.builder

        task_pane = builder.get_object('task_pane')
        if task_pane is None:
            return

        task_list = TaskListView()
        swap_widget(builder, 'task_list', task_list)
        if not hasattr(window, 'tasks'):
            window.tasks = None
        if not hasattr(window, 'grouped_entries_ordering_source'):
            window.grouped_entries_ordering_source = None
        task_list.tasks = window.tasks

        window.task_pane = task_pane
        window.task_pane_button = builder.get_object('task_pane_button')
        window.task_list = task_list
        self._task_list = task_list

        task_pane_position = window.gsettings.get_int('task-pane-position')
        window.paned.set_position(task_pane_position)
        window.paned.connect('notify::position', self._store_task_pane_position)

        show_task_pane = self.gi().Gio.PropertyAction.new('show-task-pane', task_pane, 'visible')
        window.add_action(show_task_pane)
        window.actions.show_task_pane = show_task_pane

        task_list.connect('row-activated', self._task_list_row_activated)

        window.load_tasks = self._load_tasks
        window.download_tasks = self._download_tasks
        window.check_reload_tasks = self._check_reload_tasks
        window.update_edit_tasks_availability = self._update_edit_tasks_availability

        self.gi().GLib.idle_add(self._load_tasks)

    def bind_settings(self, window):
        """Bind task settings to window."""
        super().bind_settings(window)
        gs = window.gsettings

        task_pane = getattr(window, 'task_pane', None)
        if task_pane is None:
            return

        gs.bind('show-task-pane', task_pane, 'visible', self.gi().Gio.SettingsBindFlags.DEFAULT)
        gs.bind('gtk-completion', window.task_entry, 'gtk-completion-enabled', self.gi().Gio.SettingsBindFlags.DEFAULT)
        window.update_edit_tasks_availability()

    def _store_task_pane_position(self, *args):
        task_pane_position = self.window.paned.get_position()
        old_position = self.window.gsettings.get_int('task-pane-position')
        if task_pane_position != old_position:
            self.window.gsettings.set_int('task-pane-position', task_pane_position)

    def _task_list_row_activated(self, _treeview, path, _view_column):
        task = self._task_list.get_task_for_row(path)
        self.window.task_entry.set_text(task)
        self.gi().GLib.idle_add(self._focus_task_entry)

    def _focus_task_entry(self):
        self.window.task_entry.grab_focus()
        self.window.task_entry.set_position(-1)

    def _download_tasks(self):
        """Hook method intentionally empty in local-only tasks addon."""

    def _load_tasks(self, *args):
        task_list_cls = self.env['task.list']
        settings_cls = self.env['settings']

        filename = settings_cls().get_task_list_file()
        tasks = task_list_cls(filename)

        if self.window.tasks:
            self.window.unwatch_file(self.window.tasks.filename)

        self.window.tasks = tasks
        self.window.grouped_entries_ordering_source = tasks
        self._propagate_tasks()
        self.window.watch_file(self.window.tasks.filename, self._on_tasks_file_changed)
        self._update_edit_tasks_availability()

    def _update_edit_tasks_availability(self, *args):
        if hasattr(self.window.app.actions, 'edit_tasks'):
            self.window.app.actions.edit_tasks.set_enabled(True)

    def _on_tasks_file_changed(self, _monitor, file, _other_file, event_type):
        log.debug('watch on %s reports %s', file.get_path(), event_type.value_nick.upper())
        if event_type == self.gi().Gio.FileMonitorEvent.CHANGES_DONE_HINT:
            self._check_reload_tasks()
        else:
            self.gi().GLib.timeout_add_seconds(1, self._check_reload_tasks)

    def _check_reload_tasks(self):
        if self.window.tasks and self.window.tasks.check_reload():
            self._notify_tasks_consumers()

    def _propagate_tasks(self):
        if self._task_list is not None:
            self._task_list.tasks = self.window.tasks
        log_view = getattr(self.window, 'log_view', None)
        if log_view is not None:
            log_view.grouped_entries_ordering_source = self.window.grouped_entries_ordering_source

    def _notify_tasks_consumers(self):
        if self._task_list is not None:
            self._task_list.notify('tasks')
        log_view = getattr(self.window, 'log_view', None)
        if log_view is not None:
            log_view.notify('grouped-entries-ordering-source')
