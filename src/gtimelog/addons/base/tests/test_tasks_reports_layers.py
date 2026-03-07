import datetime
import io
import unittest

from gtimelog.models import component_registry


class TestTasksLayers(unittest.TestCase):
    def setUp(self):
        self.domain = component_registry.get('domain.tasks.policy')()
        self.application = component_registry.get('application.tasks.service')(self.domain)

    def test_can_edit_tasks_domain_rules(self):
        assert self.domain.can_edit_tasks(False, '')
        assert not self.domain.can_edit_tasks(True, '')
        assert self.domain.can_edit_tasks(True, 'https://edit')

    def test_application_tasks_settings_orchestration(self):
        class FakeSettings:
            def __init__(self, remote=True, url='https://example', edit_url='https://edit'):
                self._remote = remote
                self._url = url
                self._edit_url = edit_url

            def get_boolean(self, key):
                assert key == 'remote-task-list'
                return self._remote

            def get_string(self, key):
                if key == 'task-list-url':
                    return self._url
                assert key == 'task-list-edit-url'
                return self._edit_url

        class FakeSettingsService:
            @staticmethod
            def get_task_list_cache_file():
                return '/tmp/cache-tasks.txt'

            @staticmethod
            def get_task_list_file():
                return '/tmp/local-tasks.txt'

        remote_settings = FakeSettings(remote=True)
        local_settings = FakeSettings(remote=False)

        assert self.application.should_download_tasks(remote_settings)
        assert self.application.can_edit_tasks(remote_settings)
        assert self.application.get_tasks_filename(remote_settings, FakeSettingsService()) == '/tmp/cache-tasks.txt'
        assert self.application.get_tasks_filename(local_settings, FakeSettingsService()) == '/tmp/local-tasks.txt'


class TestReportsLayers(unittest.TestCase):
    def setUp(self):
        self.domain = component_registry.get('domain.reports.service')()
        self.application = component_registry.get('application.reports.service')(self.domain)

    def test_parse_entry_line_invalid_value(self):
        parsed = self.application.parse_entry_line(None)
        assert parsed['error']
        assert parsed['customer'] is None

    def test_build_and_render_customer_tree(self):
        work_entries = [
            (datetime.datetime(2026, 3, 2, 9, 0), 'invalid entry', datetime.timedelta(minutes=30)),
        ]
        errors, tree = self.application.build_customer_tree(work_entries)
        assert errors == ['invalid entry']
        assert tree == {}

        output = io.StringIO()
        self.application.render_customer_tree(output, tree)
        rendered = output.getvalue()
        assert 'SUMMARY OF TASKS BY CLIENTS' in rendered
        assert 'TOTAL' in rendered
