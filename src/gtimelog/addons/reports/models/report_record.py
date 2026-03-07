import datetime
from collections import defaultdict

from gtimelog.addons.base.models.time_utils import get_mtime
from gtimelog.models import Model


class ReportRecord(Model):
    """A record of sent reports."""

    _name = 'report.record'
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'

    def __init__(self, filename):
        self.filename = filename
        self.last_mtime = None
        self._records = defaultdict(list)

    @classmethod
    def get_report_id(cls, report_kind, date):
        if report_kind == cls.DAILY:
            return date.strftime('%Y-%m-%d')
        if report_kind == cls.WEEKLY:
            return '{}/{}'.format(*date.isocalendar()[:2])
        if report_kind == cls.MONTHLY:
            return date.strftime('%Y-%m')
        raise AssertionError(f'Bug: unexpected report kind: {report_kind!r}')

    def record(self, report_kind, report_date, recipient, now=None):
        if report_kind not in (self.DAILY, self.WEEKLY, self.MONTHLY):
            raise ValueError(f'Invalid report kind: {report_kind!r}')
        if not isinstance(report_date, datetime.date):
            raise TypeError(f'report_date must be a date, got {type(report_date)}')
        if now is None:
            now = datetime.datetime.now()
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        report_id = self.get_report_id(report_kind, report_date)
        with open(self.filename, 'a') as f:
            f.write(f'{timestamp},{report_kind},{report_id},{recipient}\n')
        if self.last_mtime is not None:
            self.last_mtime = get_mtime(self.filename)
            self._records[report_kind, report_id].append(recipient)

    def check_reload(self):
        mtime = get_mtime(self.filename)
        if mtime != self.last_mtime:
            self.reread()

    def reread(self):
        self.last_mtime = get_mtime(self.filename)
        self._records.clear()
        try:
            with open(self.filename) as f:
                for line in f:
                    try:
                        _timestamp, report_kind, report_id, recipient = line.split(',', 3)
                    except ValueError:
                        continue
                    self._records[report_kind, report_id].append(recipient.strip())
        except OSError:
            pass

    def get_recipients(self, report_kind, report_date):
        self.check_reload()
        report_id = self.get_report_id(report_kind, report_date)
        return self._records.get((report_kind, report_id), [])
