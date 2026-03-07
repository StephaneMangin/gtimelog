import datetime
from gettext import gettext as _

from gtimelog.addons.base.helpers import format_duration
from gtimelog.models import component_registry


class OfficeHoursFooterController:
    """OOP controller for office-hours footer behavior."""

    def render_extended_footer(self, log_view, total_work, total_slacking):
        if not (log_view.showing_today and log_view.time_range == 'day'):
            return

        office_hours_svc = component_registry.get('office_hours')

        if log_view.expected_work_hours:
            current_task_work_time = self._get_current_task_work_time(log_view)
            log_view.w('\n')
            time_left = office_hours_svc.time_left_at_work(
                log_view.expected_work_hours,
                total_work,
                current_task_work_time,
            )
            time_to_leave = log_view.now + time_left
            if time_left < datetime.timedelta(0):
                fmt = _("Time left at work: {0} (should've finished at {1:%H:%M}, overtime of {2} until now)")
                real_time_left = datetime.timedelta(0)
                log_view.wfmt(
                    fmt,
                    (format_duration(real_time_left), 'duration'),
                    (time_to_leave, 'time'),
                    (format_duration(-time_left), 'duration'),
                )
            else:
                fmt = _('Time left at work: {0} (till {1:%H:%M})')
                log_view.wfmt(
                    fmt,
                    (format_duration(time_left), 'duration'),
                    (time_to_leave, 'time'),
                )
            if log_view.expected_workdays:
                log_view.w('\n')
                weekly_window = log_view.timelog.window_for_week(log_view.date)
                week_total_work, _slack = weekly_window.totals()
                overtime = office_hours_svc.estimated_week_overtime(
                    log_view.expected_presence_hours,
                    log_view.expected_workdays,
                    week_total_work,
                    time_left,
                )
                if overtime is not None:
                    log_view.wfmt(
                        _('Estimated week overtime: {0}'),
                        (format_duration(overtime), 'duration'),
                    )

        if log_view.expected_presence_hours:
            current_task_time = self._get_current_task_time(log_view)
            log_view.w('\n')
            total, delta, is_overtime = office_hours_svc.office_time_status(
                log_view.expected_presence_hours,
                total_slacking,
                total_work,
                current_task_time,
            )
            if is_overtime:
                log_view.wfmt(
                    _('At office today: {0} ({1} overtime)'),
                    (format_duration(total), 'duration'),
                    (format_duration(delta), 'duration'),
                )
            else:
                log_view.wfmt(
                    _('At office today: {0} ({1} left)'),
                    (format_duration(total), 'duration'),
                    (format_duration(delta), 'duration'),
                )

    @staticmethod
    def setup_footer_observers(log_view):
        """Attach office-hours related notify observers to the log view."""
        log_view.connect('notify::expected-work-hours', log_view.queue_footer_update)
        log_view.connect('notify::expected-presence-hours', log_view.queue_footer_update)
        log_view.connect('notify::expected-workdays', log_view.queue_footer_update)

    @staticmethod
    def _get_current_task_time(log_view):
        last_time = log_view.get_last_time()
        if last_time is None:
            return datetime.timedelta(0)
        return log_view.now - last_time

    def _get_current_task_work_time(self, log_view):
        if '**' in (log_view.current_task or ''):
            return datetime.timedelta(0)
        return self._get_current_task_time(log_view)


_FOOTER_CONTROLLER = OfficeHoursFooterController()


def render_extended_footer(log_view, total_work, total_slacking):
    _FOOTER_CONTROLLER.render_extended_footer(log_view, total_work, total_slacking)


def setup_footer_observers(log_view):
    _FOOTER_CONTROLLER.setup_footer_observers(log_view)
