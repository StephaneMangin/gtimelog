from gtimelog.models import Controller


class ApplicationController(Controller):
    """Application controller for tasks addon."""

    _inherit = 'app.controller'

    def startup(self, app):
        """Setup task pane accelerators."""
        super().startup(app)

        def _on_edit_tasks(action, parameter):
            settings_cls = self.env['settings']
            filename = settings_cls().get_task_list_file()
            app.open_in_editor(filename)

        def _on_refresh_tasks(action, parameter):
            window = app.get_active_window()
            if window is not None and hasattr(window, 'download_tasks'):
                window.download_tasks()

        edit_tasks = self.gi().Gio.SimpleAction.new('edit-tasks', None)
        edit_tasks.connect('activate', _on_edit_tasks)
        app.add_action(edit_tasks)
        app.actions.edit_tasks = edit_tasks

        refresh_tasks = self.gi().Gio.SimpleAction.new('refresh-tasks', None)
        refresh_tasks.connect('activate', _on_refresh_tasks)
        app.add_action(refresh_tasks)
        app.actions.refresh_tasks = refresh_tasks

        app.set_accels_for_action('win.log-order::task-list', ['<Alt>0'])
        app.set_accels_for_action('win.show-task-pane', ['F9'])
        app.set_accels_for_action('app.edit-tasks', ['<Primary>T'])
