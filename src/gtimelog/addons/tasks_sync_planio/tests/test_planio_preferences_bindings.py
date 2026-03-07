import unittest


class TestPlanioPreferencesConstantAndInit(unittest.TestCase):
    """Test constants and basic initialization."""

    def test_sync_url_constant(self):
        """SYNC_URL constant is correct."""
        from gtimelog.addons.tasks_sync_planio.controllers.preferences_controller import PreferencesController

        assert PreferencesController.SYNC_URL == 'sync://planio'

    def test_controller_inherits_prefs_controller(self):
        """Controller inherits from prefs.controller."""
        from gtimelog.addons.tasks_sync_planio.controllers.preferences_controller import PreferencesController

        assert PreferencesController._inherit == 'prefs.controller'
