from gettext import gettext as _
from io import StringIO

from gtimelog.models import Controller


class Exports(Controller):
    """iCalendar export for time log data."""

    _inherit = 'exports'

    def __init__(self, window):
        super().__init__(window)
        self.ical_service = self.env.get('application.export.ical.service')

    def icalendar(self, output):
        """Create an iCalendar file with activities."""
        self.ical_service.write_icalendar(output, self.window.all_entries())

    def show_download_ical_dialog(self, window, report_view):
        """Show file chooser and save iCalendar content to file."""
        output = StringIO()
        self.icalendar(output)
        ical_content = output.getvalue()

        if not ical_content.strip():
            dialog = self.gi().Gtk.MessageDialog(
                transient_for=window,
                modal=True,
                message_type=self.gi().Gtk.MessageType.INFO,
                buttons=self.gi().Gtk.ButtonsType.OK,
                text=_('No data to export'),
                secondary_text=_('There are no work entries for this period.'),
            )
            dialog.run()
            dialog.destroy()
            return

        date_str = report_view.date.strftime('%Y-%m-%d') if report_view.date else 'timelog'
        default_filename = f'timelog_{date_str}.ics'

        dialog = self.gi().Gtk.FileChooserDialog(
            title=_('Save iCalendar File'),
            transient_for=window,
            action=self.gi().Gtk.FileChooserAction.SAVE,
        )
        dialog.add_button(_('Cancel'), self.gi().Gtk.ResponseType.CANCEL)
        dialog.add_button(_('Save'), self.gi().Gtk.ResponseType.ACCEPT)
        dialog.set_do_overwrite_confirmation(True)
        dialog.set_current_name(default_filename)

        ical_filter = self.gi().Gtk.FileFilter()
        ical_filter.set_name(_('iCalendar files'))
        ical_filter.add_pattern('*.ics')
        dialog.add_filter(ical_filter)

        all_filter = self.gi().Gtk.FileFilter()
        all_filter.set_name(_('All files'))
        all_filter.add_pattern('*')
        dialog.add_filter(all_filter)

        response = dialog.run()
        if response == self.gi().Gtk.ResponseType.ACCEPT:
            filename = dialog.get_filename()
            if filename:
                try:
                    with open(filename, 'w', encoding='utf-8') as handle:
                        handle.write(ical_content)
                except OSError as error:
                    error_dialog = self.gi().Gtk.MessageDialog(
                        transient_for=window,
                        modal=True,
                        message_type=self.gi().Gtk.MessageType.ERROR,
                        buttons=self.gi().Gtk.ButtonsType.OK,
                        text=_('Error saving file'),
                        secondary_text=str(error),
                    )
                    error_dialog.run()
                    error_dialog.destroy()

        dialog.destroy()

    @classmethod
    def setup_window_action(cls, window):
        """Setup download-ical GTK action on window."""
        from gtimelog.models import component_registry

        gi = cls.gi()
        report_view = getattr(window, 'report_view', None)
        if report_view is None:
            return

        def _on_download_ical(_action, _parameter):
            if window.main_stack.get_visible_child_name() != 'report':
                return
            time_window = report_view.get_time_window()
            exports_cls = component_registry.get('exports')
            exports = exports_cls(time_window)
            show_dialog = getattr(exports, 'show_download_ical_dialog', None)
            if callable(show_dialog):
                show_dialog(window, report_view)

        download_ical_action = gi.Gio.SimpleAction.new('download-ical', None)
        download_ical_action.connect('activate', _on_download_ical)
        window.add_action(download_ical_action)
