import datetime
import unittest
from unittest import mock

from gtimelog.addons.office_hours.services import OfficeHoursService

time_left_at_work = OfficeHoursService.time_left_at_work
estimated_week_overtime = OfficeHoursService.estimated_week_overtime
office_time_status = OfficeHoursService.office_time_status


def _h(hours):
    return datetime.timedelta(hours=hours)


class TestTimeLeftAtWork(unittest.TestCase):
    def test_basic(self):
        assert time_left_at_work(8, _h(6), _h(0)) == _h(2)

    def test_overtime(self):
        assert time_left_at_work(8, _h(9), _h(0)) == _h(-1)

    def test_with_current_task(self):
        assert time_left_at_work(8, _h(5), _h(1)) == _h(2)

    def test_zero_target(self):
        assert time_left_at_work(0, _h(3), _h(0)) == _h(-3)

    def test_exact_match(self):
        assert time_left_at_work(8, _h(7), _h(1)) == datetime.timedelta(0)


class TestEstimatedWeekOvertime(unittest.TestCase):
    @mock.patch('gtimelog.addons.office_hours.services.office_hours_service.datetime')
    def test_midweek_wednesday(self, mock_dt):
        mock_dt.datetime.now.return_value = datetime.datetime(2025, 1, 8)
        mock_dt.timedelta = datetime.timedelta
        result = estimated_week_overtime(
            office_hours=8,
            week_days_str='Monday,Tuesday,Wednesday,Thursday,Friday',
            week_total_work=_h(24),
            time_left=_h(0),
        )
        assert result == datetime.timedelta(0)

    @mock.patch('gtimelog.addons.office_hours.services.office_hours_service.datetime')
    def test_overtime_friday(self, mock_dt):
        mock_dt.datetime.now.return_value = datetime.datetime(2025, 1, 10)
        mock_dt.timedelta = datetime.timedelta
        result = estimated_week_overtime(
            office_hours=8,
            week_days_str='Monday,Tuesday,Wednesday,Thursday,Friday',
            week_total_work=_h(42),
            time_left=_h(-2),
        )
        assert result == datetime.timedelta(0)

    def test_empty_week_days(self):
        assert estimated_week_overtime(8, '', _h(10), _h(0)) is None

    def test_invalid_day_names(self):
        assert estimated_week_overtime(8, 'Funday,Cakeday', _h(10), _h(0)) is None


class TestOfficeTimeStatus(unittest.TestCase):
    def test_under_target(self):
        total, delta, is_overtime = office_time_status(8, _h(1), _h(5), _h(0))
        assert total == _h(6)
        assert delta == _h(2)
        assert not is_overtime

    def test_over_target(self):
        total, delta, is_overtime = office_time_status(8, _h(1), _h(8), _h(0))
        assert total == _h(9)
        assert delta == _h(1)
        assert is_overtime

    def test_exact_target(self):
        total, _delta, is_overtime = office_time_status(8, _h(1), _h(7), _h(0))
        assert total == _h(8)
        assert not is_overtime

    def test_with_current_task(self):
        _total, _delta, is_overtime = office_time_status(8, _h(0), _h(6), _h(3))
        assert is_overtime

    def test_zero_office_hours(self):
        _, _, is_overtime = office_time_status(0, _h(0), _h(1), _h(0))
        assert is_overtime


class TestServiceAliases(unittest.TestCase):
    def test_module_level_aliases(self):
        assert time_left_at_work is OfficeHoursService.time_left_at_work
        assert estimated_week_overtime is OfficeHoursService.estimated_week_overtime
        assert office_time_status is OfficeHoursService.office_time_status


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
