from gtimelog.models import Service


class TasksDomainPolicy(Service):
    """Addon-level extension point for task domain policy."""

    _inherit = 'domain.tasks.policy'
    OVERRIDE_SOURCE = 'tasks-addon-domain'
