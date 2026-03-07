from gtimelog.models import Service, component_registry


class TasksApplicationService(Service):
    """Application service for task list workflows."""

    _name = 'application.tasks.service'

    def __init__(self, domain_policy=None):
        self.domain_policy = domain_policy or component_registry.get('domain.tasks.policy')()

    @staticmethod
    def is_remote_task_list(gsettings):
        """Return True when tasks source is configured as remote."""
        return gsettings.get_boolean('remote-task-list')

    @staticmethod
    def task_list_url(gsettings):
        """Return configured remote task URL."""
        return gsettings.get_string('task-list-url')

    @staticmethod
    def task_list_edit_url(gsettings):
        """Return configured remote task editor URL."""
        return gsettings.get_string('task-list-edit-url')

    def can_edit_tasks(self, gsettings):
        """Return whether edit-tasks UI action should be enabled."""
        return self.domain_policy.can_edit_tasks(
            self.is_remote_task_list(gsettings),
            self.task_list_edit_url(gsettings),
        )

    def should_download_tasks(self, gsettings):
        """Return whether remote download should run."""
        return self.domain_policy.should_download_tasks(self.task_list_url(gsettings))

    def should_trigger_remote_refresh(self, gsettings):
        """Return whether refresh action should trigger remote download."""
        return self.domain_policy.should_trigger_remote_refresh(self.is_remote_task_list(gsettings))

    def should_download_after_remote_edit(self, editing_remote_tasks):
        """Return whether focus recovery should refresh remote tasks."""
        return self.domain_policy.should_download_after_remote_edit(editing_remote_tasks)

    def get_tasks_filename(self, gsettings, settings_service):
        """Return the active task list filename (cache or local)."""
        if self.is_remote_task_list(gsettings):
            return settings_service.get_task_list_cache_file()
        return settings_service.get_task_list_file()
