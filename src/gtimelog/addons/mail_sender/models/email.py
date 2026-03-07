import collections
import email.header
import email.mime.base
import email.mime.multipart
import email.mime.text
import smtplib
from email.encoders import encode_base64
from email.utils import formataddr, parseaddr

from gtimelog import __version__
from gtimelog.addons.base.helpers import isascii

MailProtocol = collections.namedtuple('MailProtocol', 'factory, startssl')

MAIL_PROTOCOLS = {
    'SMTP': MailProtocol(smtplib.SMTP, False),
    'SMTPS': MailProtocol(smtplib.SMTP_SSL, False),
    'SMTP (StartTLS)': MailProtocol(smtplib.SMTP, True),
}


def address_header(name_and_address):
    if isascii(name_and_address):
        return name_and_address
    name, addr = parseaddr(name_and_address)
    name = str(email.header.Header(name, 'UTF-8'))
    return formataddr((name, addr))


def subject_header(header):
    if isascii(header):
        return header
    return email.header.Header(header, 'UTF-8')


def prepare_message(sender, recipient, subject, body, csv_attachment=None, ical_attachment=None):
    """Prepare an email message with optional CSV and iCalendar attachments."""
    if csv_attachment or ical_attachment:
        msg = email.mime.multipart.MIMEMultipart()
        if isascii(body):
            body_part = email.mime.text.MIMEText(body)
        else:
            body_part = email.mime.text.MIMEText(body, _charset='UTF-8')
        msg.attach(body_part)
        if csv_attachment:
            filename, csv_content = csv_attachment
            csv_part = email.mime.base.MIMEBase('text', 'csv')
            csv_part.set_payload(csv_content.encode('utf-8'))
            encode_base64(csv_part)
            csv_part.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(csv_part)
        if ical_attachment:
            filename, ical_content = ical_attachment
            ical_part = email.mime.base.MIMEBase('text', 'calendar')
            ical_part.set_payload(ical_content.encode('utf-8'))
            encode_base64(ical_part)
            ical_part.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(ical_part)
    else:
        msg = email.mime.text.MIMEText(body) if isascii(body) else email.mime.text.MIMEText(body, _charset='UTF-8')

    if sender:
        msg['From'] = address_header(sender)
    msg['To'] = address_header(recipient)
    msg['Subject'] = subject_header(subject)
    msg['User-Agent'] = f'gtimelog/{__version__}'
    return msg
