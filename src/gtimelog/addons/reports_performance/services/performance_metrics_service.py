import datetime
from collections.abc import Iterable

from gtimelog.models import Service


class PerformanceMetricsService(Service):
    """Compute performance metrics from grouped report entries."""

    _name = 'reports.performance.metrics'

    def _sum_durations(self, rows: Iterable[tuple]) -> datetime.timedelta:
        return sum((duration for _start, _entry, duration in rows), datetime.timedelta(0))

    @staticmethod
    def _ratio(numerator: datetime.timedelta, denominator: datetime.timedelta) -> float:
        if denominator <= datetime.timedelta(0):
            return 0.0
        return numerator.total_seconds() / denominator.total_seconds()

    def compute(self, window, distribute_slack=False, proportional=True):
        app_reports_service = self.env.get('application.reports.service')
        work_entries, slack_entries = window.grouped_entries(
            distribute_slack=distribute_slack,
            proportional=proportional,
        )

        total_work = self._sum_durations(work_entries)
        total_slack = self._sum_durations(slack_entries)
        observed_total = total_work + total_slack

        billable = datetime.timedelta(0)
        non_billable = datetime.timedelta(0)
        billable_entries_count = 0
        client_totals: dict[str, datetime.timedelta] = {}

        for _start, entry, duration in work_entries:
            if duration <= datetime.timedelta(0):
                continue
            parsed = app_reports_service.parse_entry_line(entry)
            customer = (parsed.get('customer') or '').strip()
            if customer:
                billable += duration
                billable_entries_count += 1
                client_totals[customer] = client_totals.get(customer, datetime.timedelta(0)) + duration
            else:
                non_billable += duration

        if non_billable == datetime.timedelta(0) and total_work > billable:
            # Keep invariants stable if parsing/classification evolves.
            non_billable = total_work - billable

        top_clients = sorted(client_totals.items(), key=lambda item: item[1], reverse=True)
        top_client_name = top_clients[0][0] if top_clients else None
        top_client_duration = top_clients[0][1] if top_clients else datetime.timedelta(0)

        return {
            'total_work': total_work,
            'total_slack': total_slack,
            'observed_total': observed_total,
            'billable': billable,
            'non_billable': non_billable,
            'billable_rate': self._ratio(billable, total_work),
            'non_billable_rate': self._ratio(non_billable, total_work),
            'slack_rate': self._ratio(total_slack, observed_total),
            'productive_utilization_rate': self._ratio(billable, observed_total),
            'active_clients': len(client_totals),
            'active_tasks': len(work_entries),
            'billable_entries_count': billable_entries_count,
            'avg_billable_session': (
                datetime.timedelta(0)
                if billable_entries_count == 0
                else datetime.timedelta(seconds=billable.total_seconds() / billable_entries_count)
            ),
            'top_client_name': top_client_name,
            'top_client_duration': top_client_duration,
            'top_client_share': self._ratio(top_client_duration, billable),
            'top_clients': top_clients[:5],
        }
