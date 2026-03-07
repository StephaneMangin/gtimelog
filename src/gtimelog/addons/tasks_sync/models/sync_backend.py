from gtimelog.models import Service


class TaskSyncBackend(Service):
    """Base backend API implemented by provider-specific addons."""

    _name = 'tasks.sync.backend'

    def is_configured(self, gsettings):
        """Return True when provider settings allow synchronization."""
        return False

    def should_handle_remote_sync(self, gsettings):
        """Return True when this backend should replace remote URL downloads."""
        return False

    def get_last_error(self):
        """Return backend-specific error details for latest run, if any."""
        return ''

    def get_last_count(self):
        """Return number of synchronized tasks for latest successful run."""
        return 0

    def sync(self, gsettings, settings_service):
        """Return a SyncPayload to persist or None when sync is skipped."""
        raise NotImplementedError('Sync backend is not implemented.')
