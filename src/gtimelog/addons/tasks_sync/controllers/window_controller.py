import logging
from gettext import gettext as _

from gtimelog import require_version
from gtimelog.addons import registry as addons_registry
from gtimelog.models import Controller

log = logging.getLogger('gtimelog.tasks_sync')


class WindowController(Controller):
    """Own remote-task-list behavior and provider synchronization flow."""

    _inherit = 'window.controller'

    def __init__(self, window):
        super().__init__(window)
        from gtimelog.addons.tasks.models.secrets import Authenticator

        self._base_download_tasks = None
        self._auto_sync_source_id = None
        self._sync_running = False

        self._download = None
        self._cancellable = None
        self._soup_session = None
        self._authenticator = Authenticator()
        self._tasks_infobar = None
        self._tasks_infobar_label = None

    def initialize(self, window):
        super().initialize(window)
        if not hasattr(window, 'download_tasks'):
            return

        self.window = window
        self._tasks_infobar = window.builder.get_object('tasks_infobar')
        self._tasks_infobar_label = window.builder.get_object('tasks_infobar_label')

        self._base_download_tasks = window.download_tasks
        window.download_tasks = self._download_tasks_proxy
        window.load_tasks = self._load_tasks
        window.update_edit_tasks_availability = self._update_edit_tasks_availability

        addons_registry.register_hook('window_focus', self._on_window_focus)

        gsettings = window.gsettings
        gsettings.connect('changed::auto-sync-enabled', self._refresh_auto_sync_timer)
        gsettings.connect('changed::auto-sync-interval-minutes', self._refresh_auto_sync_timer)
        gsettings.connect('changed::remote-task-list', self._on_remote_setting_changed)
        gsettings.connect('changed::task-list-url', self._on_remote_setting_changed)
        gsettings.connect('changed::task-list-edit-url', self._on_remote_setting_changed)

        window.connect('destroy', lambda *_args: self._stop_auto_sync_timer())
        self._refresh_auto_sync_timer()

    def bind_settings(self, window):
        super().bind_settings(window)

        if hasattr(window.app.actions, 'refresh_tasks'):
            window.gsettings.bind(
                'remote-task-list',
                window.app.actions.refresh_tasks,
                'enabled',
                self.gi().Gio.SettingsBindFlags.DEFAULT,
            )
        window.update_edit_tasks_availability()

    def _service(self):
        service_cls = self.env['application.tasks.sync.service']
        return service_cls()

    def _on_remote_setting_changed(self, *_args):
        self.window.load_tasks()
        self._refresh_auto_sync_timer()

    def _download_tasks_proxy(self, *args, show_feedback=True):
        if not self.window.gsettings.get_boolean('remote-task-list'):
            if self._base_download_tasks is not None:
                self._base_download_tasks()
            return

        service = self._service()
        if service.should_handle_remote_sync(self.window.gsettings):
            if self._sync_running:
                return
            self._sync_running = True
            try:
                success = service.sync_now(self.window.gsettings)
                if success and hasattr(self.window, 'check_reload_tasks'):
                    self.window.check_reload_tasks()
                if show_feedback:
                    self._show_sync_feedback(success)
            finally:
                self._sync_running = False
            return

        self._download_remote_tasks(show_feedback=show_feedback)

    def _download_remote_tasks(self, show_feedback=True):
        require_version('Soup', '3.0')

        self._cancel_tasks_download(hide=show_feedback)

        url = self.window.gsettings.get_string('task-list-url')
        if not url or url.startswith('sync://'):
            log.debug('Not downloading remote tasks: URL not set or handled by sync backend.')
            return

        settings_cls = self.env['settings']
        cache_filename = settings_cls().get_task_list_cache_file()

        if self._soup_session is None:
            self._soup_session = self.gi().Soup.Session()

        self._cancellable = self.gi().Gio.Cancellable()
        if show_feedback and self._tasks_infobar:
            self._tasks_infobar.set_message_type(self.gi().Gtk.MessageType.INFO)
            self._tasks_infobar_label.set_text(_('Downloading tasks...'))
            self._tasks_infobar.connect('response', lambda *a: self._cancel_tasks_download())
            self._tasks_infobar.show()
            self._tasks_infobar.queue_resize()

        message = self.gi().Soup.Message.new('GET', url)
        self._download = (message, url, show_feedback)
        message.connect('authenticate', self._authenticator.http_auth_cb)
        self._soup_session.send_and_read_async(
            message,
            self.gi().GLib.PRIORITY_DEFAULT,
            self._cancellable,
            self._tasks_downloaded,
            cache_filename,
        )

    def _tasks_downloaded(self, _session, result, cache_filename):
        require_version('Soup', '3.0')

        show_feedback = bool(self._download and self._download[2])
        message = self._soup_session.get_async_result_message(result)
        status_code = message.get_status()
        if status_code != self.gi().Soup.Status.OK:
            url = message.get_uri().to_string()
            log.error('Failed to download tasks from %s: %d %s', url, status_code, message.get_reason_phrase())
            if show_feedback and self._tasks_infobar:
                self._tasks_infobar.set_message_type(self.gi().Gtk.MessageType.ERROR)
                self._tasks_infobar_label.set_text(_('Download failed.'))
                self._tasks_infobar.connect('response', lambda *a: self._tasks_infobar.hide())
                self._tasks_infobar.show()
        else:
            content = self._soup_session.send_and_read_finish(result).get_data().decode()
            with open(cache_filename, 'w') as file_obj:
                file_obj.write(content)
            if hasattr(self.window, 'check_reload_tasks'):
                self.window.check_reload_tasks()
            if show_feedback and self._tasks_infobar:
                self._tasks_infobar.hide()
        self._download = None

    def _cancel_tasks_download(self, hide=True):
        if self._download and self._cancellable is not None:
            self._cancellable.cancel()
            self._download = None
        if hide and self._tasks_infobar:
            self._tasks_infobar.hide()

    def _load_tasks(self, *args):
        task_list_cls = self.env['task.list']
        settings_cls = self.env['settings']
        settings = settings_cls()

        # Always load local tasks.txt first
        local_filename = settings.get_task_list_file()
        tasks = task_list_cls(local_filename)

        # If remote sync is enabled, merge with remote tasks
        if self.window.gsettings.get_boolean('remote-task-list'):
            remote_filename = settings.get_task_list_cache_file()
            remote_tasks = task_list_cls(remote_filename)
            tasks.merge_with(remote_tasks)
            self._download_tasks_proxy(show_feedback=False)
        else:
            if self._tasks_infobar:
                self._tasks_infobar.hide()

        if self.window.tasks:
            self.window.unwatch_file(self.window.tasks.filename)

        self.window.tasks = tasks
        if hasattr(self, '_propagate_tasks'):
            self._propagate_tasks()
        self.window.watch_file(self.window.tasks.filename, self._on_tasks_file_changed)
        self.window.update_edit_tasks_availability()

    def _update_edit_tasks_availability(self, *args):
        if self.window.gsettings.get_boolean('remote-task-list'):
            can_edit = bool(self.window.gsettings.get_string('task-list-edit-url'))
        else:
            can_edit = True

        if hasattr(self.window.app.actions, 'edit_tasks'):
            self.window.app.actions.edit_tasks.set_enabled(can_edit)

    def _on_window_focus(self, _win):
        if getattr(self.window, 'editing_remote_tasks', False):
            self._download_tasks_proxy(show_feedback=False)
            self.window.editing_remote_tasks = False
        if hasattr(self.window, 'check_reload_tasks'):
            self.window.check_reload_tasks()

    def _should_auto_sync(self):
        gsettings = self.window.gsettings
        if not gsettings.get_boolean('auto-sync-enabled'):
            return False
        if not gsettings.get_boolean('remote-task-list'):
            return False
        service = self._service()
        return service.should_handle_remote_sync(gsettings)

    def _refresh_auto_sync_timer(self, *args):
        self._stop_auto_sync_timer()
        if not self._should_auto_sync():
            return

        interval_minutes = max(1, self.window.gsettings.get_int('auto-sync-interval-minutes'))
        self._auto_sync_source_id = self.gi().GLib.timeout_add_seconds(interval_minutes * 60, self._on_auto_sync_tick)
        log.debug('Auto-sync timer started (%d minutes).', interval_minutes)

    def _stop_auto_sync_timer(self):
        if self._auto_sync_source_id is None:
            return
        self.gi().GLib.source_remove(self._auto_sync_source_id)
        self._auto_sync_source_id = None

    def _on_auto_sync_tick(self):
        self._download_tasks_proxy(show_feedback=False)
        return True

    def _show_sync_feedback(self, success: bool):
        """Display synchronization outcome in the existing task infobar."""
        infobar = self.window.builder.get_object('tasks_infobar')
        label = self.window.builder.get_object('tasks_infobar_label')
        if infobar is None or label is None:
            return

        message = self.window.gsettings.get_string('last-sync-message').strip()
        if not message:
            message = 'Synchronization completed.' if success else 'Synchronization failed.'

        infobar.set_message_type(self.gi().Gtk.MessageType.INFO if success else self.gi().Gtk.MessageType.ERROR)
        label.set_text(message)
        infobar.show()
        infobar.queue_resize()
