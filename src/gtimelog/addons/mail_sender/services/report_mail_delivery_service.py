import logging
import smtplib
from contextlib import closing
from email.utils import parseaddr
from gettext import gettext as _

from gtimelog.models import Service

log = logging.getLogger('gtimelog')
DEBUG = '--debug' in __import__('sys').argv


def _start_smtp_password_lookup(server, username, callback):
    from gtimelog.addons.mail_sender.models.secrets import start_smtp_password_lookup

    return start_smtp_password_lookup(server, username, callback)


class ReportMailDeliveryService(Service):
    """Integration service responsible for sending report emails."""

    _name = 'report.mail.delivery'

    def _build_csv_attachment(self, report_view, csv_content):
        if not csv_content:
            return None
        report_date = report_view.date
        date_str = report_date.strftime('%Y-%m-%d') if report_date else 'timesheet'
        filename = f'timesheet_{date_str}.csv'
        return filename, csv_content

    def _build_ical_attachment(self, report_view, ical_content):
        if not ical_content:
            return None
        report_date = report_view.date
        date_str = report_date.strftime('%Y-%m-%d') if report_date else 'timelog'
        filename = f'timelog_{date_str}.ics'
        return filename, ical_content

    def _do_send_email(self, window, sender, recipient, subject, body, csv_attachment, ical_attachment, smtp_password):
        mail_svc = self.env['mail_sender']
        smtp_server = window.gsettings.get_string('smtp-server')
        smtp_port = window.gsettings.get_int('smtp-port')
        smtp_username = window.gsettings.get_string('smtp-username')

        _sender_name, sender_address = parseaddr(sender)
        _recipient_name, recipient_address = parseaddr(recipient)

        msg = mail_svc.prepare_message(sender, recipient, subject, body, csv_attachment, ical_attachment)

        mail_protocol = window.gsettings.get_string('mail-protocol')
        factory, starttls = mail_svc.MAIL_PROTOCOLS[mail_protocol]
        try:
            log.debug('Connecting to %s port %s', smtp_server, smtp_port or '(default)')
            with closing(factory(smtp_server, smtp_port)) as smtp:
                if DEBUG:
                    smtp.set_debuglevel(1)
                if starttls:
                    smtp.starttls()
                if smtp_username:
                    smtp.login(smtp_username, smtp_password)
                smtp.sendmail(sender_address, [recipient_address], msg.as_string())
        except (OSError, smtplib.SMTPException) as exc:
            log.error(_("Couldn't send mail: %s"), exc)
            raise mail_svc.EmailError(exc) from exc

    def send_report(
        self,
        window,
        report_view,
        sender,
        recipient,
        subject,
        body,
        csv_content,
        ical_content,
        on_success,
        on_error,
    ):
        """Send a report email and notify callers through callbacks."""

        smtp_server = window.gsettings.get_string('smtp-server')
        smtp_username = window.gsettings.get_string('smtp-username')
        csv_attachment = self._build_csv_attachment(report_view, csv_content)
        ical_attachment = self._build_ical_attachment(report_view, ical_content)

        def _send_with_password(smtp_password):
            try:
                self._do_send_email(
                    window,
                    sender,
                    recipient,
                    subject,
                    body,
                    csv_attachment,
                    ical_attachment,
                    smtp_password,
                )
            except self.env['mail_sender'].EmailError as exc:
                on_error(str(exc))
            else:
                on_success()

        if smtp_username:
            _start_smtp_password_lookup(smtp_server, smtp_username, _send_with_password)
        else:
            _send_with_password('')
