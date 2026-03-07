from gtimelog.models import component_registry


class TimelogApplicationOrchestrator:
    """OOP orchestrator for timelog application-level shortcuts/actions."""

    def __init__(self, app):
        self.app = app

    def startup(self):
        from gi.repository import Gio

        self.app.set_accels_for_action('win.detail-level::chronological', ['<Alt>1'])
        self.app.set_accels_for_action('win.detail-level::grouped', ['<Alt>2'])
        self.app.set_accels_for_action('win.detail-level::summary', ['<Alt>3'])
        self.app.set_accels_for_action('win.time-range::day', ['<Alt>4'])
        self.app.set_accels_for_action('win.time-range::week', ['<Alt>5'])
        self.app.set_accels_for_action('win.time-range::month', ['<Alt>6'])
        self.app.set_accels_for_action('win.log-order::start-time', ['<Alt>7'])
        self.app.set_accels_for_action('win.log-order::name', ['<Alt>8'])
        self.app.set_accels_for_action('win.log-order::duration', ['<Alt>9'])
        self.app.set_accels_for_action('win.show-search-bar', ['<Primary>F'])
        self.app.set_accels_for_action('win.go-back', ['<Alt>Left'])
        self.app.set_accels_for_action('win.go-forward', ['<Alt>Right'])
        self.app.set_accels_for_action('win.go-home', ['<Alt>Home'])
        self.app.set_accels_for_action('win.focus-task-entry', ['<Primary>L'])
        self.app.set_accels_for_action('win.edit-last-entry', ['<Primary><Shift>BackSpace'])
        self.app.set_accels_for_action('app.edit-log', ['<Primary>E'])

        edit_log_action = Gio.SimpleAction.new('edit-log', None)
        edit_log_action.connect('activate', self._on_edit_log)
        self.app.add_action(edit_log_action)
        self.app.actions.edit_log = edit_log_action

    def _on_edit_log(self, action, parameter):
        settings_cls = component_registry.get('settings')
        filename = settings_cls().get_timelog_file()
        self.app.open_in_editor(filename)
