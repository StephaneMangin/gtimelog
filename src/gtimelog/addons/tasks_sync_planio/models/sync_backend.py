import logging

from gtimelog.addons.tasks_sync.models.sync_payload import SyncPayload
from gtimelog.models import Service

from .planio_client import PlanioClient
from .planio_project_mapping import PlanioProjectMapping
from .sync_task import SyncTask

log = logging.getLogger('gtimelog.tasks_sync.planio')


class TaskSyncBackend(Service):
    """Provider backend that pulls issues from Planio and emits SyncTask entries."""

    _inherit = 'tasks.sync.backend'

    def __init__(self):
        self._last_error = ''
        self._last_count = 0

    def get_last_error(self):
        return self._last_error

    def get_last_count(self):
        return self._last_count

    def is_configured(self, gsettings):
        """Return True when required Planio settings are available."""
        return bool(
            gsettings.get_boolean('planio-enabled')
            and gsettings.get_string('planio-url').strip()
            and gsettings.get_string('planio-customer').strip()
        )

    def should_handle_remote_sync(self, gsettings):
        """Route remote sync to Planio backend when URL scheme is sync://planio."""
        if not self.is_configured(gsettings):
            return False
        return gsettings.get_boolean('remote-task-list') and gsettings.get_string('task-list-url') == 'sync://planio'

    def sync(self, gsettings, settings_service):
        """Fetch issues, map them to SyncTask, and return persistence payload."""
        url = gsettings.get_string('planio-url').strip()
        customer_name = gsettings.get_string('planio-customer').strip()
        project_filter = gsettings.get_string('planio-project-filter').strip()
        category_filter = gsettings.get_string('planio-category-filter').strip()
        task_format = gsettings.get_string('planio-task-format').strip()
        exclude_resolved = gsettings.get_boolean('planio-exclude-resolved')

        secrets_cls = self.env['planio.secrets']
        api_key = secrets_cls().get_api_key(url)
        if not api_key:
            self._last_error = 'Missing Planio API key in Secret Service.'
            self._last_count = 0
            log.warning('Planio API key is missing in keyring, sync skipped.')
            return None

        client = PlanioClient(
            url=url,
            api_key=api_key,
            project_filter=project_filter,
            category_filter=category_filter,
            exclude_resolved=exclude_resolved,
        )
        try:
            issues = client.fetch_issues()
        except Exception as exc:
            self._last_error = str(exc) or 'Planio API request failed.'
            self._last_count = 0
            log.exception('Planio synchronization failed while fetching issues.')
            return None

        mapping = PlanioProjectMapping(settings_service.get_planio_project_mapping_file())
        tasks = [self._issue_to_sync_task(issue, mapping, customer_name, client) for issue in issues]
        self._last_error = ''
        self._last_count = len(tasks)

        return SyncPayload(
            tasks=tasks,
            filename=settings_service.get_planio_sync_cache_file(),
            customer_name=customer_name,
            task_format=task_format,
        )

    @staticmethod
    def _issue_to_sync_task(issue, mapping, customer_name: str, client: PlanioClient):
        project_name = getattr(issue.project, 'name', 'Unknown')
        odoo_project_name = mapping.ensure_mapping(project_name)
        category = getattr(getattr(issue, 'category', None), 'name', 'N/A')
        status = getattr(getattr(issue, 'status', None), 'name', '')
        return SyncTask(
            id=getattr(issue, 'id', 0),
            project_name=odoo_project_name,
            category=category,
            subject=getattr(issue, 'subject', ''),
            status=status,
            description=getattr(issue, 'description', ''),
            customer_name=customer_name,
            project_short=project_name.split(' ')[-1] if project_name else 'unknown',
            work_package=client.get_custom_field(issue, 'Work package'),
        )
