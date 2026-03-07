import doctest

from gtimelog.addons.base.tests.common import Checker


def doctest_as_hours():
    """Tests for as_hours

    >>> from gtimelog.addons.base.models.time_utils import as_hours
    >>> from datetime import timedelta
    >>> as_hours(timedelta(0))
    0.0
    >>> as_hours(timedelta(minutes=30))
    0.5
    >>> as_hours(timedelta(minutes=60))
    1.0
    >>> as_hours(timedelta(days=2))
    48.0

    """


def doctest_format_duration():
    """Tests for format_duration.

    >>> from gtimelog.addons.base.models.time_utils import format_duration
    >>> from datetime import timedelta
    >>> format_duration(timedelta(0))
    '0 h 0 min'
    >>> format_duration(timedelta(minutes=1))
    '0 h 1 min'
    >>> format_duration(timedelta(minutes=60))
    '1 h 0 min'

    """


def doctest_format_short():
    """Tests for format_duration_short.

    >>> from gtimelog.addons.base.models.time_utils import format_duration_short
    >>> from datetime import timedelta
    >>> format_duration_short(timedelta(0))
    '0:00'
    >>> format_duration_short(timedelta(minutes=1))
    '0:01'
    >>> format_duration_short(timedelta(minutes=59))
    '0:59'
    >>> format_duration_short(timedelta(minutes=60))
    '1:00'
    >>> format_duration_short(timedelta(days=1, hours=2, minutes=3))
    '26:03'

    """


def doctest_format_duration_long():
    """Tests for format_duration_long.

    >>> from gtimelog.addons.base.models.time_utils import format_duration_long
    >>> from datetime import timedelta
    >>> format_duration_long(timedelta(0))
    '0 min'
    >>> format_duration_long(timedelta(minutes=1))
    '1 min'
    >>> format_duration_long(timedelta(minutes=60))
    '1 hour'
    >>> format_duration_long(timedelta(minutes=65))
    '1 hour 5 min'
    >>> format_duration_long(timedelta(hours=2))
    '2 hours'
    >>> format_duration_long(timedelta(hours=2, minutes=1))
    '2 hours 1 min'

    """


def doctest_parse_datetime():
    """Tests for parse_datetime

    >>> from gtimelog.addons.base.models.time_utils import parse_datetime
    >>> parse_datetime('2005-02-03 02:13')
    datetime.datetime(2005, 2, 3, 2, 13)
    >>> parse_datetime('xyzzy')
    Traceback (most recent call last):
      ...
    ValueError: bad date time: 'xyzzy'
    >>> parse_datetime('YYYY-MM-DD HH:MM')
    Traceback (most recent call last):
      ...
    ValueError: bad date time: 'YYYY-MM-DD HH:MM'

    """


def doctest_parse_time():
    """Tests for parse_time

    >>> from gtimelog.addons.base.models.time_utils import parse_time
    >>> parse_time('02:13')
    datetime.time(2, 13)
    >>> parse_time('xyzzy')
    Traceback (most recent call last):
      ...
    ValueError: bad time: 'xyzzy'

    """


def doctest_virtual_day():
    """Tests for virtual_day

        >>> from datetime import datetime, time
        >>> from gtimelog.addons.base.models.time_utils import virtual_day

    Virtual midnight

        >>> vm = time(2, 0)

    The tests themselves:

        >>> virtual_day(datetime(2005, 2, 3, 1, 15), vm)
        datetime.date(2005, 2, 2)
        >>> virtual_day(datetime(2005, 2, 3, 1, 59), vm)
        datetime.date(2005, 2, 2)
        >>> virtual_day(datetime(2005, 2, 3, 2, 0), vm)
        datetime.date(2005, 2, 3)
        >>> virtual_day(datetime(2005, 2, 3, 12, 0), vm)
        datetime.date(2005, 2, 3)
        >>> virtual_day(datetime(2005, 2, 3, 23, 59), vm)
        datetime.date(2005, 2, 3)

    """


def doctest_different_days():
    """Tests for different_days

        >>> from datetime import datetime, time
        >>> from gtimelog.addons.base.models.time_utils import different_days

    Virtual midnight

        >>> vm = time(2, 0)

    The tests themselves:

        >>> different_days(datetime(2005, 2, 3, 1, 15),
        ...                datetime(2005, 2, 3, 2, 15), vm)
        True
        >>> different_days(datetime(2005, 2, 3, 11, 15),
        ...                datetime(2005, 2, 3, 12, 15), vm)
        False

    """


def doctest_first_of_month():
    """Tests for first_of_month

        >>> from gtimelog.addons.base.models.time_utils import first_of_month
        >>> from datetime import date, timedelta

        >>> first_of_month(date(2007, 1, 1))
        datetime.date(2007, 1, 1)

        >>> first_of_month(date(2007, 1, 7))
        datetime.date(2007, 1, 1)

        >>> first_of_month(date(2007, 1, 31))
        datetime.date(2007, 1, 1)

        >>> first_of_month(date(2007, 2, 1))
        datetime.date(2007, 2, 1)

        >>> first_of_month(date(2007, 2, 28))
        datetime.date(2007, 2, 1)

        >>> first_of_month(date(2007, 3, 1))
        datetime.date(2007, 3, 1)

    Why not test extensively?

        >>> d = date(2000, 1, 1)
        >>> while d < date(2005, 1, 1):
        ...     f = first_of_month(d)
        ...     if (f.year, f.month, f.day) != (d.year, d.month, 1):
        ...         print("WRONG: first_of_month(%r) returned %r" % (d, f))
        ...     d += timedelta(1)

    """


def doctest_prev_month():
    """Tests for prev_month

        >>> from gtimelog.addons.base.models.time_utils import prev_month
        >>> from datetime import date, timedelta

        >>> prev_month(date(2007, 3, 1))
        datetime.date(2007, 2, 1)

        >>> prev_month(date(2007, 3, 7))
        datetime.date(2007, 2, 1)

        >>> prev_month(date(2007, 3, 31))
        datetime.date(2007, 2, 1)

        >>> prev_month(date(2007, 4, 1))
        datetime.date(2007, 3, 1)

        >>> prev_month(date(2007, 2, 28))
        datetime.date(2007, 1, 1)

        >>> prev_month(date(2007, 4, 1))
        datetime.date(2007, 3, 1)

    Why not test extensively?

        >>> d = date(2000, 1, 1)
        >>> while d < date(2005, 1, 1):
        ...     f = prev_month(d)
        ...     next = f + timedelta(31)
        ...     if f.day != 1 or (next.year, next.month) != (d.year, d.month):
        ...         print("WRONG: prev_month(%r) returned %r" % (d, f))
        ...     d += timedelta(1)

    """


def doctest_next_month():
    """Tests for next_month

        >>> from gtimelog.addons.base.models.time_utils import next_month
        >>> from datetime import date, timedelta

        >>> next_month(date(2007, 1, 1))
        datetime.date(2007, 2, 1)

        >>> next_month(date(2007, 1, 7))
        datetime.date(2007, 2, 1)

        >>> next_month(date(2007, 1, 31))
        datetime.date(2007, 2, 1)

        >>> next_month(date(2007, 2, 1))
        datetime.date(2007, 3, 1)

        >>> next_month(date(2007, 2, 28))
        datetime.date(2007, 3, 1)

        >>> next_month(date(2007, 3, 1))
        datetime.date(2007, 4, 1)

    Why not test extensively?

        >>> d = date(2000, 1, 1)
        >>> while d < date(2005, 1, 1):
        ...     f = next_month(d)
        ...     prev = f - timedelta(1)
        ...     if f.day != 1 or (prev.year, prev.month) != (d.year, d.month):
        ...         print("WRONG: next_month(%r) returned %r" % (d, f))
        ...     d += timedelta(1)

    """


def doctest_uniq():
    """Tests for uniq

    >>> from gtimelog.addons.base.models.time_utils import uniq
    >>> uniq(['a', 'b', 'b', 'c', 'd', 'b', 'd'])
    ['a', 'b', 'c', 'd', 'b', 'd']
    >>> uniq(['a'])
    ['a']
    >>> uniq([])
    []

    """


def additional_tests():
    return doctest.DocTestSuite(
        optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS,
        checker=Checker(),
    )
