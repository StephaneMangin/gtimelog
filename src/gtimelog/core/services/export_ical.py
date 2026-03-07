import datetime
import socket
from hashlib import sha256

from gtimelog.models import Service


class IcalExportApplicationService(Service):
    """Application service that renders iCalendar payloads from entries."""

    _name = 'application.export.ical.service'

    @staticmethod
    def _hash(start, stop, entry):
        return sha256((f'{start}{stop}{entry}').encode()).hexdigest()

    def icalendar_lines(self, entries):
        """Return calendar lines for the provided entries iterable."""
        lines = [
            'BEGIN:VCALENDAR',
            'PRODID:-//gtimelog.org/NONSGML GTimeLog//EN',
            'VERSION:2.0',
        ]
        idhost = socket.getfqdn()
        dtstamp = datetime.datetime.now(datetime.UTC).strftime('%Y%m%dT%H%M%SZ')
        for start, stop, _duration, _tags, entry in entries:
            escaped_summary = entry.replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,')
            lines.extend(
                [
                    'BEGIN:VEVENT',
                    f'UID:{self._hash(start, stop, entry)}@{idhost}',
                    f'SUMMARY:{escaped_summary}',
                    f'DTSTART:{start.strftime("%Y%m%dT%H%M%S")}',
                    f'DTEND:{stop.strftime("%Y%m%dT%H%M%S")}',
                    f'DTSTAMP:{dtstamp}',
                    'END:VEVENT',
                ]
            )
        lines.append('END:VCALENDAR')
        return lines

    def write_icalendar(self, output, entries):
        """Write a full iCalendar document to output."""
        for line in self.icalendar_lines(entries):
            output.write(f'{line}\n')
