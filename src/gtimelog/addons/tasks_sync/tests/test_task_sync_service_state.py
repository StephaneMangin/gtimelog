import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gtimelog.addons.tasks_sync.models.sync_payload import SyncPayload
from gtimelog.addons.tasks_sync.services.task_sync_service import TaskSyncService


class FakeTask:
    """Minimal synchronized task object for storage writes."""

    def __init__(self, identifier: int):
        self.id = identifier

    def render(self, _template: str):
        return f'ACME: task {self.id}\n'


class FakeGSettings:
    """In-memory settings store emulating the Gio.Settings API used here."""

    def __init__(self):
        self._booleans = {}
        self._strings = {
            'last-sync-message': '',
            'last-sync-at': '',
        }

    def set_boolean(self, name, value):
        self._booleans[name] = bool(value)

    def set_string(self, name, value):
        self._strings[name] = value

    def get_string(self, name):
        return self._strings.get(name, '')


class FakeSettingsService:
    """Settings service stub with filesystem paths used by backend payload."""

    def __init__(self, tmpdir):
        self._tmpdir = Path(tmpdir)

    def get_planio_project_mapping_file(self):
        return str(self._tmpdir / 'projects_mapping.json')

    def get_planio_sync_cache_file(self):
        return str(self._tmpdir / 'planio-remote-tasks.txt')


class SuccessBackend:
    """Backend that simulates a successful sync run."""

    def __init__(self, tmpdir):
        self._tmpdir = Path(tmpdir)

    def is_configured(self, _gsettings):
        return True

    def sync(self, _gsettings, _settings_service):
        return SyncPayload(
            tasks=[FakeTask(1)],
            filename=str(self._tmpdir / 'planio-remote-tasks.txt'),
            customer_name='ACME',
            task_format='{subject}',
        )

    def get_last_count(self):
        return 1

    def get_last_error(self):
        return ''


class FailureBackend:
    """Backend that simulates a failed sync run."""

    def is_configured(self, _gsettings):
        return True

    def sync(self, _gsettings, _settings_service):
        return None

    def get_last_count(self):
        return 0

    def get_last_error(self):
        return 'Planio request failed'


class ExceptionBackend:
    """Backend that raises during sync to emulate runtime dependency failures."""

    def is_configured(self, _gsettings):
        return True

    def sync(self, _gsettings, _settings_service):
        raise RuntimeError('redminelib is required for Planio synchronization.')

    def get_last_count(self):
        return 0

    def get_last_error(self):
        return ''


class TestTaskSyncServiceState(unittest.TestCase):
    """Validate persisted sync status after success and failure paths."""

    def test_sync_success_updates_status_keys(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            gsettings = FakeGSettings()
            service = TaskSyncService(backend=SuccessBackend(tmpdir))

            with patch(
                'gtimelog.addons.tasks_sync.services.task_sync_service.component_registry.get',
                return_value=lambda: FakeSettingsService(tmpdir),
            ):
                result = service.sync_now(gsettings)

            assert result
            assert gsettings._booleans['last-sync-success']
            assert 'Success:' in gsettings.get_string('last-sync-message')
            assert gsettings.get_string('last-sync-at')

    def test_sync_failure_updates_status_keys(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            gsettings = FakeGSettings()
            service = TaskSyncService(backend=FailureBackend())

            with patch(
                'gtimelog.addons.tasks_sync.services.task_sync_service.component_registry.get',
                return_value=lambda: FakeSettingsService(tmpdir),
            ):
                result = service.sync_now(gsettings)

            assert not result
            assert not gsettings._booleans['last-sync-success']
            assert gsettings.get_string('last-sync-message') == 'Planio request failed'
            assert gsettings.get_string('last-sync-at')

    def test_sync_exception_updates_status_keys(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            gsettings = FakeGSettings()
            service = TaskSyncService(backend=ExceptionBackend())

            with patch(
                'gtimelog.addons.tasks_sync.services.task_sync_service.component_registry.get',
                return_value=lambda: FakeSettingsService(tmpdir),
            ):
                result = service.sync_now(gsettings)

            assert not result
            assert not gsettings._booleans['last-sync-success']
            assert gsettings.get_string('last-sync-message') == 'redminelib is required for Planio synchronization.'
            assert gsettings.get_string('last-sync-at')
