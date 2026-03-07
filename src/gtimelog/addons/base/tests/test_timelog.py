import datetime
import os
import textwrap
import unittest
from io import StringIO

import freezegun

from gtimelog.addons.base.tests.common import Mixins
from gtimelog.addons.timelog.models import TimeLog


class TestTimeLog(Mixins, unittest.TestCase):
    def test_reloading(self):
        logfile = self.tempfile()
        timelog = TimeLog(logfile, datetime.time(2, 0))
        # No file - nothing to reload
        assert not timelog.check_reload()
        # Create a file - it should be reloaded, once.
        open(logfile, 'w').close()
        assert timelog.check_reload()
        assert not timelog.check_reload()
        # Change the timestamp, somehow
        st = os.stat(logfile)
        os.utime(logfile, (st.st_atime, st.st_mtime + 1))
        assert timelog.check_reload()
        assert not timelog.check_reload()
        # Disappearance of the file is noticed
        os.unlink(logfile)
        assert timelog.check_reload()
        assert not timelog.check_reload()

    def test_window_for_day(self):
        timelog = TimeLog(StringIO(), datetime.time(2, 0))
        window = timelog.window_for_day(datetime.date(2015, 9, 17))
        assert window.min_timestamp == datetime.datetime(2015, 9, 17, 2, 0)
        assert window.max_timestamp == datetime.datetime(2015, 9, 18, 2, 0)

    def test_window_for_week(self):
        timelog = TimeLog(StringIO(), datetime.time(2, 0))
        for d in range(14, 21):
            window = timelog.window_for_week(datetime.date(2015, 9, d))
            assert window.min_timestamp == datetime.datetime(2015, 9, 14, 2, 0)
            assert window.max_timestamp == datetime.datetime(2015, 9, 21, 2, 0)

    def test_window_for_month(self):
        timelog = TimeLog(StringIO(), datetime.time(2, 0))
        for d in range(1, 31):
            window = timelog.window_for_month(datetime.date(2015, 9, d))
            assert window.min_timestamp == datetime.datetime(2015, 9, 1, 2, 0)
            assert window.max_timestamp == datetime.datetime(2015, 10, 1, 2, 0)

    def test_window_for_date_range(self):
        timelog = TimeLog(StringIO(), datetime.time(2, 0))
        window = timelog.window_for_date_range(datetime.date(2015, 9, 3), datetime.date(2015, 9, 24))
        assert window.min_timestamp == datetime.datetime(2015, 9, 3, 2, 0)
        assert window.max_timestamp == datetime.datetime(2015, 9, 25, 2, 0)

    def test_appending_clears_window_cache(self):
        # Regression test for https://github.com/gtimelog/gtimelog/issues/28
        timelog = TimeLog(self.tempfile(), datetime.time(2, 0))

        w = timelog.window_for_day(datetime.date(2014, 11, 12))
        assert list(w.all_entries()) == []

        timelog.append('started **', now=datetime.datetime(2014, 11, 12, 10, 00))
        w = timelog.window_for_day(datetime.date(2014, 11, 12))
        assert len(list(w.all_entries())) == 1

    def test_append_adds_blank_line_on_new_day(self):
        timelog = TimeLog(self.tempfile(), datetime.time(2, 0))
        timelog.append('working on sth', now=datetime.datetime(2014, 11, 12, 18, 0))
        timelog.append('new day **', now=datetime.datetime(2014, 11, 13, 8, 0))
        with open(timelog.filename) as f:
            assert f.readlines() == ['2014-11-12 18:00: working on sth\n', '\n', '2014-11-13 08:00: new day **\n']

    @freezegun.freeze_time('2015-05-12 16:27:35.115265')
    def test_append_rounds_the_time(self):
        timelog = TimeLog(self.tempfile(), datetime.time(2, 0))
        timelog.append('now')
        assert timelog.items[-1][0] == datetime.datetime(2015, 5, 12, 16, 27)

    @freezegun.freeze_time('2018-12-09 16:27')
    def test_remove_last_entry(self):
        timelog_data = textwrap.dedent("""
            2018-12-09 08:30: start at home
            2018-12-09 08:40: emails
            # comment
            2018-12-09 12:15: coding
        """)
        filename = self.tempfile()
        self.write_file(filename, timelog_data)
        timelog = TimeLog(filename, datetime.time(2, 0))
        last_entry = timelog.remove_last_entry()
        assert last_entry == 'coding'
        items_after_call = [
            (datetime.datetime(2018, 12, 9, 8, 30), 'start at home'),
            (datetime.datetime(2018, 12, 9, 8, 40), 'emails'),
        ]
        assert timelog.items == items_after_call
        assert timelog.window.items == items_after_call
        with open(filename) as f:
            assert f.read() == textwrap.dedent(
                """\n                2018-12-09 08:30: start at home\n"""
                """                2018-12-09 08:40: emails\n"""
                """                # comment\n"""
                """                ##2018-12-09 12:15: coding\n            """
            )

        last_entry = timelog.remove_last_entry()
        assert last_entry == 'emails'
        items_after_call = [(datetime.datetime(2018, 12, 9, 8, 30), 'start at home')]
        assert timelog.items == items_after_call
        assert timelog.window.items == items_after_call
        with open(filename) as f:
            assert f.read() == textwrap.dedent(
                """\n                2018-12-09 08:30: start at home\n"""
                """                ##2018-12-09 08:40: emails\n"""
                """                # comment\n"""
                """                ##2018-12-09 12:15: coding\n            """
            )

    @freezegun.freeze_time('2018-12-10 10:40')
    def test_remove_last_entry_start_of_day(self):
        timelog_data = textwrap.dedent("""
            2018-12-09 08:30: start at home
            2018-12-09 08:40: emails

            2018-12-10 08:30: start at home
        """)

        filename = self.tempfile()
        self.write_file(filename, timelog_data)
        timelog = TimeLog(filename, datetime.time(2, 0))
        timelog.reread()
        last_entry = timelog.remove_last_entry()
        assert last_entry == 'start at home'
        items_after_call = [
            (datetime.datetime(2018, 12, 9, 8, 30), 'start at home'),
            (datetime.datetime(2018, 12, 9, 8, 40), 'emails'),
        ]
        assert timelog.items == items_after_call
        assert timelog.window.items == []
        with open(filename) as f:
            assert f.read() == textwrap.dedent(
                """\n                2018-12-09 08:30: start at home\n"""
                """                2018-12-09 08:40: emails\n\n"""
                """                ##2018-12-10 08:30: start at home\n            """
            )

        # no further remove possible at beginning of the day:
        last_entry = timelog.remove_last_entry()
        assert last_entry is None

    @freezegun.freeze_time('2015-05-12 16:27')
    def test_valid_time_accepts_any_time_in_the_past_when_log_is_empty(self):
        timelog = TimeLog(StringIO(), datetime.time(2, 0))
        past = datetime.datetime(2015, 5, 12, 14, 20)
        assert timelog.valid_time(past)

    @freezegun.freeze_time('2015-05-12 16:27')
    def test_valid_time_rejects_times_in_the_future(self):
        timelog = TimeLog(StringIO(), datetime.time(2, 0))
        future = datetime.datetime(2015, 5, 12, 16, 30)
        assert not timelog.valid_time(future)

    @freezegun.freeze_time('2015-05-12 16:27')
    def test_valid_time_rejects_times_before_last_entry(self):
        timelog = TimeLog(StringIO('2015-05-12 15:00: did stuff'), datetime.time(2, 0))
        past = datetime.datetime(2015, 5, 12, 14, 20)
        assert not timelog.valid_time(past)

    @freezegun.freeze_time('2015-05-12 16:27')
    def test_valid_time_accepts_times_between_last_entry_and_now(self):
        timelog = TimeLog(StringIO('2015-05-12 15:00: did stuff'), datetime.time(2, 0))
        past = datetime.datetime(2015, 5, 12, 15, 20)
        assert timelog.valid_time(past)

    def test_parse_correction_leaves_regular_text_alone(self):
        timelog = TimeLog(StringIO(), datetime.time(2, 0))
        assert timelog.parse_correction('did stuff') == ('did stuff', None)

    @freezegun.freeze_time('2015-05-12 16:27')
    def test_parse_correction_recognizes_absolute_times(self):
        timelog = TimeLog(StringIO(), datetime.time(2, 0))
        assert timelog.parse_correction('15:20 did stuff') == ('did stuff', datetime.datetime(2015, 5, 12, 15, 20))

    @freezegun.freeze_time('2015-05-12 16:27')
    def test_parse_correction_allows_single_digit_hour(self):
        timelog = TimeLog(StringIO(), datetime.time(2, 0))
        assert timelog.parse_correction('9:20 did stuff') == ('did stuff', datetime.datetime(2015, 5, 12, 9, 20))

    @freezegun.freeze_time('2015-05-13 00:27')
    def test_parse_correction_handles_virtual_midnight_yesterdays_time(self):
        # Regression test for https://github.com/gtimelog/gtimelog/issues/33
        timelog = TimeLog(StringIO(), datetime.time(2, 0))
        assert timelog.parse_correction('15:20 did stuff') == ('did stuff', datetime.datetime(2015, 5, 12, 15, 20))

    @freezegun.freeze_time('2015-05-13 00:27')
    def test_parse_correction_handles_virtual_midnight_todays_time(self):
        timelog = TimeLog(StringIO(), datetime.time(2, 0))
        assert timelog.parse_correction('00:15 did stuff') == ('did stuff', datetime.datetime(2015, 5, 13, 0, 15))

    @freezegun.freeze_time('2015-05-12 16:27')
    def test_parse_correction_ignores_future_absolute_times(self):
        timelog = TimeLog(StringIO(), datetime.time(2, 0))
        assert timelog.parse_correction('17:20 did stuff') == ('17:20 did stuff', None)

    @freezegun.freeze_time('2015-05-12 16:27')
    def test_parse_correction_ignores_bad_absolute_times(self):
        timelog = TimeLog(StringIO(), datetime.time(2, 0))
        assert timelog.parse_correction('19:60 did stuff') == ('19:60 did stuff', None)
        assert timelog.parse_correction('24:00 did stuff') == ('24:00 did stuff', None)

    @freezegun.freeze_time('2015-05-12 16:27')
    def test_parse_correction_ignores_absolute_times_before_last_entry(self):
        timelog = TimeLog(StringIO('2015-05-12 16:00: stuff'), datetime.time(2, 0))
        assert timelog.parse_correction('15:20 did stuff') == ('15:20 did stuff', None)

    @freezegun.freeze_time('2015-05-12 16:27')
    def test_parse_correction_recognizes_negative_relative_times(self):
        timelog = TimeLog(StringIO(), datetime.time(2, 0))
        assert timelog.parse_correction('-20 did stuff') == ('did stuff', datetime.datetime(2015, 5, 12, 16, 7))

    @freezegun.freeze_time('2015-05-12 16:27')
    def test_parse_correction_recognizes_positive_relative_times(self):
        timelog = TimeLog(StringIO('2015-05-12 15:50: stuff'), datetime.time(2, 0))
        assert timelog.parse_correction('+20 did stuff') == ('did stuff', datetime.datetime(2015, 5, 12, 16, 10))

    @freezegun.freeze_time('2015-05-12 16:27')
    def test_parse_correction_ignores_positive_relative_times_without_initial_entry(self):
        timelog = TimeLog(StringIO(), datetime.time(2, 0))
        assert timelog.parse_correction('+20 did stuff') == ('+20 did stuff', None)

    @freezegun.freeze_time('2015-05-12 16:27')
    def test_parse_correction_ignores_negative_relative_times_before_last_entry(self):
        timelog = TimeLog(StringIO('2015-05-12 16:00: stuff'), datetime.time(2, 0))
        assert timelog.parse_correction('-30 did stuff') == ('-30 did stuff', None)

    @freezegun.freeze_time('2015-05-12 16:27')
    def test_parse_correction_ignores_positive_relative_times_in_the_future(self):
        timelog = TimeLog(StringIO('2015-05-12 15:50: stuff'), datetime.time(2, 0))
        assert timelog.parse_correction('+40 did stuff') == ('+40 did stuff', None)

    @freezegun.freeze_time('2015-05-12 16:27')
    def test_parse_correction_ignores_bad_negative_relative_times(self):
        timelog = TimeLog(StringIO(), datetime.time(2, 0))
        assert timelog.parse_correction('-200 did stuff') == ('-200 did stuff', None)

    @freezegun.freeze_time('2015-05-12 16:27')
    def test_parse_correction_ignores_bad_positive_relative_times(self):
        timelog = TimeLog(StringIO('2015-05-12 15:50: stuff'), datetime.time(2, 0))
        assert timelog.parse_correction('+200 did stuff') == ('+200 did stuff', None)

    @freezegun.freeze_time('2014-11-12 10:00:00.00')
    def test_appending_without_rounded_time_tasks(self):
        # Test rounding method
        current_datetime = datetime.datetime.now()
        current_date = current_datetime.date()
        current_time = current_datetime.time()
        timelog = TimeLog(self.tempfile(), current_time, rounding_time=0, rounding_time_force_above=False)

        # Check emptyness before adding tasks
        w = timelog.window_for_day(current_date)
        assert list(w.all_entries()) == []

        oracle = {
            'started ***': (current_datetime, datetime.timedelta(minutes=0)),
            'sample task no time': (current_datetime.replace(hour=10, minute=5), datetime.timedelta(minutes=5)),
            'break **': (current_datetime.replace(hour=10, minute=58), datetime.timedelta(minutes=53)),
            'sample task smallest time rounded': (
                current_datetime.replace(hour=11, minute=12),
                datetime.timedelta(minutes=14),
            ),
            'sample task normal time rounded': (
                current_datetime.replace(hour=11, minute=59),
                datetime.timedelta(minutes=47),
            ),
        }
        for entry in oracle:
            _datetime, duration = oracle.get(entry)
            timelog.append(entry, now=_datetime)
        w = timelog.window_for_day(current_date)
        for entry in w.all_entries():
            _datetime, duration = oracle.get(entry.entry, (False, False))
            assert duration == entry.duration, f"Entry '{entry.entry}' has the wrong duration"

    @freezegun.freeze_time('2014-11-12 10:00:00.00')
    def test_appending_with_rounded_time_tasks(self):
        # Test rounding method
        current_datetime = datetime.datetime.now()
        current_date = current_datetime.date()
        current_time = current_datetime.time()
        timelog = TimeLog(self.tempfile(), current_time, rounding_time=15, rounding_time_force_above=False)

        # Check emptyness before adding tasks
        w = timelog.window_for_day(current_date)
        assert list(w.all_entries()) == []

        oracle = {
            'started ***': (current_datetime, datetime.timedelta(minutes=0)),
            'sample task no time': (
                current_datetime.replace(hour=10, minute=5),
                datetime.timedelta(minutes=0),  # 10:00 to 10:00 (10:05 rounded average to 10:00) = 0 min
            ),
            'break **': (
                current_datetime.replace(hour=10, minute=58),
                datetime.timedelta(minutes=45),  # 10:00 to 10:45 (10:58 rounded down) = 45 min
            ),
            'sample task smallest time rounded': (
                current_datetime.replace(hour=11, minute=12),
                datetime.timedelta(minutes=30),  # 10:45 to 11:15 (11:12 rounded average to 11:15) = 30 min
            ),
            'sample task normal time rounded': (
                current_datetime.replace(hour=11, minute=59),
                datetime.timedelta(minutes=45),  # 11:15 to 12:00 (11:59 rounded average to 12:00) = 45 min
            ),
        }
        for entry in oracle:
            _datetime, duration = oracle.get(entry)
            timelog.append(entry, now=_datetime)
        w = timelog.window_for_day(current_date)
        for entry in w.all_entries():
            _datetime, duration = oracle.get(entry.entry, (False, False))
            assert duration == entry.duration, f"Entry '{entry.entry}' has the wrong duration"

    @freezegun.freeze_time('2014-11-12 10:00:00.00')
    def test_appending_with_force_above_rounded_time_tasks(self):
        # Test rounding method
        current_datetime = datetime.datetime.now()
        current_date = current_datetime.date()
        current_time = current_datetime.time()
        timelog = TimeLog(self.tempfile(), current_time, rounding_time=15, rounding_time_force_above=True)

        # Check emptyness before adding tasks
        w = timelog.window_for_day(current_date)
        assert list(w.all_entries()) == []

        oracle = {
            'started ***': (current_datetime, datetime.timedelta(minutes=0)),
            'sample task no time': (
                current_datetime.replace(hour=10, minute=5),
                datetime.timedelta(minutes=15),  # 10:00 to 10:15 (10:05 rounded up) = 15 min
            ),
            'break **': (
                current_datetime.replace(hour=10, minute=58),
                datetime.timedelta(minutes=30),  # 10:15 to 10:45 (10:58 rounded down) = 30 min
            ),
            'sample task smallest time rounded': (
                current_datetime.replace(hour=11, minute=12),
                datetime.timedelta(minutes=30),  # 10:45 to 11:15 (11:12 rounded up) = 30 min
            ),
            'sample task normal time rounded': (
                current_datetime.replace(hour=11, minute=59),
                datetime.timedelta(minutes=45),  # 11:15 to 12:00 (11:59 rounded up) = 45 min
            ),
        }
        for entry in oracle:
            _datetime, duration = oracle.get(entry)
            timelog.append(entry, now=_datetime)
        w = timelog.window_for_day(current_date)
        for entry in w.all_entries():
            _datetime, duration = oracle.get(entry.entry, (False, False))
            assert duration == entry.duration, f"Entry '{entry.entry}' has the wrong duration"

    @freezegun.freeze_time('2014-11-12 10:00:00.00')
    def test_get_rounding_delta_and_method(self):
        # Test rounding method
        current_datetime = datetime.datetime.now()
        current_time = current_datetime.time()
        timelog = TimeLog(self.tempfile(), current_time, rounding_time=15, rounding_time_force_above=True)
        oracle = {
            'started ***': 'down',  # has **, so uses "down"
            'sample task no time': 'up',  # no **, force_above=True, so uses "up"
            'break **': 'down',  # has **, so uses "down"
        }
        for entry, method in oracle.items():
            _result_delta, result_method = timelog.get_rounding_delta_and_method(entry)
            assert result_method == method, f"Entry '{entry}' has an invalid rounding method"

        timelog = TimeLog(self.tempfile(), current_time, rounding_time=15, rounding_time_force_above=False)
        oracle = {
            'started ***': 'down',  # has **, so uses "down"
            'sample task no time': 'average',  # no **, force_above=False, so uses "average"
            'break **': 'down',  # has **, so uses "down"
        }
        for entry, method in oracle.items():
            _result_delta, result_method = timelog.get_rounding_delta_and_method(entry)
            assert result_method == method, f"Entry '{entry}' has an invalid rounding method"
