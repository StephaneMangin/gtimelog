from urllib.parse import urlparse

from gtimelog.models import Service


class PlanioSecrets(Service):
    """Read and write Planio API keys from Secret Service."""

    _name = 'planio.secrets'

    USERNAME = 'planio-api-key'

    @staticmethod
    def _secret_module():
        """Return Secret module lazily so tests can run in headless environments."""
        from gtimelog import require_version

        require_version('Secret', '1')
        from gi.repository import Secret

        return Secret

    def _attrs_for_url(self, url: str):
        parsed = urlparse(url)
        host = parsed.hostname or ''
        scheme = parsed.scheme or 'https'
        port = parsed.port or (443 if scheme == 'https' else 80)
        return {
            'user': self.USERNAME,
            'server': host,
            'protocol': scheme,
            'port': str(port),
        }

    def get_api_key(self, url: str):
        """Return API key for a given Planio URL from keyring."""
        if not url:
            return ''
        try:
            secret = self._secret_module()
        except Exception:
            return ''
        schema = secret.get_schema(secret.SchemaType.COMPAT_NETWORK)
        return secret.password_lookup_sync(schema, self._attrs_for_url(url), None) or ''

    def set_api_key(self, url: str, api_key: str):
        """Store API key for a given Planio URL in keyring."""
        if not url:
            return
        try:
            secret = self._secret_module()
        except Exception:
            return
        schema = secret.get_schema(secret.SchemaType.COMPAT_NETWORK)
        attrs = self._attrs_for_url(url)
        label = f'{self.USERNAME}@{attrs["server"]}:{attrs["port"]}'
        secret.password_store_sync(
            schema,
            attrs,
            secret.COLLECTION_DEFAULT,
            label,
            api_key,
            None,
        )
