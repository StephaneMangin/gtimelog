from gtimelog.models import Service


class TasksApplicationService(Service):
    """Addon-level extension point for task application service."""

    _inherit = 'application.tasks.service'
    OVERRIDE_SOURCE = 'tasks-addon-application'
