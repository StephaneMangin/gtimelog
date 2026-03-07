import doctest
import sys  # noqa: F401 -- used in doctests
from io import StringIO  # noqa: F401 -- used in doctests
from unittest import mock  # noqa: F401 -- used in doctests

import freezegun  # noqa: F401 -- used in doctests

from gtimelog.addons.base.tests.common import Checker, make_time_window  # noqa: F401
from gtimelog.addons.reports_csv.controllers.exports import Exports as CsvExports  # noqa: F401 -- used in doctests
from gtimelog.addons.reports_ical.controllers.exports import Exports as IcalExports  # noqa: F401 -- used in doctests


def doctest_CsvExports_to_csv_complete():
    r"""Tests for CSV exports to_csv_complete

    >>> from datetime import datetime, time
    >>> min = datetime(2008, 6, 1)
    >>> max = datetime(2008, 7, 1)
    >>> vm = time(2, 0)

    >>> sampledata = StringIO('''
    ... 2008-06-03 12:45: start
    ... 2008-06-03 13:00: something
    ... 2008-06-03 14:45: something else
    ... 2008-06-03 15:45: etc
    ... 2008-06-05 12:45: start
    ... 2008-06-05 13:15: something
    ... 2008-06-05 14:15: rest **
    ... 2008-06-05 16:15: let's not mention this ever again ***
    ... ''')

    >>> window = make_time_window(sampledata, min, max, vm)

    >>> CsvExports(window).to_csv_complete(sys.stdout)
    task,time (minutes)
    etc,60
    something,45
    something else,105

    """


def doctest_CsvExports_to_csv_daily():
    r"""Tests for CSV exports to_csv_daily

    >>> from datetime import datetime, time
    >>> min = datetime(2008, 6, 1)
    >>> max = datetime(2008, 7, 1)
    >>> vm = time(2, 0)

    >>> sampledata = StringIO('''
    ... 2008-06-03 12:45: start
    ... 2008-06-03 13:00: something
    ... 2008-06-03 14:45: something else
    ... 2008-06-03 15:45: etc
    ... 2008-06-05 12:45: start
    ... 2008-06-05 13:15: something
    ... 2008-06-05 14:15: rest **
    ... ''')

    >>> window = make_time_window(sampledata, min, max, vm)

    >>> CsvExports(window).to_csv_daily(sys.stdout)
    date,day-start (hours),slacking (hours),work (hours)
    2008-06-03,12.75,0.0,3.0
    2008-06-04,0.0,0.0,0.0
    2008-06-05,12.75,1.0,0.5

    """


def doctest_IcalExports_icalendar():
    r"""Tests for iCalendar exports icalendar

    >>> from datetime import datetime, time
    >>> min = datetime(2008, 6, 1)
    >>> max = datetime(2008, 7, 1)
    >>> vm = time(2, 0)

    >>> sampledata = StringIO(r'''
    ... 2008-06-03 12:45: start **
    ... 2008-06-03 13:00: something
    ... 2008-06-03 15:45: something, else; with special\chars
    ... 2008-06-05 12:45: start **
    ... 2008-06-05 13:15: something
    ... 2008-06-05 14:15: rest **
    ... ''')

    >>> window = make_time_window(sampledata, min, max, vm)

    >>> with freezegun.freeze_time("2015-05-18 15:40"):
    ...     with mock.patch('socket.getfqdn') as mock_getfqdn:
    ...         mock_getfqdn.return_value = 'localhost'
    ...         IcalExports(window).icalendar(sys.stdout)
    ... # doctest: +REPORT_NDIFF
    BEGIN:VCALENDAR
    PRODID:-//gtimelog.org/NONSGML GTimeLog//EN
    VERSION:2.0
    BEGIN:VEVENT
    UID:c3cc5c6fff8660f4f5e76409272d2ed64c2c5b5c27a83c2697dfb88a9f4d4e9b@localhost
    SUMMARY:start **
    DTSTART:20080603T124500
    DTEND:20080603T124500
    DTSTAMP:20150518T154000Z
    END:VEVENT
    BEGIN:VEVENT
    UID:5b17967b6b95f956f76befed61af664e667dde655017fd84e30c6c191e5f6d92@localhost
    SUMMARY:something
    DTSTART:20080603T124500
    DTEND:20080603T130000
    DTSTAMP:20150518T154000Z
    END:VEVENT
    BEGIN:VEVENT
    UID:e63248ca64daf69ecef875ea5b19ea648c530fea89a51d44abff41022ceec132@localhost
    SUMMARY:something\, else\; with special\\chars
    DTSTART:20080603T130000
    DTEND:20080603T154500
    DTSTAMP:20150518T154000Z
    END:VEVENT
    BEGIN:VEVENT
    UID:929886af1087bb602a69a19b0b4e6079d6a5c3d77d8a82d42155877bc5e5a9ab@localhost
    SUMMARY:start **
    DTSTART:20080605T124500
    DTEND:20080605T124500
    DTSTAMP:20150518T154000Z
    END:VEVENT
    BEGIN:VEVENT
    UID:97c51380d110ac30321371c987ebfba0399d6c429bef7ab71548230b7c53767d@localhost
    SUMMARY:something
    DTSTART:20080605T124500
    DTEND:20080605T131500
    DTSTAMP:20150518T154000Z
    END:VEVENT
    BEGIN:VEVENT
    UID:e495a6df38857ab12fcd712905b8327ea3ffc217d39cd1cf95a259a4cdebc356@localhost
    SUMMARY:rest **
    DTSTART:20080605T131500
    DTEND:20080605T141500
    DTSTAMP:20150518T154000Z
    END:VEVENT
    END:VCALENDAR

    """


def additional_tests():
    return doctest.DocTestSuite(
        optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS,
        checker=Checker(),
    )
