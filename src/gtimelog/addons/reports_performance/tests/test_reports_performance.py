import datetime
import importlib
import io
import unittest

from gtimelog import component_registry
from gtimelog.addons import registry


def _h(hours):
    return datetime.timedelta(hours=hours)


class _FakeWindow:
    def __init__(self, work=None, slack=None):
        self._work = work or []
        self._slack = slack or []
        self.min_timestamp = datetime.datetime(2025, 1, 6, 0, 0)
        self.max_timestamp = datetime.datetime(2025, 1, 13, 0, 0)

    def grouped_entries(self, **kwargs):
        return self._work, self._slack

    def all_entries(self):
        return iter([('dummy',)])

    def set_of_all_tags(self):
        return set()


def _load_reports_class():
    registry.discover()
    importlib.import_module('gtimelog.addons.reports_performance.controllers.reports')
    return component_registry.get('reports')


class TestReportsPerformanceAddon(unittest.TestCase):
    def test_weekly_performance_report_includes_metrics_sections(self):
        reports_cls = _load_reports_class()
        window = _FakeWindow(
            work=[
                (None, 'ACME: [R1] Project Alpha / Delivery -> #101 API', _h(3)),
                (None, 'Internal workshop', _h(1)),
            ],
            slack=[(None, 'Break **', _h(0.5))],
        )

        report = reports_cls(window, email_headers=False, style='performance')
        out = io.StringIO()
        report.weekly_report(out, 'team@example.com', 'Alice')
        text = out.getvalue()

        assert 'PERFORMANCE SUMMARY' in text
        assert '- Billable:' in text
        assert '- Non-billable:' in text
        assert 'FOCUS AND EFFICIENCY' in text
        assert 'TOP 5 CLIENTS' in text
        assert 'ACME' in text

    def test_style_fallback_keeps_existing_plain_behavior(self):
        reports_cls = _load_reports_class()
        window = _FakeWindow(work=[(None, 'ACME: [R1] Project Alpha / Delivery -> #101 API', _h(1))])

        report = reports_cls(window, email_headers=False, style='plain')
        out = io.StringIO()
        report.weekly_report(out, 'team@example.com', 'Alice')
        text = out.getvalue()

        assert 'Total work done this week' in text
        assert 'PERFORMANCE SUMMARY' not in text

    def test_performance_metrics_service_classifies_billable_vs_non_billable(self):
        registry.discover()

        service_cls = component_registry.get('reports.performance.metrics')
        window = _FakeWindow(
            work=[
                (None, 'Client A: [R1] Build / Feature -> #1 Task', _h(2)),
                (None, 'Admin backlog grooming', _h(1)),
            ],
            slack=[(None, 'Break **', _h(0.5))],
        )

        metrics = service_cls().compute(window)

        assert metrics['billable'] == _h(2)
        assert metrics['non_billable'] == _h(1)
        assert metrics['total_slack'] == _h(0.5)
        assert metrics['active_clients'] == 1
        assert metrics['top_client_name'] == 'Client A'
