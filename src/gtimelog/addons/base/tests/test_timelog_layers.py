import datetime
import unittest

import pytest

from gtimelog.models import component_registry


class TestTimelogLayers(unittest.TestCase):
    def setUp(self):
        self.domain = component_registry.get('domain.timelog.policy')()
        self.application = component_registry.get('application.timelog.service')(self.domain)

    def test_normalize_task_entry_handles_bytes_and_spaces(self):
        assert self.domain.normalize_task_entry(b'  coding task  ') == 'coding task'
        assert self.domain.normalize_task_entry('  review  ') == 'review'

    def test_is_add_entry_enabled_requires_timelog_and_non_empty_entry(self):
        assert self.domain.is_add_entry_enabled(True, 'task')
        assert not self.domain.is_add_entry_enabled(False, 'task')
        assert not self.domain.is_add_entry_enabled(True, '   ')

    def test_validate_detail_level_accepts_known_values(self):
        assert self.domain.validate_detail_level('chronological') == 'chronological'
        with pytest.raises(ValueError):
            self.domain.validate_detail_level('invalid')

    def test_validate_time_range_accepts_known_values(self):
        assert self.domain.validate_time_range('week') == 'week'
        with pytest.raises(ValueError):
            self.domain.validate_time_range('year')

    def test_prepare_entry_for_append_delegates_to_parse_correction(self):
        called = {}

        def fake_parse_correction(entry):
            called['entry'] = entry
            return entry + ' normalized', None

        entry, when = self.application.prepare_entry_for_append('  my task  ', fake_parse_correction)
        assert called['entry'] == 'my task'
        assert entry == 'my task normalized'
        assert when is None

    def test_should_reset_date_after_append(self):
        assert self.application.should_reset_date_after_append(False)
        assert not self.application.should_reset_date_after_append(True)

    def test_navigation_delegates_to_domain(self):
        date = datetime.date(2026, 3, 15)
        assert self.application.previous_date(date, 'day') == datetime.date(2026, 3, 14)
        assert self.application.next_date(date, 'week') == datetime.date(2026, 3, 22)
        assert self.application.home_date() is None

    def test_settings_accessors_and_build_timelog(self):
        class FakeSettings:
            def get_value(self, key):
                assert key == 'virtual-midnight'
                return 2, 30

            def get_int(self, key):
                assert key == 'rounding-time'
                return 15

            def get_boolean(self, key):
                assert key == 'rounding-time-force-above'
                return True

        class FakeTimeLog:
            def __init__(self, filename, virtual_midnight, rounding_time, rounding_time_force_above):
                self.filename = filename
                self.virtual_midnight = virtual_midnight
                self.rounding_time = rounding_time
                self.rounding_time_force_above = rounding_time_force_above

        settings = FakeSettings()
        timelog = self.application.build_timelog(settings, '/tmp/timelog.txt', FakeTimeLog)
        assert timelog.filename == '/tmp/timelog.txt'
        assert timelog.virtual_midnight == datetime.time(2, 30)
        assert timelog.rounding_time == 15
        assert timelog.rounding_time_force_above
