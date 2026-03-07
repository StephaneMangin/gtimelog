import unittest

from gtimelog.addons.tasks_sync_planio.models.sync_backend import TaskSyncBackend


class FakeSettings:
    """Minimal settings stub implementing get_boolean/get_string."""

    def __init__(self, booleans, strings):
        self._booleans = booleans
        self._strings = strings

    def get_boolean(self, name):
        return self._booleans.get(name, False)

    def get_string(self, name):
        return self._strings.get(name, '')


class TestPlanioBackendFlags(unittest.TestCase):
    """Unit tests for Planio backend activation gates."""

    def test_is_configured_requires_enabled_url_and_customer(self):
        backend = TaskSyncBackend()
        settings = FakeSettings(
            booleans={'planio-enabled': True},
            strings={'planio-url': 'https://example.plan.io', 'planio-customer': 'ACME'},
        )
        assert backend.is_configured(settings)

    def test_should_handle_remote_sync_requires_sync_scheme(self):
        backend = TaskSyncBackend()
        settings = FakeSettings(
            booleans={'planio-enabled': True, 'remote-task-list': True},
            strings={
                'planio-url': 'https://example.plan.io',
                'planio-customer': 'ACME',
                'task-list-url': 'sync://planio',
            },
        )
        assert backend.should_handle_remote_sync(settings)

    def test_should_handle_remote_sync_rejects_other_urls(self):
        backend = TaskSyncBackend()
        settings = FakeSettings(
            booleans={'planio-enabled': True, 'remote-task-list': True},
            strings={
                'planio-url': 'https://example.plan.io',
                'planio-customer': 'ACME',
                'task-list-url': 'https://remote/tasks.txt',
            },
        )
        assert not backend.should_handle_remote_sync(settings)
