import datetime
import doctest
import textwrap
import unittest
from io import StringIO

from gtimelog.addons.base.tests.common import Checker, Mixins, make_time_window
from gtimelog.addons.timelog.models import TimeCollection


def doctest_TimeWindow_repr():
    """Test for TimeWindow.__repr__

    >>> from datetime import datetime, time
    >>> min = datetime(2013, 12, 3)
    >>> max = datetime(2013, 12, 4)
    >>> vm = time(2, 0)

    >>> make_time_window(dt_min=min, dt_max=max, vm=vm)
    <TimeWindow: 2013-12-03 00:00:00..2013-12-04 00:00:00>

    """


def doctest_TimeWindow_reread_no_file():
    """Test for TimeWindow.reread

        >>> window = make_time_window('/nosuchfile')

    There's no error.

        >>> len(window.items)
        0
        >>> window.last_time()

    """


def doctest_TimeWindow_reread_bad_timestamp():
    """Test for TimeWindow.reread

        >>> from datetime import datetime, time
        >>> min = datetime(2013, 12, 4)
        >>> max = datetime(2013, 12, 5)
        >>> vm = time(2, 0)

        >>> sampledata = StringIO('''
        ... 2013-12-04 09:00: start **
        ... # hey: this is not a timestamp
        ... 2013-12-04 09:14: gtimelog: write some tests
        ... ''')

        >>> window = make_time_window(sampledata, min, max, vm)

    There's no error, the line with a bad timestamp is silently skipped.

        >>> len(window.items)
        2

    """


def doctest_TimeWindow_reread_bad_ordering():
    """Test for TimeWindow.reread

        >>> from datetime import datetime
        >>> min = datetime(2013, 12, 4)
        >>> max = datetime(2013, 12, 5)

        >>> sampledata = StringIO('''
        ... 2013-12-04 09:00: start **
        ... 2013-12-04 09:14: gtimelog: write some tests
        ... 2013-12-04 09:10: gtimelog: whoops clock got all confused
        ... 2013-12-04 09:10: gtimelog: so this will need to be fixed
        ... ''')

        >>> window = make_time_window(sampledata, min, max)

    There's no error, the timestamps have been reordered, but note that
    order was preserved for events with the same timestamp

        >>> for t, e in window.items:
        ...     print("%s: %s" % (t.strftime('%H:%M'), e))
        09:00: start **
        09:10: gtimelog: whoops clock got all confused
        09:10: gtimelog: so this will need to be fixed
        09:14: gtimelog: write some tests

        >>> window.last_time()
        datetime.datetime(2013, 12, 4, 9, 14)

    """


def doctest_TimeWindow_count_days():
    """Test for TimeWindow.count_days

    >>> from datetime import datetime, time
    >>> min = datetime(2013, 12, 2)
    >>> max = datetime(2013, 12, 9)
    >>> vm = time(2, 0)

    >>> sampledata = StringIO('''
    ... 2013-12-04 09:00: start **
    ... 2013-12-04 09:14: gtimelog: write some tests
    ... 2013-12-04 09:10: gtimelog: whoops clock got all confused
    ... 2013-12-04 09:10: gtimelog: so this will need to be fixed
    ...
    ... 2013-12-05 22:30: some fictional late night work **
    ... 2013-12-06 00:30: frobnicate the widgets
    ...
    ... 2013-12-08 09:00: work **
    ... 2013-12-08 09:01: and stuff
    ... ''')

    >>> window = make_time_window(sampledata, min, max, vm)
    >>> window.count_days()
    3

    """


def doctest_TimeWindow_last_entry():
    """Test for TimeWindow.last_entry

        >>> from datetime import datetime
        >>> window = make_time_window()

    Case #1: no items

        >>> window.items = []
        >>> window.last_entry()

    Case #2: single item

        >>> window.items = [
        ...     (datetime(2013, 12, 4, 9, 0), 'started **'),
        ... ]
        >>> start, stop, duration, tags, entry = window.last_entry()
        >>> start == stop == datetime(2013, 12, 4, 9, 0)
        True
        >>> duration
        datetime.timedelta(0)
        >>> entry
        'started **'

    Case #3: single item at start of new day

        >>> window.items = [
        ...     (datetime(2013, 12, 3, 12, 0), 'stuff'),
        ...     (datetime(2013, 12, 4, 9, 0), 'started **'),
        ... ]
        >>> start, stop, duration, tags, entry = window.last_entry()
        >>> start == stop == datetime(2013, 12, 4, 9, 0)
        True
        >>> duration
        datetime.timedelta(0)
        >>> entry
        'started **'


    Case #4: several items

        >>> window.items = [
        ...     (datetime(2013, 12, 4, 9, 0), 'started **'),
        ...     (datetime(2013, 12, 4, 9, 31), 'gtimelog: tests'),
        ... ]
        >>> start, stop, duration, tags, entry = window.last_entry()
        >>> start
        datetime.datetime(2013, 12, 4, 9, 0)
        >>> stop
        datetime.datetime(2013, 12, 4, 9, 31)
        >>> duration
        datetime.timedelta(seconds=1860)
        >>> entry
        'gtimelog: tests'

    """


class TestTimeCollection(Mixins, unittest.TestCase):
    def test_split_category(self):
        sp = TimeCollection.split_category
        assert sp('some task') == (None, 'some task')
        assert sp('project: some task') == ('project', 'some task')
        assert sp('project: some task: etc') == ('project', 'some task: etc')

    def test_split_category_no_task_just_category(self):
        # Regression test for https://github.com/gtimelog/gtimelog/issues/117
        sp = TimeCollection.split_category
        assert sp('project: ') == ('project', '')
        assert sp('project:') == ('project', '')


class TestTotals(unittest.TestCase):
    TEST_TIMELOG = textwrap.dedent(
        """
        2018-12-09 08:30: start at home
        2018-12-09 08:40: emails
        2018-12-09 09:10: travel to work ***
        2018-12-09 09:15: coffee **
        2018-12-09 12:15: coding
        """
    )

    def setUp(self):
        self.tw = make_time_window(
            StringIO(self.TEST_TIMELOG),
            datetime.datetime(2018, 12, 9, 8, 0),
            datetime.datetime(2018, 12, 9, 23, 59),
            datetime.time(2, 0),
        )

    def test_TimeWindow_totals(self):
        work, slack = self.tw.totals()
        assert work == datetime.timedelta(hours=3, minutes=10)
        assert slack == datetime.timedelta(hours=0, minutes=5)


class TestFiltering(unittest.TestCase):
    TEST_TIMELOG = textwrap.dedent("""
        2014-05-27 10:03: arrived
        2014-05-27 10:13: edx: introduce topic to new sysadmins
        2014-05-27 10:30: email
        2014-05-27 12:11: meeting: how to support new courses?
        2014-05-27 15:12: edx: write test procedure for EdX instances
        2014-05-27 17:03: cluster: set-up accounts, etc.
        2014-05-27 17:14: support: how to run statistics on Hydra?
        2014-05-27 17:36: off: pause **
        2014-05-27 17:38: email
        2014-05-27 19:06: off: dinner & family **
        2014-05-27 22:19: cluster: fix shmmax-shmall issue
        """)

    def setUp(self):
        self.tw = make_time_window(
            StringIO(self.TEST_TIMELOG),
            datetime.datetime(2014, 5, 27, 9, 0),
            datetime.datetime(2014, 5, 27, 23, 59),
            datetime.time(2, 0),
        )

    def test_TimeWindow_totals_filtering1(self):
        work, slack = self.tw.totals(filter_text='support')
        # matches two items: 1h 41m (10:30--12:11) + 11m (17:03--17:14)
        assert work == datetime.timedelta(hours=1, minutes=52)
        assert slack == datetime.timedelta(0)

    def test_TimeWindow_totals_filtering2(self):
        work, slack = self.tw.totals(filter_text='f')
        # matches four items:
        # 3h  1m (12:11--15:12) edx: write test procedure [f]or EdX instances
        # 3h 13m (19:06--22:19) cluster: [f]ix shmmax-shmall issue
        # total work: 6h 14m
        #    22m (17:14--17:36) o[f]f: pause **
        # 1h 28m (17:38--19:06) o[f]f: dinner & family **
        # total slacking: 1h 50m
        assert work == datetime.timedelta(hours=6, minutes=14)
        assert slack == datetime.timedelta(hours=1, minutes=50)


class TestTagging(unittest.TestCase):
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

    def test_TimeWindow_set_of_all_tags(self):
        tags = self.tw.set_of_all_tags()
        assert tags == {'edx', 'hpc', 'hydra', 'meeting', 'support', 'sysadmin'}

    def test_TimeWindow_totals_per_tag1(self):
        """Test aggregate time per tag, 1 entry only"""
        result = self.tw.totals('meeting')
        assert len(result) == 2
        work, slack = result
        assert work == (datetime.timedelta(hours=12, minutes=11) - datetime.timedelta(hours=10, minutes=30))
        assert slack == datetime.timedelta(0)

    def test_TimeWindow_totals_per_tag2(self):
        """Test aggregate time per tag, several entries"""
        result = self.tw.totals('hpc')
        assert len(result) == 2
        work, slack = result
        assert work == (
            (datetime.timedelta(hours=17, minutes=3) - datetime.timedelta(hours=15, minutes=12))
            + (datetime.timedelta(hours=22, minutes=19) - datetime.timedelta(hours=19, minutes=6))
        )
        assert slack == datetime.timedelta(0)

    def test_TimeWindow__split_entry_and_tags1(self):
        """Test `TimeWindow._split_entry_and_tags` with simple entry"""
        result = self.tw._split_entry_and_tags('email')
        assert len(result) == 2
        assert result[0] == 'email'
        assert result[1] == set()

    def test_TimeWindow__split_entry_and_tags2(self):
        """Test `TimeWindow._split_entry_and_tags` with simple entry and tags"""
        result = self.tw._split_entry_and_tags('restart CFEngine server -- sysadmin cfengine issue327')
        assert len(result) == 2
        assert result[0] == 'restart CFEngine server'
        assert result[1] == {'sysadmin', 'cfengine', 'issue327'}

    def test_TimeWindow__split_entry_and_tags3(self):
        """Test `TimeWindow._split_entry_and_tags` with category, entry, and tags"""
        result = self.tw._split_entry_and_tags('tooling: tagging support in gtimelog -- tooling gtimelog')
        assert len(result) == 2
        assert result[0] == 'tooling: tagging support in gtimelog'
        assert result[1] == {'tooling', 'gtimelog'}

    def test_TimeWindow__split_entry_and_tags4(self):
        """Test `TimeWindow._split_entry_and_tags` with slack-type entry"""
        result = self.tw._split_entry_and_tags('read news -- reading **')
        assert len(result) == 2
        assert result[0] == 'read news **'
        assert result[1] == {'reading'}

    def test_TimeWindow__split_entry_and_tags5(self):
        """Test `TimeWindow._split_entry_and_tags` with slack-type entry"""
        result = self.tw._split_entry_and_tags('read news -- reading ***')
        assert len(result) == 2
        assert result[0] == 'read news ***'
        assert result[1] == {'reading'}


def additional_tests():
    return doctest.DocTestSuite(
        optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS,
        checker=Checker(),
    )
