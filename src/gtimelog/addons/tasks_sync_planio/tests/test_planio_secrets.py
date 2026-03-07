import unittest


class TestPlanioSecretsConstants(unittest.TestCase):
    """Test constants."""

    def test_username_constant(self):
        """Verify username constant."""
        from gtimelog.addons.tasks_sync_planio.models.planio_secrets import PlanioSecrets

        assert PlanioSecrets.USERNAME == 'planio-api-key'


class TestPlanioSecretsAttributeGeneration(unittest.TestCase):
    """Test Secret Service attribute mapping from URL."""

    def test_attrs_for_https_url(self):
        """Generate attrs for https URL."""
        from gtimelog.addons.tasks_sync_planio.models.planio_secrets import PlanioSecrets

        secrets = PlanioSecrets()
        attrs = secrets._attrs_for_url('https://planio.example.com')

        assert attrs['server'] == 'planio.example.com'
        assert attrs['protocol'] == 'https'
        assert attrs['port'] == '443'
        assert attrs['user'] == 'planio-api-key'

    def test_attrs_for_http_url(self):
        """Generate attrs for http URL."""
        from gtimelog.addons.tasks_sync_planio.models.planio_secrets import PlanioSecrets

        secrets = PlanioSecrets()
        attrs = secrets._attrs_for_url('http://planio.example.com')

        assert attrs['protocol'] == 'http'
        assert attrs['port'] == '80'

    def test_attrs_for_custom_port(self):
        """Handle custom port in URL."""
        from gtimelog.addons.tasks_sync_planio.models.planio_secrets import PlanioSecrets

        secrets = PlanioSecrets()
        attrs = secrets._attrs_for_url('https://planio.example.com:8443')

        assert attrs['port'] == '8443'

    def test_attrs_for_empty_url(self):
        """Handle empty URL gracefully."""
        from gtimelog.addons.tasks_sync_planio.models.planio_secrets import PlanioSecrets

        secrets = PlanioSecrets()
        attrs = secrets._attrs_for_url('')

        assert attrs['server'] == ''
        assert attrs['protocol'] == 'https'  # default


class TestPlanioSecretsGetApiKey(unittest.TestCase):
    """Test API key retrieval."""

    def test_get_api_key_empty_url_returns_empty(self):
        """Return empty for empty URL."""
        from gtimelog.addons.tasks_sync_planio.models.planio_secrets import PlanioSecrets

        secrets = PlanioSecrets()
        result = secrets.get_api_key('')

        assert result == ''


class TestPlanioSecretsSetApiKey(unittest.TestCase):
    """Test API key storage."""

    def test_set_api_key_empty_url_returns_early(self):
        """Return early for empty URL without trying Secret Service."""
        from gtimelog.addons.tasks_sync_planio.models.planio_secrets import PlanioSecrets

        secrets = PlanioSecrets()
        # Should not raise
        secrets.set_api_key('', 'test-key')
