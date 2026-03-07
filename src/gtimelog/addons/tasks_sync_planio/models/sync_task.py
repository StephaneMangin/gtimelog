from dataclasses import dataclass
from typing import ClassVar

from gtimelog.addons.tasks_sync.models.sync_task import SyncTask as BaseSyncTask


@dataclass
class SyncTask(BaseSyncTask):
    """Planio extension of generic SyncTask with provider-specific fields."""

    customer_name: str
    project_short: str
    work_package: str

    STATUS_ICONS: ClassVar[dict[str, str]] = {
        'New': '!',
        'Confirmed': '*',
        'In Progress': '>',
        'Code Review': '?',
        'Resolved': '~',
        'QA ok': '+',
        'Closed': '#',
    }

    def render(self, template: str) -> str:
        """Render a Planio task line using Planio placeholders."""
        status_icon = self.STATUS_ICONS.get(self.status, '')
        category = self.category.lower() if self.work_package else self.category
        work_package = f'{self.work_package.capitalize()} - ' if self.work_package else ''
        return (
            template.format(
                id=self.id,
                customer_name=self.customer_name,
                project_name=self.project_name,
                project_short=self.project_short,
                category=category,
                subject=self.subject,
                status=self.status,
                status_icon=status_icon,
                work_package=work_package,
                description=self.description,
            )
            + '\n'
        )
