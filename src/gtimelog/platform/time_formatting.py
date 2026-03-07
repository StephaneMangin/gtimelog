from gtimelog.models import Service


class DurationFormatter(Service):
    """Format durations in short and long textual forms."""

    _name = 'platform.duration.formatter'

    @staticmethod
    def format_duration_short(duration):
        """Format duration as H:MM."""
        hours, minutes = divmod((duration.days * 24 * 60 + duration.seconds // 60), 60)
        return f'{hours}:{minutes:02d}'

    @staticmethod
    def format_duration_long(duration):
        """Format duration as human-readable long string."""
        hours, minutes = divmod((duration.days * 24 * 60 + duration.seconds // 60), 60)
        if hours and minutes:
            return f'{hours} hour{"s" if hours != 1 else ""} {minutes} min'
        if hours:
            return f'{hours} hour{"s" if hours != 1 else ""}'
        return f'{minutes} min'
