"""Doctest-based tests for the Reports controller."""

import datetime
import doctest
import os  # noqa: F401 -- used in doctests
import shutil  # noqa: F401 -- used in doctests
import sys  # noqa: F401 -- used in doctests
import tempfile  # noqa: F401 -- used in doctests
import textwrap
import unittest
from io import StringIO

import freezegun

from gtimelog.addons.base.tests.common import Checker, Mixins, make_time_window
from gtimelog.addons.reports.controllers.reports import Reports
from gtimelog.addons.reports.models.report_record import ReportRecord


def doctest_Reports_weekly_report_categorized():
    r"""Tests for Reports.weekly_report_categorized

    >>> from datetime import datetime

    >>> min = datetime(2010, 1, 25)
    >>> max = datetime(2010, 1, 31)

    >>> window = make_time_window(dt_min=min, dt_max=max)
    >>> reports = Reports(window)
    >>> reports.weekly_report_categorized(sys.stdout, 'foo@bar.com',
    ...                                   'Bob Jones')
    To: foo@bar.com
    Subject: Weekly report for Bob Jones (week 04)
    <BLANKLINE>
    No work done this week.

    >>> fh = StringIO(textwrap.dedent('''
    ...    2010-01-30 09:00: start **
    ...    2010-01-30 09:23: Bing: stuff
    ...    2010-01-30 12:54: Bong: other stuff
    ...    2010-01-30 13:32: lunch **
    ...    2010-01-30 23:46: misc: blah
    ... '''))

    >>> window = make_time_window(fh, min, max)
    >>> reports = Reports(window)
    >>> reports.weekly_report_categorized(sys.stdout, 'foo@bar.com',
    ...                                   'Bob Jones')
    To: foo@bar.com
    Subject: Weekly report for Bob Jones (week 04)
    <BLANKLINE>
                                                                    time
    Bing:
    <BLANKLINE>
      Stuff                                                           0:23
    ----------------------------------------------------------------------
                                                                      0:23
    <BLANKLINE>
    Bong:
    <BLANKLINE>
      Other stuff                                                     3:31
    ----------------------------------------------------------------------
                                                                      3:31
    <BLANKLINE>
    misc:
    <BLANKLINE>
      Blah                                                           10:14
    ----------------------------------------------------------------------
                                                                     10:14
    <BLANKLINE>
    Total work done this week: 14:08
    <BLANKLINE>
    Categories by time spent:
      misc            10:14
      Bong             3:31
      Bing             0:23

    """


def doctest_Reports_monthly_report_categorized():
    r"""Tests for Reports.monthly_report_categorized

    >>> from datetime import datetime, time

    >>> vm = time(2, 0)
    >>> min = datetime(2010, 1, 25)
    >>> max = datetime(2010, 1, 31)

    >>> window = make_time_window(dt_min=min, dt_max=max)
    >>> reports = Reports(window)
    >>> reports.monthly_report_categorized(sys.stdout, 'foo@bar.com',
    ...                                   'Bob Jones')
    To: foo@bar.com
    Subject: Monthly report for Bob Jones (2010/01)
    <BLANKLINE>
    No work done this month.

    >>> fh = StringIO(textwrap.dedent('''
    ...    2010-01-28 09:00: start
    ...    2010-01-28 09:23: give up ***
    ...
    ...    2010-01-30 09:00: start
    ...    2010-01-30 09:23: Bing: stuff
    ...    2010-01-30 12:54: Bong: other stuff
    ...    2010-01-30 13:32: lunch **
    ...    2010-01-30 23:46: misc
    ... '''))

    >>> window = make_time_window(fh, min, max, vm)
    >>> reports = Reports(window)
    >>> reports.monthly_report_categorized(sys.stdout, 'foo@bar.com',
    ...                                   'Bob Jones')
    To: foo@bar.com
    Subject: Monthly report for Bob Jones (2010/01)
    <BLANKLINE>
                                                                      time
    Bing:
      Stuff                                                           0:23
    ----------------------------------------------------------------------
                                                                      0:23
    <BLANKLINE>
    Bong:
      Other stuff                                                     3:31
    ----------------------------------------------------------------------
                                                                      3:31
    <BLANKLINE>
    No category:
      Misc                                                           10:14
    ----------------------------------------------------------------------
                                                                     10:14
    <BLANKLINE>
    Total work done this month: 14:08
    <BLANKLINE>
    Categories by time spent:
      No category     10:14
      Bong             3:31
      Bing             0:23

    """


def doctest_Reports_report_categories():
    r"""Tests for Reports._report_categories

    >>> from datetime import datetime, time, timedelta

    >>> vm = time(2, 0)
    >>> min = datetime(2010, 1, 25)
    >>> max = datetime(2010, 1, 31)

    >>> categories = {
    ...    'Bing': timedelta(2),
    ...    None: timedelta(1)}

    >>> window = make_time_window(StringIO(), min, max, vm)
    >>> reports = Reports(window)
    >>> reports._report_categories(sys.stdout, categories)
    <BLANKLINE>
    By category:
    <BLANKLINE>
    Bing                                                            48 hours
    (none)                                                          24 hours
    <BLANKLINE>

    """


def doctest_Reports_daily_report():
    r"""Tests for Reports.daily_report

    >>> from datetime import datetime, time

    >>> vm = time(2, 0)
    >>> min = datetime(2010, 1, 30)
    >>> max = datetime(2010, 1, 31)

    >>> window = make_time_window(StringIO(), min, max, vm)
    >>> reports = Reports(window)
    >>> reports.daily_report(sys.stdout, 'foo@bar.com', 'Bob Jones')
    To: foo@bar.com
    Subject: 2010-01-30 report for Bob Jones (Sat, week 04)
    <BLANKLINE>
    No work done today.

    >>> fh = StringIO('\n'.join([
    ...    '2010-01-30 09:00: start',
    ...    '2010-01-30 09:23: Bing: stuff',
    ...    '2010-01-30 12:54: Bong: other stuff',
    ...    '2010-01-30 13:32: lunch **',
    ...    '2010-01-30 15:46: misc',
    ...    '']))

    >>> window = make_time_window(fh, min, max, vm)
    >>> reports = Reports(window)
    >>> reports.daily_report(sys.stdout, 'foo@bar.com', 'Bob Jones')
    To: foo@bar.com
    Subject: 2010-01-30 report for Bob Jones (Sat, week 04)
    <BLANKLINE>
    Start at 09:00
    <BLANKLINE>
    Bing: stuff                                                     23 min
    Bong: other stuff                                               3 hours 31 min
    Misc                                                            2 hours 14 min
    <BLANKLINE>
    Total work done: 6 hours 8 min
    <BLANKLINE>
    By category:
    <BLANKLINE>
    Bing                                                            23 min
    Bong                                                            3 hours 31 min
    (none)                                                          2 hours 14 min
    <BLANKLINE>
    Slacking:
    <BLANKLINE>
    Lunch **                                                        38 min
    <BLANKLINE>
    Time spent slacking: 38 min

    """


def doctest_Reports_weekly_report_plain():
    r"""Tests for Reports.weekly_report_plain

    >>> from datetime import datetime, time

    >>> vm = time(2, 0)
    >>> min = datetime(2010, 1, 25)
    >>> max = datetime(2010, 1, 31)

    >>> window = make_time_window(StringIO(), min, max, vm)
    >>> reports = Reports(window)
    >>> reports.weekly_report_plain(sys.stdout, 'foo@bar.com', 'Bob Jones')
    To: foo@bar.com
    Subject: Weekly report for Bob Jones (week 04)
    <BLANKLINE>
    No work done this week.

    >>> fh = StringIO(textwrap.dedent('''
    ...    2010-01-28 09:00: start
    ...    2010-01-28 09:23: give up ***
    ...
    ...    2010-01-30 09:00: start
    ...    2010-01-30 09:23: Bing: stuff
    ...    2010-01-30 12:54: Bong: other stuff
    ...    2010-01-30 13:32: lunch **
    ...    2010-01-30 15:46: misc
    ... '''))

    >>> window = make_time_window(fh, min, max, vm)
    >>> reports = Reports(window)
    >>> reports.weekly_report_plain(sys.stdout, 'foo@bar.com', 'Bob Jones')
    To: foo@bar.com
    Subject: Weekly report for Bob Jones (week 04)
    <BLANKLINE>
                                                                    time
    Bing: stuff                                                     23 min
    Bong: other stuff                                               3 hours 31 min
    Misc                                                            2 hours 14 min
    <BLANKLINE>
    Total work done this week: 6 hours 8 min
    <BLANKLINE>
    By category:
    <BLANKLINE>
    Bing                                                            23 min
    Bong                                                            3 hours 31 min
    (none)                                                          2 hours 14 min
    <BLANKLINE>

    """


def doctest_Reports_monthly_report_plain():
    r"""Tests for Reports.monthly_report_plain

    >>> from datetime import datetime, time

    >>> vm = time(2, 0)
    >>> min = datetime(2007, 9, 1)
    >>> max = datetime(2007, 10, 1)

    >>> window = make_time_window(StringIO(), min, max, vm)
    >>> reports = Reports(window)
    >>> reports.monthly_report_plain(sys.stdout, 'foo@bar.com', 'Bob Jones')
    To: foo@bar.com
    Subject: Monthly report for Bob Jones (2007/09)
    <BLANKLINE>
    No work done this month.

    >>> fh = StringIO('\n'.join([
    ...    '2007-09-30 09:00: start',
    ...    '2007-09-30 09:23: Bing: stuff',
    ...    '2007-09-30 12:54: Bong: other stuff',
    ...    '2007-09-30 13:32: lunch **',
    ...    '2007-09-30 15:46: misc',
    ...    '']))

    >>> window = make_time_window(fh, min, max, vm)
    >>> reports = Reports(window)
    >>> reports.monthly_report_plain(sys.stdout, 'foo@bar.com', 'Bob Jones')
    To: foo@bar.com
    Subject: Monthly report for Bob Jones (2007/09)
    <BLANKLINE>
                                                                   time
    Bing: stuff                                                     23 min
    Bong: other stuff                                               3 hours 31 min
    Misc                                                            2 hours 14 min
    <BLANKLINE>
    Total work done this month: 6 hours 8 min
    <BLANKLINE>
    By category:
    <BLANKLINE>
    Bing                                                            23 min
    Bong                                                            3 hours 31 min
    (none)                                                          2 hours 14 min
    <BLANKLINE>

    """


def doctest_Reports_custom_range_report_categorized():
    r"""Tests for Reports.custom_range_report_categorized

    >>> from datetime import datetime, time

    >>> vm = time(2, 0)
    >>> min = datetime(2010, 1, 25)
    >>> max = datetime(2010, 2, 1)

    >>> window = make_time_window(StringIO(), min, max, vm)
    >>> reports = Reports(window)
    >>> reports.custom_range_report_categorized(sys.stdout, 'foo@bar.com',
    ...                                         'Bob Jones')
    To: foo@bar.com
    Subject: Custom date range report for Bob Jones (2010-01-25 - 2010-01-31)
    <BLANKLINE>
    No work done this custom range.

    >>> fh = StringIO('\n'.join([
    ...    '2010-01-20 09:00: arrived',
    ...    '2010-01-20 09:30: asdf',
    ...    '2010-01-20 10:00: Bar: Foo',
    ...    ''
    ...    '2010-01-30 09:00: arrived',
    ...    '2010-01-30 09:23: Bing: stuff',
    ...    '2010-01-30 12:54: Bong: other stuff',
    ...    '2010-01-30 13:32: lunch **',
    ...    '2010-01-30 23:46: misc',
    ...    '']))

    >>> window = make_time_window(fh, min, max, vm)
    >>> reports = Reports(window)
    >>> reports.custom_range_report_categorized(sys.stdout, 'foo@bar.com',
    ...                                         'Bob Jones')
    To: foo@bar.com
    Subject: Custom date range report for Bob Jones (2010-01-25 - 2010-01-31)
    <BLANKLINE>
                                                                      time
    Bing:
      Stuff                                                           0:23
    ----------------------------------------------------------------------
                                                                      0:23
    <BLANKLINE>
    Bong:
      Other stuff                                                     3:31
    ----------------------------------------------------------------------
                                                                      3:31
    <BLANKLINE>
    No category:
      Misc                                                           10:14
    ----------------------------------------------------------------------
                                                                     10:14
    <BLANKLINE>
    Total work done this custom range: 14:08
    <BLANKLINE>
    Categories by time spent:
      No category     10:14
      Bong             3:31
      Bing             0:23

    """


class TestTaggingReports(unittest.TestCase):
    """Tests for Reports._report_tags and tag inclusion in reports."""

    TEST_TIMELOG = textwrap.dedent("""
        2014-05-27 10:03: arrived
        2014-05-27 10:13: edx: introduce topic to new sysadmins -- edx
        2014-05-27 10:30: email
        2014-05-27 12:11: meeting: how to support new courses?  -- edx meeting
        2014-05-27 15:12: edx: write test procedure for EdX instances -- edx sysadmin
        2014-05-27 17:03: cluster: set-up accounts, etc. -- sysadmin hpc
        2014-05-27 17:14: support: how to run statistics on Hydra? -- support hydra
        2014-05-27 17:36: off: pause **
        2014-05-27 17:38: email
        2014-05-27 19:06: off: dinner & family **
        2014-05-27 22:19: cluster: fix shmmax-shmall issue -- sysadmin hpc
    """)

    def setUp(self):
        self.tw = make_time_window(
            StringIO(self.TEST_TIMELOG),
            datetime.datetime(2014, 5, 27, 9, 0),
            datetime.datetime(2014, 5, 27, 23, 59),
            datetime.time(2, 0),
        )

    def test_Reports__report_tags(self):
        rp = Reports(self.tw)
        txt = StringIO()
        # use same tags as in tests above, so we know the totals
        rp._report_tags(txt, ['meeting', 'hpc'])
        expected = (
            'Time spent in each area:\n'
            '\n'
            '  hpc          5:04\n'
            '  meeting      1:41\n'
            '\n'
            'Note that area totals may not add up to the period totals,\n'
            'as each entry may be belong to multiple areas (or none at all).'
        )
        assert txt.getvalue().strip() == expected

    def test_Reports_daily_report_includes_tags(self):
        rp = Reports(self.tw)
        txt = StringIO()
        rp.daily_report(txt, 'me@example.com', 'me')
        assert 'Time spent in each area' in txt.getvalue()

    def test_Reports_weekly_report_includes_tags(self):
        rp = Reports(self.tw)
        txt = StringIO()
        rp.weekly_report(txt, 'me@example.com', 'me')
        assert 'Time spent in each area' in txt.getvalue()

    def test_Reports_monthly_report_includes_tags(self):
        rp = Reports(self.tw)
        txt = StringIO()
        rp.monthly_report(txt, 'me@example.com', 'me')
        assert 'Time spent in each area' in txt.getvalue()

    def test_Reports_categorized_report_includes_tags(self):
        rp = Reports(self.tw, style='categorized')
        txt = StringIO()
        rp.weekly_report(txt, 'me@example.com', 'me')
        assert 'Time spent in each area' in txt.getvalue()
        txt = StringIO()
        rp.monthly_report(txt, 'me@example.com', 'me')
        assert 'Time spent in each area' in txt.getvalue()


class TestReportRecord(Mixins, unittest.TestCase):
    def setUp(self):
        self.filename = self.tempfile('sentreports.log')

    def load_fixture(self, lines):
        with open(self.filename, 'w') as f:
            for line in lines:
                f.write(line + '\n')

    def test_get_report_id(self):
        get_id = ReportRecord.get_report_id
        assert get_id(ReportRecord.WEEKLY, datetime.date(2016, 1, 1)) == '2015/53'

    @freezegun.freeze_time('2016-01-08 09:34:50')
    def test_record(self):
        rr = ReportRecord(self.filename)
        rr.record(rr.DAILY, datetime.date(2016, 1, 6), 'test@example.com')
        rr.record(rr.WEEKLY, datetime.date(2016, 1, 6), 'test@example.com')
        rr.record(rr.MONTHLY, datetime.date(2016, 1, 6), 'test@example.com')
        with open(self.filename) as f:
            written = f.read()
        assert written.splitlines() == [
            '2016-01-08 09:34:50,daily,2016-01-06,test@example.com',
            '2016-01-08 09:34:50,weekly,2016/1,test@example.com',
            '2016-01-08 09:34:50,monthly,2016-01,test@example.com',
        ]

    def test_get_recipients(self):
        self.load_fixture(
            [
                '2015-12-21 12:15:11,daily,2015-12-21,test@example.com',
                '2015-12-21 12:17:35,daily,2015-12-21,marius+test@example.com',
                '2015-12-21 12:18:21,daily,2015-12-21,marius+test@example.com',
                '2015-12-21 12:19:06,weekly,2015/46,marius+test@example.com',
                '2016-01-04 10:35:09,weekly,2015/53,activity@example.com',
                '2016-01-04 11:00:33,monthly,2015-12,activity@example.com',
                '2016-01-04 12:59:24,weekly,2015/49,activity@example.com',
                '2016-01-04 12:59:37,weekly,2015/52,activity@example.com',
            ]
        )
        rr = ReportRecord(self.filename)
        assert rr.get_recipients(rr.DAILY, datetime.date(2016, 1, 6)) == []
        assert rr.get_recipients(rr.DAILY, datetime.date(2015, 12, 21)) == [
            'test@example.com',
            'marius+test@example.com',
            'marius+test@example.com',
        ]
        assert rr.get_recipients(rr.WEEKLY, datetime.date(2015, 12, 21)) == ['activity@example.com']

    def test_reread_missing_file(self):
        rr = ReportRecord(self.filename)
        rr.reread()
        assert len(rr._records) == 0

    def test_reread_bad_records_are_ignored(self):
        self.load_fixture(
            [
                '2016-01-08 09:34:50,daily,2016-01-06,test@example.com',
                'Somebody might edit this file and corrupt it',
                '2016-01-08 09:34:50,monthly,2016-01,test@example.com',
            ]
        )
        rr = ReportRecord(self.filename)
        rr.reread()
        assert len(rr._records) == 2

    def test_record_then_load_when_empty(self):
        rr = ReportRecord(self.filename)
        now = datetime.datetime(2016, 1, 8, 9, 34, 50)
        rr.record(rr.DAILY, datetime.date(2016, 1, 6), 'test@example.com', now)
        assert rr.get_recipients(rr.DAILY, datetime.date(2016, 1, 6)) == ['test@example.com']

    def test_record_then_load_twice_when_empty(self):
        # Recording twice might not change the mtime because the resolution
        # is too low; so record() must update the internal data structures
        # by itself.
        rr = ReportRecord(self.filename)
        now = datetime.datetime(2016, 1, 8, 9, 34, 50)
        rr.record(rr.DAILY, datetime.date(2016, 1, 6), 'test@example.com', now)
        assert rr.get_recipients(rr.DAILY, datetime.date(2016, 1, 6)) == ['test@example.com']
        rr.record(rr.DAILY, datetime.date(2016, 1, 6), 'test@example.org', now)
        assert rr.get_recipients(rr.DAILY, datetime.date(2016, 1, 6)) == ['test@example.com', 'test@example.org']

    def test_record_then_load_when_nonempty(self):
        # Since we have lazy-loading, the "let's add the new record internally
        # and set last_mtime" optimization in record() might trick ReportRecord
        # into not loading an existing file at all.
        self.load_fixture(
            [
                '2016-01-08 09:34:50,daily,2016-01-06,test@example.com',
                '2016-01-08 09:34:50,weekly,2016/1,test@example.com',
                '2016-01-08 09:34:50,monthly,2016-01,test@example.com',
            ]
        )
        rr = ReportRecord(self.filename)
        now = datetime.datetime(2016, 1, 8, 9, 34, 50)
        rr.record(rr.DAILY, datetime.date(2016, 1, 6), 'test@example.org', now)
        assert rr.get_recipients(rr.DAILY, datetime.date(2016, 1, 6)) == ['test@example.com', 'test@example.org']

    def test_record_then_load_twice_when_nonempty(self):
        # I'm not sure what I'm protecting against with this test.  Probably
        # pure unnecessary paranoia.
        self.load_fixture(
            [
                '2016-01-08 09:34:50,daily,2016-01-06,test@example.com',
                '2016-01-08 09:34:50,weekly,2016/1,test@example.com',
                '2016-01-08 09:34:50,monthly,2016-01,test@example.com',
            ]
        )
        rr = ReportRecord(self.filename)
        now = datetime.datetime(2016, 1, 8, 9, 34, 50)
        rr.record(rr.DAILY, datetime.date(2016, 1, 6), 'test@example.org', now)
        rr.record(rr.DAILY, datetime.date(2016, 1, 6), 'test@example.net', now)
        assert rr.get_recipients(rr.DAILY, datetime.date(2016, 1, 6)) == [
            'test@example.com',
            'test@example.org',
            'test@example.net',
        ]

    def test_automatic_reload(self):
        rr = ReportRecord(self.filename)
        assert rr.get_recipients(rr.DAILY, datetime.date(2016, 1, 6)) == []
        self.load_fixture(
            [
                '2016-01-08 09:34:50,daily,2016-01-06,test@example.com',
                '2016-01-08 09:34:50,weekly,2016/1,test@example.com',
                '2016-01-08 09:34:50,monthly,2016-01,test@example.com',
            ]
        )
        assert rr.get_recipients(rr.DAILY, datetime.date(2016, 1, 6)) == ['test@example.com']


def additional_tests():
    return doctest.DocTestSuite(
        optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS,
        checker=Checker(),
    )
