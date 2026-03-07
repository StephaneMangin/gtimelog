import logging

from gtimelog.models import Service

from .. import report_mail_delivery_service

log = logging.getLogger('gtimelog')


class ReportMailDeliveryService(Service):
    """Addon-level extension point for report mail delivery integration."""

    _inherit = 'report.mail.delivery'
    BASE_REPORT_MAIL_DELIVERY_MODULE = report_mail_delivery_service
    OVERRIDE_SOURCE = 'mail_sender-addon-integration'

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
        log.debug('report.mail.delivery override active (mail_sender)')
        return super().send_report(
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
        )
