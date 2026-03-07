import datetime
import textwrap
import unittest
from datetime import timedelta
from io import StringIO

import pytest

import gtimelog.addons.slack_distribution  # noqa: F401 — registers service extension
from gtimelog.addons.timelog.models import TimeLog


def make_time_window(file=None, min=None, max=None, vm=datetime.time(2)):
    if file is None:
        file = StringIO()
    return TimeLog(file, vm).window_for(min, max)


class TestSlackDistribution(unittest.TestCase):
    TEST_TIMELOG_WITH_SLACK = textwrap.dedent("""
        2026-02-16 09:00: start **
        2026-02-16 09:30: Task A
        2026-02-16 09:50: Task B
        2026-02-16 10:00: Task C
        2026-02-16 10:20: thinking ***
        2026-02-16 10:40: Task A
        2026-02-16 11:00: Task B
        2026-02-16 11:10: Task D
    """)

    TEST_TIMELOG_NO_SLACK = textwrap.dedent("""
        2026-02-16 09:00: start **
        2026-02-16 09:30: Task A
        2026-02-16 09:50: Task B
    """)

    TEST_TIMELOG_ONLY_SLACK = textwrap.dedent("""
        2026-02-16 09:00: start **
        2026-02-16 09:20: thinking ***
    """)

    TEST_TIMELOG_TWO_WEEKS = textwrap.dedent("""
        2026-02-16 09:00: start **
        2026-02-16 09:10: Week 8 Task A
        2026-02-16 09:20: pause ***
        2026-02-16 09:30: end **
        2026-02-23 09:00: start **
        2026-02-23 09:10: Week 9 Task B
        2026-02-23 09:20: pause ***
        2026-02-23 09:30: pause ***
        2026-02-23 09:40: pause ***
        2026-02-23 09:50: pause ***
        2026-02-23 10:00: end **
    """)

    def test_slack_distribution_equal(self):
        window = make_time_window(
            StringIO(self.TEST_TIMELOG_WITH_SLACK),
            datetime.datetime(2026, 2, 16, 0, 0),
            datetime.datetime(2026, 2, 17, 0, 0),
            datetime.time(2, 0),
        )
        work_entries, _slack_entries = window.grouped_entries(distribute_slack=True, proportional=False)
        work_dict = {name: duration for _, name, duration in work_entries}

        assert 'Task A' in work_dict
        assert 'Task B' in work_dict
        assert 'Task C' in work_dict
        assert 'Task D' in work_dict
        assert 'thinking ***' not in work_dict

        total_distributed = sum(d.total_seconds() for d in work_dict.values())
        total_raw_work = (30 + 20 + 10 + 20 + 20 + 10) * 60
        total_slack = 20 * 60
        assert total_distributed == pytest.approx(total_raw_work + total_slack, abs=1)

    def test_slack_distribution_proportional(self):
        window = make_time_window(
            StringIO(self.TEST_TIMELOG_WITH_SLACK),
            datetime.datetime(2026, 2, 16, 0, 0),
            datetime.datetime(2026, 2, 17, 0, 0),
            datetime.time(2, 0),
        )
        work_entries, _slack_entries = window.grouped_entries(distribute_slack=True, proportional=True)
        work_dict = {name: duration for _, name, duration in work_entries}

        assert 'Task A' in work_dict
        assert 'Task B' in work_dict
        assert 'Task C' in work_dict
        assert 'Task D' in work_dict
        assert 'thinking ***' not in work_dict

        total_distributed = sum(d.total_seconds() for d in work_dict.values())
        total_raw_work = (30 + 20 + 10 + 20 + 20 + 10) * 60
        total_slack = 20 * 60
        assert total_distributed == pytest.approx(total_raw_work + total_slack, abs=1)

        assert work_dict['Task A'].total_seconds() > work_dict['Task D'].total_seconds()

    def test_slack_distribution_no_slack(self):
        window = make_time_window(
            StringIO(self.TEST_TIMELOG_NO_SLACK),
            datetime.datetime(2026, 2, 16, 0, 0),
            datetime.datetime(2026, 2, 17, 0, 0),
            datetime.time(2, 0),
        )
        work_entries, _slack_entries = window.grouped_entries(distribute_slack=True, proportional=True)
        work_dict = {name: duration for _, name, duration in work_entries}

        assert 'Task A' in work_dict
        assert 'Task B' in work_dict
        assert work_dict['Task A'].total_seconds() == timedelta(minutes=30).total_seconds()
        assert work_dict['Task B'].total_seconds() == timedelta(minutes=20).total_seconds()

    def test_slack_distribution_no_work_entries(self):
        window = make_time_window(
            StringIO(self.TEST_TIMELOG_ONLY_SLACK),
            datetime.datetime(2026, 2, 16, 0, 0),
            datetime.datetime(2026, 2, 17, 0, 0),
            datetime.time(2, 0),
        )
        work_entries, _slack_entries = window.grouped_entries(distribute_slack=True, proportional=True)
        assert len(work_entries) == 0

    def test_no_distribution_by_default(self):
        """Without distribute_slack=True, *** entries are simply skipped."""
        window = make_time_window(
            StringIO(self.TEST_TIMELOG_WITH_SLACK),
            datetime.datetime(2026, 2, 16, 0, 0),
            datetime.datetime(2026, 2, 17, 0, 0),
            datetime.time(2, 0),
        )
        work_entries, _slack_entries = window.grouped_entries()
        work_dict = {name: duration for _, name, duration in work_entries}

        assert 'thinking ***' not in work_dict
        total_work = sum(d.total_seconds() for d in work_dict.values())
        expected = (30 + 20 + 10 + 20 + 20 + 10) * 60
        assert total_work == pytest.approx(expected, abs=1)

    def test_categorized_with_distribution(self):
        window = make_time_window(
            StringIO(self.TEST_TIMELOG_WITH_SLACK),
            datetime.datetime(2026, 2, 16, 0, 0),
            datetime.datetime(2026, 2, 17, 0, 0),
            datetime.time(2, 0),
        )
        _entries, totals = window.categorized_work_entries(distribute_slack=True, proportional=True)
        total_time = sum(t.total_seconds() for t in totals.values())
        expected = (30 + 20 + 10 + 20 + 20 + 10 + 20) * 60
        assert total_time == pytest.approx(expected, abs=1)

    def test_month_window_distribution_respects_week_boundaries_equal(self):
        window = make_time_window(
            StringIO(self.TEST_TIMELOG_TWO_WEEKS),
            datetime.datetime(2026, 2, 1, 0, 0),
            datetime.datetime(2026, 3, 1, 0, 0),
            datetime.time(2, 0),
        )

        work_entries, _slack_entries = window.grouped_entries(distribute_slack=True, proportional=False)
        work_dict = {name: duration for _start, name, duration in work_entries}

        assert work_dict['Week 8 Task A'].total_seconds() == pytest.approx(timedelta(minutes=20).total_seconds(), abs=1)
        assert work_dict['Week 9 Task B'].total_seconds() == pytest.approx(timedelta(minutes=50).total_seconds(), abs=1)

    def test_month_window_distribution_respects_week_boundaries_proportional(self):
        window = make_time_window(
            StringIO(self.TEST_TIMELOG_TWO_WEEKS),
            datetime.datetime(2026, 2, 1, 0, 0),
            datetime.datetime(2026, 3, 1, 0, 0),
            datetime.time(2, 0),
        )

        work_entries, _slack_entries = window.grouped_entries(distribute_slack=True, proportional=True)
        work_dict = {name: duration for _start, name, duration in work_entries}

        assert work_dict['Week 8 Task A'].total_seconds() == pytest.approx(timedelta(minutes=20).total_seconds(), abs=1)
        assert work_dict['Week 9 Task B'].total_seconds() == pytest.approx(timedelta(minutes=50).total_seconds(), abs=1)
