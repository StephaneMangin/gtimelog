from dataclasses import dataclass


@dataclass
class SyncTask:
    """Normalized task payload used by all sync providers."""

    id: int
    project_name: str
    category: str
    subject: str
    status: str
    description: str

    def render(self, template: str) -> str:
        """Render a generic task line using the configured provider template."""
        return (
            template.format(
                id=self.id,
                project_name=self.project_name,
                category=self.category,
                subject=self.subject,
                status=self.status,
                description=self.description,
            )
            + '\n'
        )
