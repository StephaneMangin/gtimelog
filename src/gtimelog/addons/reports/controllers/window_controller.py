import logging
from gettext import gettext as _

from gtimelog.addons.base.helpers import swap_widget
from gtimelog.models import Controller, component_registry

log = logging.getLogger('gtimelog')


class WindowController(Controller):
    """Window controller for reports addon."""

    _inherit = 'window.controller'

    def __init__(self, window):
        super().__init__(window)
        self.builder = None
        self.email_delivery_available = component_registry.is_registered('report.mail.delivery')
        self.report_view = None

        self.send_report_action = None
        self.send_report_button = None
        self.cancel_report_button = None
        self.download_csv_button = None
        self.sender_entry = None
        self.recipient_entry = None
        self.subject_entry = None
        self.style_combo = None
        self.infobar = None
        self.infobar_label = None
        self.task_pane_button = None

    def initialize(self, window):
        """Initialize report mode selector."""
        from gtimelog.addons.reports.views.report_view import ReportView

        super().initialize(window)
        self.window = window
        self.builder = window.builder

        report_view_placeholder = self.builder.get_object('report_view')
        if report_view_placeholder is None:
            return

        self.send_report_button = self.builder.get_object('send_report_button')
        self.cancel_report_button = self.builder.get_object('cancel_report_button')
        self.download_csv_button = self.builder.get_object('download_csv_button')
        self.sender_entry = self.builder.get_object('sender_entry')
        self.recipient_entry = self.builder.get_object('recipient_entry')
        self.subject_entry = self.builder.get_object('subject_entry')
        self.style_combo = self.builder.get_object('style_combo')
        self.infobar = self.builder.get_object('report_infobar')
        self.infobar_label = self.builder.get_object('infobar_label')
        self.task_pane_button = self.builder.get_object('task_pane_button')

        if self.infobar:
            self.infobar.connect('response', lambda *args: self.infobar.hide())

        self.report_view = ReportView()
        swap_widget(self.builder, 'report_view', self.report_view)

        self.report_view.timelog = getattr(self.window, 'timelog', None)
        self.window.bind_property('date', self.report_view, 'date', self.gi().GObject.BindingFlags.SYNC_CREATE)
        self.report_view.time_range = getattr(self.window, 'time_range', 'day')

        if self.sender_entry:
            self.sender_entry.bind_property(
                'text', self.report_view, 'sender', self.gi().GObject.BindingFlags.SYNC_CREATE
            )
        if self.recipient_entry:
            self.recipient_entry.bind_property(
                'text', self.report_view, 'recipient', self.gi().GObject.BindingFlags.SYNC_CREATE
            )
        if self.subject_entry:
            self.report_view.bind_property(
                'subject', self.subject_entry, 'text', self.gi().GObject.BindingFlags.DEFAULT
            )

        if self.style_combo:
            self._init_style_combo()

        self.report_view.connect('notify::recipient', self._update_send_availability)
        self.report_view.connect('notify::body', self._update_send_availability)
        self.report_view.connect('notify::report-status', self._update_already_sent_indication)

        self.window.report_view = self.report_view
        self.window.sender_entry = self.sender_entry
        self.window.recipient_entry = self.recipient_entry
        self.window.subject_entry = self.subject_entry
        self.window.infobar = self.infobar
        self.window.infobar_label = self.infobar_label
        self.window.on_cancel_report = self.on_cancel_report

        report_action = self.gi().Gio.SimpleAction.new('report', None)
        report_action.connect('activate', self.on_report)
        self.window.add_action(report_action)

        cancel_report_action = self.gi().Gio.SimpleAction.new('cancel-report', None)
        cancel_report_action.connect('activate', self.on_cancel_report)
        self.window.add_action(cancel_report_action)

        self.send_report_action = self.gi().Gio.SimpleAction.new('send-report', None)
        self.send_report_action.set_enabled(False)
        self.send_report_action.connect('activate', self.on_send_report)
        self.window.add_action(self.send_report_action)

        self.window.actions.send_report = self.send_report_action
        self.window.actions.report = report_action

    def bind_settings(self, window):
        """Bind report settings to window."""
        super().bind_settings(window)
        gs = window.gsettings

        rv = getattr(window, 'report_view', None)
        if rv is None:
            return

        gs.bind('name', rv, 'name', self.gi().Gio.SettingsBindFlags.DEFAULT)
        gs.bind('report-style', rv, 'report-style', self.gi().Gio.SettingsBindFlags.DEFAULT)

        sender_entry = getattr(window, 'sender_entry', None)
        if sender_entry:
            gs.bind('sender', sender_entry, 'text', self.gi().Gio.SettingsBindFlags.DEFAULT)
        recipient_entry = getattr(window, 'recipient_entry', None)
        if recipient_entry:
            gs.bind('list-email', recipient_entry, 'text', self.gi().Gio.SettingsBindFlags.DEFAULT)

    def _update_send_availability(self, *_args):
        if self.window.main_stack.get_visible_child_name() == 'report':
            can_send = self.email_delivery_available and bool(self.report_view.recipient and self.report_view.body)
        else:
            can_send = False
        if self.send_report_action is not None:
            self.send_report_action.set_enabled(can_send)

    def _update_already_sent_indication(self, *_args):
        if not self.infobar:
            return
        if self.report_view.report_status == 'sent':
            self.infobar_label.set_text(_('Report already sent'))
            self.infobar.show()
            self.infobar.queue_resize()
        elif self.report_view.report_status == 'sent-elsewhere':
            self.infobar_label.set_text(_('Report already sent (to {})').format(self.report_view.report_sent_to))
            self.infobar.show()
            self.infobar.queue_resize()
        else:
            self.infobar.hide()

    def on_report(self, action, parameter):
        if self.window.main_stack.get_visible_child_name() == 'report':
            self.on_cancel_report(action, parameter)
            return

        self.window.saved_date = self.window.date
        self.window.saved_time_range = self.window.time_range
        self.window.main_stack.set_visible_child_name('report')
        self.window.view_button.hide()
        if self.task_pane_button:
            self.task_pane_button.hide()
        self.window.menu_button.hide()
        if self.cancel_report_button:
            self.cancel_report_button.show()
        if self.send_report_button:
            if self.email_delivery_available:
                self.send_report_button.show()
            else:
                self.send_report_button.hide()
        if self.download_csv_button:
            self.download_csv_button.show()
        self.report_view.show()
        self.window.headerbar.set_show_close_button(False)
        self.window.set_title(_('Report'))
        self._update_send_availability()

    def on_cancel_report(self, action=None, parameter=None):
        if self.window.main_stack.get_visible_child_name() != 'report':
            self.window.search_bar.set_search_mode(False)
            self.window.filter_text = ''
            log_view = getattr(self.window, 'log_view', None)
            if log_view is not None:
                log_view.filter_text = ''
            return

        self.window.main_stack.set_visible_child_name('entry')
        self.window.view_button.show()
        if self.task_pane_button:
            self.task_pane_button.show()
        self.window.menu_button.show()
        if self.cancel_report_button:
            self.cancel_report_button.hide()
        if self.send_report_button:
            self.send_report_button.hide()
        if self.download_csv_button:
            self.download_csv_button.hide()
        self.report_view.hide()
        if self.infobar:
            self.infobar.hide()
        self.window.headerbar.set_show_close_button(True)
        self.window.set_title(_('Time Log'))
        self.window.date = self.window.saved_date
        time_range_action = getattr(self.window.actions, 'time_range', None)
        if time_range_action is not None:
            time_range_action.activate(self.gi().GLib.Variant('s', self.window.saved_time_range))
        else:
            self.window.time_range = self.window.saved_time_range
            if self.report_view is not None:
                self.report_view.time_range = self.window.saved_time_range
        self._update_send_availability()
        self.window.add_button.grab_default()

    def _record_sent_email(self, time_range, date, recipient):
        try:
            report_kinds = self.env['reports.service'].REPORT_KINDS
            report_kind = report_kinds[time_range]
            self.report_view.record.record(report_kind, date, recipient)
        except OSError as error:
            log.error(_("Couldn't append to {}: {}").format(self.report_view.record.filename, error))

    def _on_send_success(self):
        self._record_sent_email(self.report_view.time_range, self.report_view.date, self.report_view.recipient)
        self.on_cancel_report()

    def _on_send_error(self, error_message):
        if self.infobar_label:
            self.infobar_label.set_text(
                _("Couldn't send email to {}: {}.").format(self.report_view.recipient, error_message)
            )
        if self.infobar:
            self.infobar.show()

    def on_send_report(self, action, parameter):
        if self.window.main_stack.get_visible_child_name() != 'report':
            return
        if not self.email_delivery_available:
            return

        sender = self.report_view.sender
        recipient = self.report_view.recipient
        subject = self.report_view.subject
        body = self.report_view.body
        attach_csv = self.window.gsettings.get_boolean('attach-csv-to-reports')
        attach_ical = self.window.gsettings.get_boolean('attach-ical-to-reports')
        csv_content = self.report_view.csv_attachment if attach_csv else None
        ical_content = None

        if attach_ical:
            time_window = self.report_view.get_time_window()
            exports_cls = self.env['exports']
            exports = exports_cls(time_window)
            render_ical = getattr(exports, 'icalendar', None)
            if callable(render_ical):
                from io import StringIO

                ical_output = StringIO()
                render_ical(ical_output)
                ical_content = ical_output.getvalue()

        if not body or not recipient:
            return

        delivery_cls = self.env['report.mail.delivery']
        delivery = delivery_cls()
        delivery.send_report(
            window=self.window,
            report_view=self.report_view,
            sender=sender,
            recipient=recipient,
            subject=subject,
            body=body,
            csv_content=csv_content,
            ical_content=ical_content,
            on_success=self._on_send_success,
            on_error=self._on_send_error,
        )

    def _init_style_combo(self):
        """Initialize and bind the style combo box."""
        # Get available styles from the service
        try:
            styles_service = self.env.get('reports.styles.service')
            available_styles = styles_service.get_available_styles()
        except (AttributeError, ValueError):
            # Fallback if service not available
            available_styles = ['plain']

        # Add items to the combo box
        for style in available_styles:
            self.style_combo.append_text(style)

        # Create mapping for style to index
        style_to_index = {style: idx for idx, style in enumerate(available_styles)}

        # Set the combo box to match the report view's report_style
        if self.report_view.report_style and self.report_view.report_style in style_to_index:
            self.style_combo.set_active(style_to_index[self.report_view.report_style])
        else:
            # Default to first available style
            self.style_combo.set_active(0)

        # Store available styles for later use in callbacks
        self._available_styles = available_styles

        # Connect combo box changes to report_style
        self.style_combo.connect('changed', self._on_style_combo_changed)

        # Connect report_view changes back to combo box
        self.report_view.connect('notify::report-style', self._on_report_style_changed)

    def _on_style_combo_changed(self, combo):
        """Handle style combo box selection change."""
        index = combo.get_active()
        available_styles = getattr(self, '_available_styles', ['plain'])
        if 0 <= index < len(available_styles):
            style = available_styles[index]
            if self.report_view.report_style != style:
                self.report_view.report_style = style

    def _on_report_style_changed(self, *_args):
        """Handle report_style property change."""
        style = self.report_view.report_style
        available_styles = getattr(self, '_available_styles', ['plain'])
        style_to_index = {s: idx for idx, s in enumerate(available_styles)}
        if style in style_to_index:
            index = style_to_index[style]
            if self.style_combo.get_active() != index:
                self.style_combo.set_active(index)

