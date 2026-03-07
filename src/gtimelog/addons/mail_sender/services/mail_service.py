from gtimelog.models import Service

from ..models.email import (
    MAIL_PROTOCOLS,
    MailProtocol,
    address_header,
    prepare_message,
    subject_header,
)
from ..models.email_error import EmailError


class MailService(Service):
    """Email sending capabilities."""

    _name = 'mail_sender'

    EmailError = EmailError
    MailProtocol = MailProtocol
    MAIL_PROTOCOLS = MAIL_PROTOCOLS

    prepare_message = staticmethod(prepare_message)
    address_header = staticmethod(address_header)
    subject_header = staticmethod(subject_header)
