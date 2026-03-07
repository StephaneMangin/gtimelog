import unittest
from unittest.mock import MagicMock, patch


class TestPlanioBackendIsConfigured(unittest.TestCase):
    """Test is_configured decision logic."""

    def test_is_configured_all_settings_present(self):
        """Configured when all required settings present."""
        from gtimelog.addons.tasks_sync_planio.models.sync_backend import TaskSyncBackend

        backend = TaskSyncBackend.__new__(TaskSyncBackend)
        gsettings = MagicMock()
        gsettings.get_boolean.return_value = True
        gsettings.get_string.side_effect = ['https://test.planio.de', 'CUSTOMER']

        result = backend.is_configured(gsettings)

        assert result is True

    def test_is_configured_disabled(self):
        """Not configured when planio-enabled is False."""
        from gtimelog.addons.tasks_sync_planio.models.sync_backend import TaskSyncBackend

        backend = TaskSyncBackend.__new__(TaskSyncBackend)
        gsettings = MagicMock()
        gsettings.get_boolean.return_value = False

        result = backend.is_configured(gsettings)

        assert result is False

    def test_is_configured_missing_url(self):
        """Not configured when URL is empty."""
        from gtimelog.addons.tasks_sync_planio.models.sync_backend import TaskSyncBackend

        backend = TaskSyncBackend.__new__(TaskSyncBackend)
        gsettings = MagicMock()
        gsettings.get_boolean.return_value = True
        gsettings.get_string.side_effect = ['', 'CUSTOMER']  # Empty URL

        result = backend.is_configured(gsettings)

        assert result is False

    def test_is_configured_missing_customer(self):
        """Not configured when customer is empty."""
        from gtimelog.addons.tasks_sync_planio.models.sync_backend import TaskSyncBackend

        backend = TaskSyncBackend.__new__(TaskSyncBackend)
        gsettings = MagicMock()
        gsettings.get_boolean.return_value = True
        gsettings.get_string.side_effect = ['https://test.planio.de', '']  # Empty customer

        result = backend.is_configured(gsettings)

        assert result is False


class TestPlanioBackendShouldHandleRemoteSync(unittest.TestCase):
    """Test remote sync routing decision."""

    def test_should_handle_remote_sync_true(self):
        """Handle remote sync when sync://planio URL."""
        from gtimelog.addons.tasks_sync_planio.models.sync_backend import TaskSyncBackend

        backend = TaskSyncBackend.__new__(TaskSyncBackend)
        gsettings = MagicMock()

        # Make is_configured return True
        with patch.object(backend, 'is_configured', return_value=True):
            gsettings.get_boolean.return_value = True
            gsettings.get_string.return_value = 'sync://planio'

            result = backend.should_handle_remote_sync(gsettings)

            assert result is True

    def test_should_handle_remote_sync_false_not_configured(self):
        """Don't handle when not configured."""
        from gtimelog.addons.tasks_sync_planio.models.sync_backend import TaskSyncBackend

        backend = TaskSyncBackend.__new__(TaskSyncBackend)
        gsettings = MagicMock()

        with patch.object(backend, 'is_configured', return_value=False):
            result = backend.should_handle_remote_sync(gsettings)

            assert result is False

    def test_should_handle_remote_sync_false_other_url(self):
        """Don't handle when task-list-url is not sync://planio."""
        from gtimelog.addons.tasks_sync_planio.models.sync_backend import TaskSyncBackend

        backend = TaskSyncBackend.__new__(TaskSyncBackend)
        gsettings = MagicMock()

        with patch.object(backend, 'is_configured', return_value=True):
            gsettings.get_boolean.return_value = True
            gsettings.get_string.return_value = 'sync://other'

            result = backend.should_handle_remote_sync(gsettings)

            assert result is False


class TestPlanioBackendErrorTracking(unittest.TestCase):
    """Test error and count tracking."""

    def test_get_last_error_empty(self):
        """Get last error returns empty initially."""
        from gtimelog.addons.tasks_sync_planio.models.sync_backend import TaskSyncBackend

        backend = TaskSyncBackend()

        result = backend.get_last_error()

        assert result == ''

    def test_get_last_count_zero(self):
        """Get last count returns zero initially."""
        from gtimelog.addons.tasks_sync_planio.models.sync_backend import TaskSyncBackend

        backend = TaskSyncBackend()

        result = backend.get_last_count()

        assert result == 0

    def test_set_last_error(self):
        """Last error can be set via sync failure."""
        from gtimelog.addons.tasks_sync_planio.models.sync_backend import TaskSyncBackend

        backend = TaskSyncBackend()
        backend._last_error = 'Connection timeout'
        backend._last_count = 0

        assert backend.get_last_error() == 'Connection timeout'
        assert backend.get_last_count() == 0


class TestPlanioBackendSyncMissingAPIKey(unittest.TestCase):
    """Test sync behavior when API key is missing."""

    def test_sync_missing_api_key_returns_none(self):
        """Sync returns None when API key is missing."""
        from gtimelog.addons.tasks_sync_planio.models.sync_backend import TaskSyncBackend

        backend = TaskSyncBackend()
        gsettings = MagicMock()
        settings_service = MagicMock()

        gsettings.get_string.side_effect = ['https://test.planio.de', 'CUST', '', '', '']
        gsettings.get_boolean.return_value = False

        mock_secrets = MagicMock()
        mock_secrets.get_api_key.return_value = None  # No API key

        with patch('gtimelog.addons.tasks_sync_planio.models.sync_backend.component_registry') as mock_registry:
            mock_registry.get.return_value = MagicMock(return_value=mock_secrets)

            result = backend.sync(gsettings, settings_service)

            assert result is None
            assert backend._last_error == 'Missing Planio API key in Secret Service.'
            assert backend._last_count == 0

    def test_sync_missing_api_key_sets_error(self):
        """Sync sets error message when API key missing."""
        from gtimelog.addons.tasks_sync_planio.models.sync_backend import TaskSyncBackend

        backend = TaskSyncBackend()
        gsettings = MagicMock()
        settings_service = MagicMock()

        gsettings.get_string.side_effect = ['https://test.planio.de', 'CUST', '', '', '']
        gsettings.get_boolean.return_value = False

        mock_secrets = MagicMock()
        mock_secrets.get_api_key.return_value = ''  # Empty API key

        with patch('gtimelog.addons.tasks_sync_planio.models.sync_backend.component_registry') as mock_registry:
            mock_registry.get.return_value = MagicMock(return_value=mock_secrets)

            backend.sync(gsettings, settings_service)

            assert 'Missing Planio API key' in backend._last_error


class TestPlanioBackendSyncAPIError(unittest.TestCase):
    """Test sync behavior when API call fails."""

    def test_sync_fetch_issues_exception_returns_none(self):
        """Sync returns None when fetch_issues raises exception."""
        from gtimelog.addons.tasks_sync_planio.models.sync_backend import TaskSyncBackend

        backend = TaskSyncBackend()
        gsettings = MagicMock()
        settings_service = MagicMock()

        gsettings.get_string.side_effect = ['https://test.planio.de', 'CUST', '', '', '']
        gsettings.get_boolean.return_value = False

        mock_secrets = MagicMock()
        mock_secrets.get_api_key.return_value = 'test_key'

        with patch('gtimelog.addons.tasks_sync_planio.models.sync_backend.component_registry') as mock_registry:
            mock_registry.get.return_value = MagicMock(return_value=mock_secrets)

            with patch('gtimelog.addons.tasks_sync_planio.models.sync_backend.PlanioClient') as MockClient:
                client_instance = MagicMock()
                client_instance.fetch_issues.side_effect = RuntimeError('API error')
                MockClient.return_value = client_instance

                result = backend.sync(gsettings, settings_service)

                assert result is None
                assert backend._last_count == 0
                assert 'API error' in backend._last_error
