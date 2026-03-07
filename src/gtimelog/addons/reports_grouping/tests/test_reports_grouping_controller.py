import datetime
import importlib
import io
import unittest

from gtimelog import component_registry


class _FakeWindow:
    def __init__(self, items=None, work=None):
        self._items = items or []
        self._work = work or []
        self.min_timestamp = datetime.datetime(2025, 1, 6, 0, 0)
        self.max_timestamp = datetime.datetime(2025, 1, 13, 0, 0)

    def all_entries(self):
        return iter(self._items)

    def grouped_entries(self, **kwargs):
        return self._work, []

    def set_of_all_tags(self):
        return set()


def _h(hours):
    return datetime.timedelta(hours=hours)


class TestReportsGroupingAddon(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reports_module = importlib.import_module('gtimelog.addons.reports.controllers.reports')
        grouping_module = importlib.import_module(
            'gtimelog.addons.reports_grouping.controllers.reports_grouping_controller'
        )
        if not component_registry.is_registered('reports'):
            importlib.reload(reports_module)
            importlib.reload(grouping_module)

    def test_weekly_plain_uses_grouped_summary(self):
        reports_cls = component_registry.get('reports')
        work = [(None, 'Client: [R1] Proj / Phase -> #1 Task', _h(2))]
        window = _FakeWindow(items=[('dummy',)], work=work)

        output = io.StringIO()
        reports_cls(window).weekly_report_plain(output, 'test@example.com', 'Test User')
        text = output.getvalue()

        assert 'SUMMARY OF TASKS BY CLIENTS' in text
        assert 'Total work done this week' in text

    def test_monthly_plain_uses_grouped_summary(self):
        reports_cls = component_registry.get('reports')
        work = [(None, 'Client: [R1] Proj / Phase -> #1 Task', _h(2))]
        window = _FakeWindow(items=[('dummy',)], work=work)

        output = io.StringIO()
        reports_cls(window).monthly_report_plain(output, 'test@example.com', 'Test User')
        text = output.getvalue()

        assert 'SUMMARY OF TASKS BY CLIENTS' in text
        assert 'Total work done this month' in text
