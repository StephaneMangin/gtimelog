import datetime

from gtimelog.models import Service


class TimelogDomainPolicy(Service):
    """Domain policy for task entry and date navigation rules."""

    _name = 'domain.timelog.policy'

    ALLOWED_DETAIL_LEVELS = frozenset({'chronological', 'grouped', 'summary'})
    ALLOWED_TIME_RANGES = frozenset({'day', 'week', 'month'})

    @staticmethod
    def normalize_task_entry(raw_entry):
        """Normalize task input to a stripped unicode string."""
        entry = raw_entry
        if isinstance(entry, bytes):
            entry = entry.decode('UTF-8')
        return entry.strip()

    def is_add_entry_enabled(self, has_timelog, raw_entry):
        """Return True when add-entry action should be enabled."""
        return bool(has_timelog and self.normalize_task_entry(raw_entry))

    def validate_detail_level(self, value):
        """Validate detail-level domain value."""
        if value not in self.ALLOWED_DETAIL_LEVELS:
            raise ValueError(f'Invalid detail level: {value}')
        return value

    def validate_time_range(self, value):
        """Validate time-range domain value."""
        if value not in self.ALLOWED_TIME_RANGES:
            raise ValueError(f'Invalid time range: {value}')
        return value

    def previous_date(self, date, time_range):
        """Compute previous period date for the given time range."""
        self.validate_time_range(time_range)
        if time_range == 'day':
            return date - datetime.timedelta(1)
        if time_range == 'week':
            return date - datetime.timedelta(7)
        return self._prev_month(date)

    def next_date(self, date, time_range):
        """Compute next period date for the given time range."""
        self.validate_time_range(time_range)
        if time_range == 'day':
            return date + datetime.timedelta(1)
        if time_range == 'week':
            return date + datetime.timedelta(7)
        return self._next_month(date)

    @staticmethod
    def home_date():
        """Date value representing 'today' mode in UI."""
        return

    @staticmethod
    def _prev_month(date):
        if date.month == 1:
            return date.replace(year=date.year - 1, month=12)
        return date.replace(month=date.month - 1)

    @staticmethod
    def _next_month(date):
        if date.month == 12:
            return date.replace(year=date.year + 1, month=1)
        return date.replace(month=date.month + 1)
