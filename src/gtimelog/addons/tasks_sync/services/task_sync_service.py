import logging
from datetime import datetime, timezone

from gtimelog.models import Service

from ..models.sync_storage import TaskSyncStorage

log = logging.getLogger('gtimelog.tasks_sync')


class TaskSyncService(Service):
    """Trigger synchronization using the active provider backend."""

    _name = 'application.tasks.sync.service'

    def __init__(self, backend=None):
        self.backend = backend or self.env.get('tasks.sync.backend')

    def should_handle_remote_sync(self, gsettings):
        """Return whether provider should replace default remote download behavior."""
        return self.backend.should_handle_remote_sync(gsettings)

    def sync_now(self, gsettings):
        """Run backend sync and persist provider payload."""
        settings_cls = self.env['settings']
        settings_service = settings_cls()

        if not self.backend.is_configured(gsettings):
            self._set_sync_state(gsettings, False, 'Synchronization is not configured.')
            return False

        try:
            payload = self.backend.sync(gsettings, settings_service)
        except Exception as exc:
            # Keep UI responsive if provider dependency/import fails at runtime.
            message = str(exc) or 'Synchronization failed.'
            log.warning('Task synchronization failed: %s', message)
            self._set_sync_state(gsettings, False, message)
            return False

        if payload is None:
            message = self.backend.get_last_error() or 'Synchronization failed.'
            self._set_sync_state(gsettings, False, message)
            return False

        TaskSyncStorage(payload.filename).update_file(payload.tasks, payload.customer_name, payload.task_format)
        count = self.backend.get_last_count() or len(payload.tasks)
        self._set_sync_state(gsettings, True, f'Success: synchronized {count} tasks.')
        log.info('Task sync completed: %d tasks written to %s', len(payload.tasks), payload.filename)
        return True

    @staticmethod
    def _set_sync_state(gsettings, success: bool, message: str):
        """Persist sync state for task synchronization status display."""
        gsettings.set_boolean('last-sync-success', bool(success))
        gsettings.set_string('last-sync-message', message)
        gsettings.set_string('last-sync-at', datetime.now(timezone.utc).isoformat())
