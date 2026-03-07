import datetime
import io
import unittest

from gtimelog.addons.reports.controllers.reports import Reports


class _FakeWindow:
    """Minimal mock for a time window used by Reports."""

    def __init__(self, items=None, work=None, slack=None, categorized_entries=None, categorized_totals=None):
        self._items = items or []
        self._work = work or []
        self._slack = slack or []
        self._categorized_entries = categorized_entries or {}
        self._categorized_totals = categorized_totals or {}
        self._grouped_entries_calls = []
        self._categorized_calls = []
        self.min_timestamp = datetime.datetime(2025, 1, 6, 0, 0)
        self.max_timestamp = datetime.datetime(2025, 1, 13, 0, 0)

    def all_entries(self):
        return iter(self._items)

    def grouped_entries(self, **kwargs):
        self._grouped_entries_calls.append(kwargs)
        return self._work, self._slack

    def totals(self, **kwargs):
        work = sum((d for _, _, d in self._work), datetime.timedelta(0))
        slack = sum((d for _, _, d in self._slack), datetime.timedelta(0))
        return work, slack

    def categorized_work_entries(self, **kwargs):
        self._categorized_calls.append(kwargs)
        return self._categorized_entries, self._categorized_totals

    def set_of_all_tags(self):
        return set()

    def count_days(self):
        return 1


def _h(hours):
    return datetime.timedelta(hours=hours)


class TestWeeklyReportPlain(unittest.TestCase):
    def test_no_work(self):
        window = _FakeWindow()
        r = Reports(window)
        out = io.StringIO()
        r.weekly_report_plain(out, 'test@example.com', 'Test User')
        text = out.getvalue()
        assert 'Weekly report for Test User' in text
        assert 'No work done this week' in text

    def test_with_entries(self):
        work = [(None, 'Client: task', _h(2))]
        window = _FakeWindow(items=[('dummy',)], work=work)
        r = Reports(window)
        out = io.StringIO()
        r.weekly_report_plain(out, 'test@example.com', 'Test User')
        text = out.getvalue()
        assert 'Weekly report' in text
        assert 'Client: task' in text
        assert 'By category:' in text
        assert 'Total work done this week' in text


class TestMonthlyReportPlain(unittest.TestCase):
    def test_with_entries(self):
        work = [(None, 'Client: task', _h(2))]
        window = _FakeWindow(items=[('dummy',)], work=work)
        r = Reports(window)
        out = io.StringIO()
        r.monthly_report_plain(out, 'test@example.com', 'Test User')
        text = out.getvalue()
        assert 'Monthly report' in text
        assert 'Client: task' in text
        assert 'By category:' in text
        assert 'Total work done this month' in text


class TestDistributionPropagation(unittest.TestCase):
    def test_plain_report_passes_distribution_kwargs(self):
        work = [(None, 'Client: Project / Phase -> #1 Task', _h(2))]
        window = _FakeWindow(items=[('dummy',)], work=work)
        report = Reports(window)
        report.distribute_slack = True
        report.proportional = False

        out = io.StringIO()
        report.weekly_report_plain(out, 'test@example.com', 'Test User')

        assert window._grouped_entries_calls
        assert all(call.get('distribute_slack') is True for call in window._grouped_entries_calls)
        assert all(call.get('proportional') is False for call in window._grouped_entries_calls)

    def test_categorized_report_total_uses_distributed_categories(self):
        categorized_entries = {'Delivery': [(None, 'Task', _h(2))]}
        categorized_totals = {'Delivery': _h(2)}
        window = _FakeWindow(
            items=[('dummy',)],
            work=[(None, 'Task', _h(1))],
            categorized_entries=categorized_entries,
            categorized_totals=categorized_totals,
        )
        report = Reports(window, email_headers=False, style='categorized')
        report.distribute_slack = True
        report.proportional = True

        out = io.StringIO()
        report.weekly_report_categorized(out, 'test@example.com', 'Test User')
        text = out.getvalue()

        assert window._categorized_calls
        assert window._categorized_calls[-1].get('distribute_slack') is True
        assert window._categorized_calls[-1].get('proportional') is True
        assert 'Total work done this week: 2:00' in text

    def test_daily_report_passes_distribution_kwargs(self):
        items = [
            (
                datetime.datetime(2025, 1, 6, 9, 0),
                datetime.datetime(2025, 1, 6, 10, 0),
                datetime.timedelta(hours=1),
                set(),
                'Client: Project / Phase -> #1 Task',
            )
        ]
        work = [(None, 'Client: Project / Phase -> #1 Task', _h(1))]
        slack = [(None, 'Break **', _h(0.5))]
        window = _FakeWindow(items=items, work=work, slack=slack)
        report = Reports(window, email_headers=False)
        report.distribute_slack = True
        report.proportional = False

        out = io.StringIO()
        report.daily_report(out, 'test@example.com', 'Test User')

        assert window._grouped_entries_calls
        assert window._grouped_entries_calls[-1].get('distribute_slack') is True
        assert window._grouped_entries_calls[-1].get('proportional') is False


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
