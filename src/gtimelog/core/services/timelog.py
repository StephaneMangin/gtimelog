import datetime

from gtimelog.models import Service, component_registry


class TimelogApplicationService(Service):
    """Application service for timelog-related use-cases."""

    _name = 'application.timelog.service'

    def __init__(self, domain_policy=None):
        self.domain_policy = domain_policy or component_registry.get('domain.timelog.policy')()

    def prepare_entry_for_append(self, raw_entry, parse_correction):
        """Prepare user input for append by normalizing and parsing correction syntax."""
        entry = self.domain_policy.normalize_task_entry(raw_entry)
        return parse_correction(entry)

    @staticmethod
    def should_reset_date_after_append(showing_today):
        """Return True when appending should force UI back to today."""
        return not showing_today

    def previous_date(self, current_date, time_range):
        """Compute previous period date."""
        return self.domain_policy.previous_date(current_date, time_range)

    def next_date(self, current_date, time_range):
        """Compute next period date."""
        return self.domain_policy.next_date(current_date, time_range)

    def home_date(self):
        """Return date representing 'today' mode in UI."""
        return self.domain_policy.home_date()

    @staticmethod
    def get_virtual_midnight(gsettings):
        """Read virtual-midnight tuple from settings and return a time object."""
        hour, minute = gsettings.get_value('virtual-midnight')
        return datetime.time(hour, minute)

    @staticmethod
    def get_rounding_time(gsettings):
        """Read rounding time in minutes from settings."""
        return gsettings.get_int('rounding-time')

    @staticmethod
    def get_rounding_time_force_above(gsettings):
        """Read force-above rounding behavior from settings."""
        return gsettings.get_boolean('rounding-time-force-above')

    def build_timelog(self, gsettings, timelog_file, timelog_cls):
        """Build a timelog model instance from current settings."""
        return timelog_cls(
            timelog_file,
            self.get_virtual_midnight(gsettings),
            self.get_rounding_time(gsettings),
            self.get_rounding_time_force_above(gsettings),
        )
