import datetime
import io
import unittest

from gtimelog.models import component_registry


class TestCsvExportLayers(unittest.TestCase):
    def setUp(self):
        self.service = component_registry.get('application.export.csv.service')()

    def test_to_csv_complete_rows(self):
        rows = self.service.to_csv_complete_rows(
            [
                (datetime.datetime(2026, 3, 2, 9, 0), 'Task B', datetime.timedelta(minutes=30)),
                (datetime.datetime(2026, 3, 2, 10, 0), 'Task A', datetime.timedelta(minutes=45)),
            ]
        )
        assert rows == [('Task A', 45), ('Task B', 30)]

    def test_to_csv_daily_rows(self):
        entries = [
            (
                datetime.datetime(2026, 3, 2, 9, 15),
                datetime.datetime(2026, 3, 2, 10, 0),
                datetime.timedelta(minutes=45),
                set(),
                'Task A',
            ),
            (
                datetime.datetime(2026, 3, 3, 14, 0),
                datetime.datetime(2026, 3, 3, 14, 30),
                datetime.timedelta(minutes=30),
                set(),
                'Break **',
            ),
        ]
        rows = self.service.to_csv_daily_rows(entries)
        assert len(rows) == 2
        assert rows[0][0] == datetime.date(2026, 3, 2)
        assert rows[1][0] == datetime.date(2026, 3, 3)


class TestIcalExportLayers(unittest.TestCase):
    def setUp(self):
        self.service = component_registry.get('application.export.ical.service')()

    def test_write_icalendar_contains_expected_sections(self):
        entries = [
            (
                datetime.datetime(2026, 3, 2, 9, 0),
                datetime.datetime(2026, 3, 2, 9, 30),
                datetime.timedelta(minutes=30),
                set(),
                'Task A',
            )
        ]
        output = io.StringIO()
        self.service.write_icalendar(output, entries)
        content = output.getvalue()
        assert 'BEGIN:VCALENDAR' in content
        assert 'BEGIN:VEVENT' in content
        assert 'SUMMARY:Task A' in content
        assert 'END:VCALENDAR' in content
