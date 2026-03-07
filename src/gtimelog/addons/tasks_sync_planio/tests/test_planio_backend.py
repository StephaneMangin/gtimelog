import unittest
from unittest.mock import MagicMock


class TestPlanioBackendLogic(unittest.TestCase):
    """Test backend decision logic."""

    def test_is_configured_with_all_required(self):
        """Return True when all Planio settings present."""
        from gtimelog.addons.tasks_sync_planio.models.sync_backend import TaskSyncBackend

        gsettings = MagicMock()
        gsettings.get_boolean.side_effect = lambda k: k == 'planio-enabled'
        gsettings.get_string.side_effect = lambda k: {
            'planio-url': 'https://planio.example.com',
            'planio-customer': 'Customer1',
        }.get(k, '')

        backend = TaskSyncBackend()
        assert backend.is_configured(gsettings) is True

    def test_is_configured_missing_url(self):
        """Return False when URL is empty."""
        from gtimelog.addons.tasks_sync_planio.models.sync_backend import TaskSyncBackend

        gsettings = MagicMock()
        gsettings.get_boolean.return_value = True
        gsettings.get_string.side_effect = lambda k: {
            'planio-url': '',
            'planio-customer': 'Customer1',
        }.get(k, '')

        backend = TaskSyncBackend()
        assert backend.is_configured(gsettings) is False

    def test_is_configured_disabled(self):
        """Return False when planio-enabled is False."""
        from gtimelog.addons.tasks_sync_planio.models.sync_backend import TaskSyncBackend

        gsettings = MagicMock()
        gsettings.get_boolean.return_value = False
        gsettings.get_string.return_value = 'https://planio.example.com'

        backend = TaskSyncBackend()
        assert backend.is_configured(gsettings) is False

    def test_should_handle_remote_sync_true(self):
        """Return True when sync://planio scheme with settings enabled."""
        from gtimelog.addons.tasks_sync_planio.models.sync_backend import TaskSyncBackend

        gsettings = MagicMock()
        gsettings.get_boolean.side_effect = lambda k: {
            'planio-enabled': True,
            'remote-task-list': True,
        }.get(k, False)
        gsettings.get_string.side_effect = lambda k: {
            'planio-url': 'https://planio.example.com',
            'planio-customer': 'Cust',
            'task-list-url': 'sync://planio',
        }.get(k, '')

        backend = TaskSyncBackend()
        assert backend.should_handle_remote_sync(gsettings) is True

    def test_should_handle_remote_sync_wrong_scheme(self):
        """Return False when task-list-url is not sync://planio."""
        from gtimelog.addons.tasks_sync_planio.models.sync_backend import TaskSyncBackend

        gsettings = MagicMock()
        gsettings.get_boolean.return_value = True
        gsettings.get_string.side_effect = lambda k: {
            'task-list-url': 'sync://jira',
        }.get(k, 'https://example.com')

        backend = TaskSyncBackend()
        # is_configured will fail, so should_handle returns False
        assert backend.should_handle_remote_sync(gsettings) is False

    def test_backend_state_tracking(self):
        """Track sync error and count state."""
        from gtimelog.addons.tasks_sync_planio.models.sync_backend import TaskSyncBackend

        backend = TaskSyncBackend()
        assert backend.get_last_error() == ''
        assert backend.get_last_count() == 0

        # Simulate error setting
        backend._last_error = 'Test error'
        backend._last_count = 5

        assert backend.get_last_error() == 'Test error'
        assert backend.get_last_count() == 5

    def test_issue_to_sync_task_conversion(self):
        """Convert issue object to SyncTask."""
        from gtimelog.addons.tasks_sync_planio.models.sync_backend import TaskSyncBackend
        from gtimelog.addons.tasks_sync_planio.models.sync_task import SyncTask

        issue = MagicMock()
        issue.id = 42
        issue.subject = 'Test Issue'
        issue.project.name = 'MyProject'
        issue.status.name = 'New'
        issue.category.name = 'Bug'

        mapping = MagicMock()
        mapping.ensure_mapping.return_value = 'Mapped'

        client = MagicMock()
        client.get_custom_field.return_value = 'WP-001'

        task = TaskSyncBackend._issue_to_sync_task(issue, mapping, 'Cust', client)

        assert isinstance(task, SyncTask)
        assert task.id == 42
        assert task.subject == 'Test Issue'
        assert task.customer_name == 'Cust'
        assert task.work_package == 'WP-001'

    def test_issue_to_sync_task_missing_category(self):
        """Handle issue without category."""
        from gtimelog.addons.tasks_sync_planio.models.sync_backend import TaskSyncBackend

        issue = MagicMock()
        issue.id = 1
        issue.subject = 'Test'
        issue.project.name = 'Proj'
        issue.status.name = 'New'
        issue.category = None

        mapping = MagicMock()
        mapping.ensure_mapping.return_value = 'Proj'

        client = MagicMock()
        client.get_custom_field.return_value = ''

        task = TaskSyncBackend._issue_to_sync_task(issue, mapping, 'Cust', client)

        assert task.category == 'N/A'
