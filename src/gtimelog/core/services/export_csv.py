import datetime

from gtimelog.models import Service


class CsvExportApplicationService(Service):
    """Application service for CSV export data preparation."""

    _name = 'application.export.csv.service'

    @staticmethod
    def to_csv_complete_rows(grouped_work_entries):
        """Build sorted rows (task, minutes) from grouped work entries."""
        rows = [
            (entry, CsvExportApplicationService._as_minutes(duration))
            for _start, entry, duration in grouped_work_entries
            if duration
        ]
        rows.sort()
        return rows

    @staticmethod
    def to_csv_daily_rows(all_entries):
        """Build daily rows (date, day-start, slacking, work) from all entries."""
        zero = datetime.timedelta(0)
        days = {}
        first_day = None
        last_day = None

        for start, _stop, duration, _tags, entry in all_entries:
            if first_day is None:
                first_day = start.date()
            last_day = start.date()
            day = days.setdefault(
                start.date(),
                [datetime.timedelta(minutes=start.minute, hours=start.hour), zero, zero],
            )
            if '**' in entry:
                day[1] += duration
            else:
                day[2] += duration

        if first_day and last_day:
            current_day = first_day
            while current_day <= last_day:
                days.setdefault(current_day, [zero, zero, zero])
                current_day += datetime.timedelta(days=1)

        return sorted(
            (
                day,
                CsvExportApplicationService._as_hours(start),
                CsvExportApplicationService._as_hours(slacking),
                CsvExportApplicationService._as_hours(work),
            )
            for day, (start, slacking, work) in days.items()
        )

    @staticmethod
    def _as_minutes(duration):
        return duration.days * 24 * 60 + duration.seconds // 60

    @staticmethod
    def _as_hours(duration):
        return duration.days * 24.0 + duration.seconds / (60.0 * 60.0)
