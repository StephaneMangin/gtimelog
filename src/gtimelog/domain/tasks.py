from gtimelog.models import Service


class TasksDomainPolicy(Service):
    """Domain policy for task list behavior decisions."""

    _name = 'domain.tasks.policy'

    @staticmethod
    def can_edit_tasks(remote_task_list, edit_url):
        """Return whether task list editing should be enabled."""
        if remote_task_list:
            return bool(edit_url)
        return True

    @staticmethod
    def should_download_tasks(task_list_url):
        """Return True when remote task download should run."""
        return bool(task_list_url)

    @staticmethod
    def should_trigger_remote_refresh(remote_task_list):
        """Return True when refresh action should trigger remote download."""
        return bool(remote_task_list)

    @staticmethod
    def should_download_after_remote_edit(editing_remote_tasks):
        """Return True when refocusing should refresh remote tasks."""
        return bool(editing_remote_tasks)
