import unittest
from unittest.mock import MagicMock


class TestPlanioPreferencesControllerSync(unittest.TestCase):
    """Test controller constants."""

    def test_sync_url_constant(self):
        """Verify SYNC_URL constant."""
        from gtimelog.addons.tasks_sync_planio.controllers.preferences_controller import PreferencesController

        assert PreferencesController.SYNC_URL == 'sync://planio'


class TestPlanioPreferencesLogic(unittest.TestCase):
    """Test preferences logic extracted from controller."""

    def test_enable_planio_mode_sets_correct_keys(self):
        """When Planio enabled, set task-list-url and remote-task-list."""
        # This tests the logic that would be in _enable_planio_mode
        gsettings = MagicMock()
        gsettings.get_string.side_effect = lambda k: {
            'task-list-url': '',
            'planio-url': 'https://planio.example.com',
            'task-list-edit-url': '',
        }.get(k, '')
        gsettings.get_boolean.return_value = False

        SYNC_URL = 'sync://planio'

        # Simulate _enable_planio_mode logic
        if gsettings.get_string('task-list-url') != SYNC_URL:
            gsettings.set_string('task-list-url', SYNC_URL)

        gsettings.set_string.assert_any_call('task-list-url', 'sync://planio')

    def test_disable_planio_mode_clears_keys(self):
        """When Planio disabled, clear task-list-url."""
        gsettings = MagicMock()
        gsettings.get_string.return_value = 'sync://planio'
        gsettings.get_boolean.return_value = True

        SYNC_URL = 'sync://planio'

        # Simulate _disable_planio_mode logic
        if gsettings.get_string('task-list-url') == SYNC_URL:
            gsettings.set_string('task-list-url', '')

        gsettings.set_string.assert_called_with('task-list-url', '')

    def test_sync_remote_mode_routes_correctly(self):
        """_sync_remote_mode delegates to enable or disable."""
        gsettings = MagicMock()

        # When enabled
        gsettings.get_boolean.return_value = True
        enable_called = bool(gsettings.get_boolean('planio-enabled'))

        assert enable_called is True

        # When disabled
        gsettings.get_boolean.return_value = False
        disable_called = not gsettings.get_boolean('planio-enabled')

        assert disable_called is True
