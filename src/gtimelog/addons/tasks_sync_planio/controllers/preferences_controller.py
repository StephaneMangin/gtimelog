from gtimelog.models import Controller


class PreferencesController(Controller):
    """Bind Planio preferences and keyring-backed API key field."""

    _inherit = 'prefs.controller'

    SYNC_URL = 'sync://planio'

    def initialize(self, dialog):  # noqa: C901
        super().initialize(dialog)
        builder = dialog.builder
        gsettings = dialog.gsettings

        planio_enabled_switch = builder.get_object('planio_enabled_switch')
        if planio_enabled_switch is None:
            return

        planio_url_entry = builder.get_object('planio_url_entry')
        planio_api_key_entry = builder.get_object('planio_api_key_entry')
        planio_customer_entry = builder.get_object('planio_customer_entry')
        planio_project_filter_entry = builder.get_object('planio_project_filter_entry')
        planio_category_filter_entry = builder.get_object('planio_category_filter_entry')
        planio_exclude_resolved_switch = builder.get_object('planio_exclude_resolved_switch')
        planio_auto_sync_switch = builder.get_object('planio_auto_sync_switch')
        planio_auto_sync_interval_entry = builder.get_object('planio_auto_sync_interval_entry')
        planio_task_format_entry = builder.get_object('planio_task_format_entry')
        planio_last_sync_status_value = builder.get_object('planio_last_sync_status_value')
        planio_last_sync_time_value = builder.get_object('planio_last_sync_time_value')
        sync_now_button = builder.get_object('planio_sync_now_button')

        gsettings.bind('planio-enabled', planio_enabled_switch, 'active', self.gi().Gio.SettingsBindFlags.DEFAULT)
        gsettings.bind('planio-url', planio_url_entry, 'text', self.gi().Gio.SettingsBindFlags.DEFAULT)
        gsettings.bind('planio-customer', planio_customer_entry, 'text', self.gi().Gio.SettingsBindFlags.DEFAULT)
        gsettings.bind(
            'planio-project-filter', planio_project_filter_entry, 'text', self.gi().Gio.SettingsBindFlags.DEFAULT
        )
        gsettings.bind(
            'planio-category-filter', planio_category_filter_entry, 'text', self.gi().Gio.SettingsBindFlags.DEFAULT
        )
        gsettings.bind(
            'planio-exclude-resolved', planio_exclude_resolved_switch, 'active', self.gi().Gio.SettingsBindFlags.DEFAULT
        )
        gsettings.bind('auto-sync-enabled', planio_auto_sync_switch, 'active', self.gi().Gio.SettingsBindFlags.DEFAULT)
        gsettings.bind(
            'auto-sync-interval-minutes',
            planio_auto_sync_interval_entry,
            'value',
            self.gi().Gio.SettingsBindFlags.DEFAULT,
        )
        gsettings.bind('planio-task-format', planio_task_format_entry, 'text', self.gi().Gio.SettingsBindFlags.DEFAULT)

        secrets_cls = self.env['planio.secrets']
        secrets = secrets_cls()

        def _load_api_key(*_args):
            planio_api_key_entry.set_text(secrets.get_api_key(gsettings.get_string('planio-url')))

        def _save_api_key(*_args):
            secrets.set_api_key(gsettings.get_string('planio-url'), planio_api_key_entry.get_text())

        def _enable_planio_mode(*_args):
            """Enable Planio sync URL and task list when Planio is enabled."""
            if gsettings.get_string('task-list-url') != self.SYNC_URL:
                gsettings.set_string('task-list-url', self.SYNC_URL)
            if not gsettings.get_boolean('remote-task-list'):
                gsettings.set_boolean('remote-task-list', True)
            planio_url = gsettings.get_string('planio-url')
            if planio_url and not gsettings.get_string('task-list-edit-url'):
                gsettings.set_string('task-list-edit-url', planio_url)

        def _disable_planio_mode(*_args):
            """Disable Planio sync URL and task list when Planio is disabled."""
            if gsettings.get_string('task-list-url') == self.SYNC_URL:
                gsettings.set_string('task-list-url', '')
            if gsettings.get_boolean('remote-task-list'):
                gsettings.set_boolean('remote-task-list', False)

        def _sync_remote_mode(*_args):
            """Sync remote task list settings with Planio enabled state."""
            if gsettings.get_boolean('planio-enabled'):
                _enable_planio_mode()
            else:
                _disable_planio_mode()

        def _refresh_sync_status(*_args):
            status_message = gsettings.get_string('last-sync-message')
            status_time = gsettings.get_string('last-sync-at')
            if planio_last_sync_status_value is not None:
                planio_last_sync_status_value.set_text(status_message or 'Not synchronized yet.')
            if planio_last_sync_time_value is not None:
                planio_last_sync_time_value.set_text(status_time or '-')

        if sync_now_button is not None:
            transient = dialog.get_transient_for()
            app_actions = getattr(getattr(transient, 'app', None), 'actions', None)
            sync_now_button.connect(
                'clicked',
                lambda *_args: app_actions.refresh_tasks.activate(None)
                if app_actions is not None and hasattr(app_actions, 'refresh_tasks')
                else None,
            )

        gsettings.connect('changed::planio-enabled', _sync_remote_mode)
        gsettings.connect('changed::planio-url', _load_api_key)
        gsettings.connect('changed::last-sync-message', _refresh_sync_status)
        gsettings.connect('changed::last-sync-at', _refresh_sync_status)
        planio_api_key_entry.connect('focus-out-event', lambda *_args: _save_api_key())
        _sync_remote_mode()
        _load_api_key()
        _refresh_sync_status()
