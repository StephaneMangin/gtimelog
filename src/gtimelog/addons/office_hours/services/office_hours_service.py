import datetime

from gtimelog.models import Service

DAY_NAME_TO_NUMBER = {
    'Monday': 1,
    'Tuesday': 2,
    'Wednesday': 3,
    'Thursday': 4,
    'Friday': 5,
    'Saturday': 6,
    'Sunday': 7,
}


class OfficeHoursService(Service):
    """Computes work-time status: time left, overtime, office presence."""

    _name = 'office_hours'

    DAY_NAME_TO_NUMBER = DAY_NAME_TO_NUMBER

    @staticmethod
    def time_left_at_work(hours_target, total_work, current_task_work_time):
        """Compute how much time is left until *hours_target* is reached."""
        total_time = total_work + current_task_work_time
        return datetime.timedelta(hours=hours_target) - total_time

    @staticmethod
    def estimated_week_overtime(
        office_hours,
        week_days_str,
        week_total_work,
        time_left,
    ):
        """Compute estimated overtime for the current week.

        Returns ``None`` if the computation cannot be done (e.g. no week
        days selected), otherwise a ``timedelta``.
        """
        hours = datetime.timedelta(hours=office_hours)
        current_week_day = datetime.datetime.now().isoweekday()

        selected_days = [d.strip() for d in week_days_str.split(',') if d.strip()]
        full_weekdays = sorted([DAY_NAME_TO_NUMBER[d] for d in selected_days if d in DAY_NAME_TO_NUMBER])

        if not full_weekdays:
            return None

        total_week_hours = len(full_weekdays) * hours
        worked_days = len([i for i in full_weekdays if i <= current_week_day])
        left_days = len(full_weekdays) - worked_days
        estimated_week_hours = (left_days * hours) + week_total_work + time_left
        return estimated_week_hours - total_week_hours

    @staticmethod
    def office_time_status(office_hours, total_slacking, total_work, current_task_time):
        """Compute office presence time vs target.

        Returns ``(total, overtime_or_left, is_overtime)`` tuple.
        """
        hours = datetime.timedelta(hours=office_hours)
        total = total_slacking + total_work + current_task_time
        if total > hours:
            return total, total - hours, True
        return total, hours - total, False
