from io import StringIO

from gi.repository import GLib, GObject, Gtk

from gtimelog.models import component_registry


class ReportView(Gtk.TextView):
    timelog = GObject.Property(type=object, default=None, nick='Time log', blurb='Time log object')

    name = GObject.Property(type=str, nick='Name', blurb='Name of report sender')

    sender = GObject.Property(type=str, nick='Sender email', blurb='Email of the report sender')

    recipient = GObject.Property(type=str, nick='Recipient email', blurb='Email of the report recipient')

    date = GObject.Property(type=object, default=None, nick='Date', blurb='Date to show (None tracks today)')

    time_range = GObject.Property(
        type=str, default='day', nick='Time range', blurb='Time range to show (day/week/month)'
    )

    report_style = GObject.Property(
        type=str,
        nick='Report style',
        blurb='Style of the report (plain/categorized/performance)',
    )

    slack_time_repartition = GObject.Property(
        type=bool,
        default=False,
        nick='Slack Time Repartition',
        blurb='Enable distribution of slack time marked with ***',
    )

    proportional_repartition = GObject.Property(
        type=bool,
        default=True,
        nick='Proportional Repartition',
        blurb='Distribute slack time proportionally based on duration',
    )

    body = GObject.Property(type=str, nick='Report body', blurb='Report body text')

    csv_attachment = GObject.Property(type=str, nick='CSV Content', blurb='CSV content for email attachment')

    report_status = GObject.Property(
        type=str,
        default='not-sent',
        nick='Report status',
        blurb='Status of this particular report (not-sent/sent/sent-elsewhere)',
    )

    report_sent_to = GObject.Property(
        type=str,
        nick='Report was sent to',
        blurb='Who already received this report (other than the current recipient?)',
    )

    def __init__(self):
        Gtk.TextView.__init__(self)
        self._update_pending = False
        self._subject = ''
        self.connect('notify::timelog', self.queue_update)
        self.connect('notify::name', self.update_subject)
        self.connect('notify::date', self.queue_update)
        self.connect('notify::time-range', self.queue_update)
        self.connect('notify::report-style', self.queue_update)
        self.connect('notify::visible', self.queue_update)
        self.connect('notify::recipient', self.update_already_sent_indication)
        self.bind_property('body', self.get_buffer(), 'text', GObject.BindingFlags.BIDIRECTIONAL)

        settings_cls = component_registry.get('settings')
        filename = settings_cls().get_report_log_file()
        report_record_cls = component_registry.get('report.record')
        self.record = report_record_cls(filename)

    def queue_update(self, *args):
        if not self._update_pending:
            self._update_pending = True
            GLib.idle_add(self.populate_report)

    def get_time_window(self):
        if self.timelog is None:
            raise RuntimeError('timelog not initialized')
        if self.time_range == 'day':
            return self.timelog.window_for_day(self.date)
        if self.time_range == 'week':
            return self.timelog.window_for_week(self.date)
        if self.time_range == 'month':
            return self.timelog.window_for_month(self.date)
        return None

    @GObject.Property(type=str, nick='Name', blurb='Report subject')
    def subject(self):
        return self._subject

    def update_subject(self, *args):
        self._subject = ''
        if self.timelog is None or self.date is None or not self.get_visible():
            self.notify('subject')
            return
        window = self.get_time_window()
        reports_cls = component_registry.get('reports')
        reports = reports_cls(window)
        reports.distribute_slack = self.slack_time_repartition
        reports.proportional = self.proportional_repartition
        name = self.name
        if self.time_range == 'day':
            self._subject = reports.daily_report_subject(name)
        elif self.time_range == 'week':
            self._subject = reports.weekly_report_subject(name)
        elif self.time_range == 'month':
            self._subject = reports.monthly_report_subject(name)
        self.notify('subject')

    def populate_report(self):
        self._update_pending = False
        self.update_subject()
        if self.timelog is None or self.date is None or not self.get_visible():
            self.get_buffer().set_text('')
            self.csv_attachment = ''
            return
        window = self.get_time_window()
        reports_cls = component_registry.get('reports')
        reports = reports_cls(window, email_headers=False, style=self.report_style)
        reports.distribute_slack = self.slack_time_repartition
        reports.proportional = self.proportional_repartition
        output = StringIO()
        recipient = self.recipient
        name = self.name
        if self.time_range == 'day':
            reports.daily_report(output, recipient, name)
        elif self.time_range == 'week':
            reports.weekly_report(output, recipient, name)
        elif self.time_range == 'month':
            reports.monthly_report(output, recipient, name)
        textbuf = self.get_buffer()
        textbuf.set_text(output.getvalue())
        textbuf.place_cursor(textbuf.get_start_iter())

        if component_registry.is_registered('exports'):
            exports_cls = component_registry.get('exports')
            exports = exports_cls(window)
            csv_output = StringIO()
            exports.to_csv_daily(csv_output)
            self.csv_attachment = csv_output.getvalue()
        else:
            self.csv_attachment = ''

        self.update_already_sent_indication()

    def update_already_sent_indication(self, *args):
        if not self.date:
            return
        report_kinds = component_registry.get('reports.service').REPORT_KINDS
        report_kind = report_kinds[self.time_range]
        recipients = self.record.get_recipients(report_kind, self.date)
        self.report_sent_to = ', '.join(sorted(set(recipients) - {self.recipient}))
        if not recipients:
            self.report_status = 'not-sent'
        elif self.recipient in recipients:
            self.report_status = 'sent'
        else:
            self.report_status = 'sent-elsewhere'
