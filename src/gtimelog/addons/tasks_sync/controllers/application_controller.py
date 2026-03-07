from gtimelog.models import Controller


class ApplicationController(Controller):
    """Register actions that trigger synchronization manually."""

    _inherit = 'app.controller'

    def startup(self, app):
        super().startup(app)

        def _on_edit_tasks(_action, _parameter):
            gsettings = self.gi().Gio.Settings.new('org.gtimelog')
            if gsettings.get_boolean('remote-task-list'):
                uri = gsettings.get_string('task-list-edit-url')
                window = app.get_active_window()
                if window is not None:
                    window.editing_remote_tasks = True
                if uri:
                    self.gi().Gtk.show_uri(None, uri, self.gi().Gdk.CURRENT_TIME)
                return

            settings_cls = self.env['settings']
            app.open_in_editor(settings_cls().get_task_list_file())

        def _on_refresh_tasks(_action, _parameter):
            window = app.get_active_window()
            if window is not None and hasattr(window, 'download_tasks'):
                window.download_tasks()

        if app.lookup_action('edit-tasks') is not None:
            app.remove_action('edit-tasks')
        if app.lookup_action('refresh-tasks') is not None:
            app.remove_action('refresh-tasks')

        edit_tasks = self.gi().Gio.SimpleAction.new('edit-tasks', None)
        edit_tasks.connect('activate', _on_edit_tasks)
        app.add_action(edit_tasks)
        app.actions.edit_tasks = edit_tasks

        refresh_tasks = self.gi().Gio.SimpleAction.new('refresh-tasks', None)
        refresh_tasks.connect('activate', _on_refresh_tasks)
        app.add_action(refresh_tasks)
        app.actions.refresh_tasks = refresh_tasks
