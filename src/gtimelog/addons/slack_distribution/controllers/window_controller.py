from gtimelog.models import Controller


class WindowController(Controller):
    """Window controller for slack distribution addon."""

    _inherit = 'window.controller'

    def bind_settings(self, window):
        """Bind slack distribution settings to window."""
        super().bind_settings(window)
        gs = window.gsettings
        lv = window.log_view

        gs.bind('slack-time-repartition', lv, 'distribute-unassigned-time', self.gi().Gio.SettingsBindFlags.DEFAULT)
        gs.bind('proportional-repartition', lv, 'proportional-distribution', self.gi().Gio.SettingsBindFlags.DEFAULT)

        rv = getattr(window, 'report_view', None)
        if rv is not None:
            gs.bind('slack-time-repartition', rv, 'slack-time-repartition', self.gi().Gio.SettingsBindFlags.DEFAULT)
            gs.bind('proportional-repartition', rv, 'proportional-repartition', self.gi().Gio.SettingsBindFlags.DEFAULT)
