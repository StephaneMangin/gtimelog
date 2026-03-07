import csv
import logging
from gettext import gettext as _
from io import StringIO

from gtimelog.models import Controller

log = logging.getLogger('gtimelog')


class Exports(Controller):
    """CSV export formats for time log data."""

    _inherit = 'exports'

    def __init__(self, window):
        super().__init__(window)
        self.csv_service = self.env.get('application.export.csv.service')

    def to_csv_complete(self, output, title_row=True):
        """Export work entries to a CSV file."""
        writer = csv.writer(output)
        if title_row:
            writer.writerow(['task', 'time (minutes)'])
        work, _slack = self.window.grouped_entries()
        work = self.csv_service.to_csv_complete_rows(work)
        writer.writerows(work)

    def to_csv_daily(self, output, title_row=True):
        """Export daily work, slacking, and arrival times to a CSV file."""
        writer = csv.writer(output)
        if title_row:
            writer.writerow(['date', 'day-start (hours)', 'slacking (hours)', 'work (hours)'])
        items = self.csv_service.to_csv_daily_rows(self.window.all_entries())
        writer.writerows(items)

    def show_download_dialog(self, window, report_view):
        """Show CSV download dialog with preview and save option.

        Args:
            window: Parent window for the dialog
            report_view: ReportView instance to get date/time window
        """
        # Generate daily CSV export
        output = StringIO()
        self.to_csv_daily(output)
        csv_content = output.getvalue()

        if not csv_content or len(csv_content.strip().split('\n')) <= 1:
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

        dialog = self.gi().Gtk.Dialog(
            title=_('Daily Timesheet CSV'),
            transient_for=window,
            modal=True,
            destroy_with_parent=True,
        )
        dialog.add_button(_('Close'), self.gi().Gtk.ResponseType.CLOSE)
        dialog.add_button(_('Save as...'), self.gi().Gtk.ResponseType.ACCEPT)
        dialog.set_default_size(800, 500)

        scrolled = self.gi().Gtk.ScrolledWindow()
        scrolled.set_policy(self.gi().Gtk.PolicyType.AUTOMATIC, self.gi().Gtk.PolicyType.AUTOMATIC)
        scrolled.set_margin_start(10)
        scrolled.set_margin_end(10)
        scrolled.set_margin_top(10)
        scrolled.set_margin_bottom(10)

        textview = self.gi().Gtk.TextView()
        textview.set_editable(False)
        textview.set_monospace(True)
        textview.get_buffer().set_text(csv_content)
        scrolled.add(textview)
        dialog.get_content_area().pack_start(scrolled, True, True, 0)
        dialog.show_all()

        response = dialog.run()
        if response == self.gi().Gtk.ResponseType.ACCEPT:
            self.save_csv_file(window, report_view, csv_content)
        dialog.destroy()

    def save_csv_file(self, window, report_view, csv_content):
        """Show file chooser and save CSV content to file.

        Args:
            window: Parent window for the dialog
            report_view: ReportView instance to get date for filename
            csv_content: CSV string to save
        """
        date_str = report_view.date.strftime('%Y-%m-%d') if report_view.date else 'timesheet'
        default_filename = f'timesheet_daily_{date_str}.csv'

        dialog = self.gi().Gtk.FileChooserDialog(
            title=_('Save CSV File'),
            transient_for=window,
            action=self.gi().Gtk.FileChooserAction.SAVE,
        )
        dialog.add_button(_('Cancel'), self.gi().Gtk.ResponseType.CANCEL)
        dialog.add_button(_('Save'), self.gi().Gtk.ResponseType.ACCEPT)
        dialog.set_do_overwrite_confirmation(True)
        dialog.set_current_name(default_filename)

        csv_filter = self.gi().Gtk.FileFilter()
        csv_filter.set_name(_('CSV files'))
        csv_filter.add_pattern('*.csv')
        dialog.add_filter(csv_filter)

        all_filter = self.gi().Gtk.FileFilter()
        all_filter.set_name(_('All files'))
        all_filter.add_pattern('*')
        dialog.add_filter(all_filter)

        response = dialog.run()
        if response == self.gi().Gtk.ResponseType.ACCEPT:
            filename = dialog.get_filename()
            if not filename.endswith('.csv'):
                filename += '.csv'
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(csv_content)
                log.info(_('CSV saved to {}').format(filename))
            except OSError as e:
                log.error(_('Could not save file: {}').format(e))
                error_dialog = self.gi().Gtk.MessageDialog(
                    transient_for=window,
                    modal=True,
                    message_type=self.gi().Gtk.MessageType.ERROR,
                    buttons=self.gi().Gtk.ButtonsType.OK,
                    text=_('Error saving file'),
                    secondary_text=str(e),
                )
                error_dialog.run()
                error_dialog.destroy()
        dialog.destroy()

    @classmethod
    def setup_window_action(cls, window):
        """Setup download-csv GTK action on window (inheritable).

        This method can be overridden by subclasses to customize
        the action registration behavior or add additional actions.

        Args:
            window: GTK window instance to add the action to
        """
        from gtimelog.models import component_registry

        gi = cls.gi()
        report_view = getattr(window, 'report_view', None)
        if report_view is None:
            return

        def _on_download_csv(action, parameter):
            """Handle download-csv action activation."""
            if window.main_stack.get_visible_child_name() != 'report':
                return

            # Get the exports controller instance and delegate
            tw = report_view.get_time_window()
            exports_cls = component_registry.get('exports')
            exports = exports_cls(tw)
            exports.show_download_dialog(window, report_view)

        download_csv_action = gi.Gio.SimpleAction.new('download-csv', None)
        download_csv_action.connect('activate', _on_download_csv)
        window.add_action(download_csv_action)
