class PlanioClient:
    """Fetch issues from Planio using optional project and category filters."""

    def __init__(
        self,
        url: str,
        api_key: str,
        project_filter: str,
        category_filter: str,
        exclude_resolved: bool,
    ):
        try:
            from redminelib import Redmine
        except ImportError as exc:
            raise RuntimeError('redminelib is required for Planio synchronization.') from exc

        self.redmine = Redmine(url, key=api_key)
        self.project_filter = project_filter
        self.category_filter = category_filter
        self.exclude_resolved = exclude_resolved
        self._filters = {}

        if project_filter:
            self._filters['project_id'] = int(project_filter) if project_filter.isdigit() else project_filter

        if category_filter and category_filter.isdigit():
            self._filters['category_id'] = int(category_filter)

    def fetch_issues(self):
        """Fetch assigned issues unless explicit project/category filters are set."""
        if self.project_filter or self.category_filter:
            return self._fetch_filtered_issues()

        filters = dict(self._filters)
        filters['assigned_to_id'] = 'me'
        issues = self.redmine.issue.filter(**filters)
        return self._post_filter(issues)

    def _fetch_filtered_issues(self):
        issues = self.redmine.issue.filter(**self._filters)
        return self._post_filter(issues)

    def _post_filter(self, issues):
        if self.category_filter and not self.category_filter.isdigit():
            issues = [
                issue
                for issue in issues
                if hasattr(issue, 'category') and getattr(issue.category, 'name', None) == self.category_filter
            ]
        if self.exclude_resolved:
            issues = [issue for issue in issues if getattr(issue.status, 'name', '') not in ['New', 'Closed', 'QA ok']]
        return issues

    @staticmethod
    def get_custom_field(issue, field_name: str) -> str:
        """Extract a custom field by name from a redmine issue."""
        if not hasattr(issue, 'custom_fields'):
            return ''
        for field in issue.custom_fields:
            if getattr(field, 'name', None) == field_name:
                return field.value
        return ''
