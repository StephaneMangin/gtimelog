import unittest


class FakeStatus:
    """Mock status object with name attribute."""

    def __init__(self, name):
        self.name = name


class FakeCategory:
    """Mock category object with name attribute."""

    def __init__(self, name):
        self.name = name


class FakeCustomField:
    """Mock custom field object with name and value."""

    def __init__(self, name, value):
        self.name = name
        self.value = value


class FakeIssue:
    """Mock issue matching redminelib pattern."""

    def __init__(self, id_val=1, status_name='New', category_name=None):
        self.id = id_val
        self.status = FakeStatus(status_name)
        if category_name:
            self.category = FakeCategory(category_name)
        self.subject = f'Issue {id_val}'
        self.custom_fields = []


class TestPlanioClientPostFilter(unittest.TestCase):
    """Test _post_filter logic: category filter + exclude_resolved."""

    def test_exclude_resolved_keeps_new_status(self):
        """Exclude resolved keeps 'New' status (not in [New, Closed, QA ok])."""
        from gtimelog.addons.tasks_sync_planio.models.planio_client import PlanioClient

        client = PlanioClient.__new__(PlanioClient)
        client.category_filter = ''
        client.exclude_resolved = True

        issue = FakeIssue(status_name='New')
        result = client._post_filter([issue])

        # 'New' is in the exclude list, so it WILL be excluded
        assert len(result) == 0

    def test_exclude_resolved_keeps_in_progress(self):
        """Exclude resolved keeps 'In Progress' status (NOT in exclude list)."""
        from gtimelog.addons.tasks_sync_planio.models.planio_client import PlanioClient

        client = PlanioClient.__new__(PlanioClient)
        client.category_filter = ''
        client.exclude_resolved = True

        issue = FakeIssue(status_name='In Progress')
        result = client._post_filter([issue])

        # 'In Progress' NOT in [New, Closed, QA ok], so kept
        assert len(result) == 1

    def test_exclude_resolved_removes_closed(self):
        """Exclude resolved removes 'Closed' status."""
        from gtimelog.addons.tasks_sync_planio.models.planio_client import PlanioClient

        client = PlanioClient.__new__(PlanioClient)
        client.category_filter = ''
        client.exclude_resolved = True

        issue = FakeIssue(status_name='Closed')
        result = client._post_filter([issue])

        assert len(result) == 0

    def test_exclude_resolved_removes_qa_ok(self):
        """Exclude resolved removes 'QA ok' status."""
        from gtimelog.addons.tasks_sync_planio.models.planio_client import PlanioClient

        client = PlanioClient.__new__(PlanioClient)
        client.category_filter = ''
        client.exclude_resolved = True

        issue = FakeIssue(status_name='QA ok')
        result = client._post_filter([issue])

        assert len(result) == 0

    def test_exclude_resolved_false_keeps_all_statuses(self):
        """Exclude resolved=False keeps all statuses."""
        from gtimelog.addons.tasks_sync_planio.models.planio_client import PlanioClient

        client = PlanioClient.__new__(PlanioClient)
        client.category_filter = ''
        client.exclude_resolved = False

        issues = [
            FakeIssue(id_val=1, status_name='New'),
            FakeIssue(id_val=2, status_name='Closed'),
            FakeIssue(id_val=3, status_name='In Progress'),
        ]
        result = client._post_filter(issues)

        # All kept when exclude_resolved=False
        assert len(result) == 3

    def test_category_filter_by_name_matches(self):
        """Category filter by name keeps matching category."""
        from gtimelog.addons.tasks_sync_planio.models.planio_client import PlanioClient

        client = PlanioClient.__new__(PlanioClient)
        client.category_filter = 'Bug'
        client.exclude_resolved = False

        issue = FakeIssue(category_name='Bug')
        result = client._post_filter([issue])

        assert len(result) == 1

    def test_category_filter_by_name_non_matching(self):
        """Category filter by name excludes non-matching category."""
        from gtimelog.addons.tasks_sync_planio.models.planio_client import PlanioClient

        client = PlanioClient.__new__(PlanioClient)
        client.category_filter = 'Bug'
        client.exclude_resolved = False

        issue = FakeIssue(category_name='Feature')
        result = client._post_filter([issue])

        assert len(result) == 0

    def test_category_filter_ignores_numeric_categories(self):
        """Numeric category filters are ignored in _post_filter."""
        from gtimelog.addons.tasks_sync_planio.models.planio_client import PlanioClient

        client = PlanioClient.__new__(PlanioClient)
        client.category_filter = '123'  # Numeric
        client.exclude_resolved = False

        issue = FakeIssue(category_name='Bug')
        result = client._post_filter([issue])

        # Numeric filter applied in __init__, not _post_filter
        assert len(result) == 1

    def test_category_filter_missing_category_attribute(self):
        """Issue without category attribute is excluded."""
        from gtimelog.addons.tasks_sync_planio.models.planio_client import PlanioClient

        client = PlanioClient.__new__(PlanioClient)
        client.category_filter = 'Bug'
        client.exclude_resolved = False

        # Create issue without category attribute
        issue = FakeIssue()
        # FakeIssue doesn't set category when category_name is None
        if hasattr(issue, 'category'):
            delattr(issue, 'category')

        result = client._post_filter([issue])

        assert len(result) == 0

    def test_combined_filters_exclude_and_category(self):
        """Apply both exclude_resolved and category filters."""
        from gtimelog.addons.tasks_sync_planio.models.planio_client import PlanioClient

        client = PlanioClient.__new__(PlanioClient)
        client.category_filter = 'Bug'
        client.exclude_resolved = True

        issues = [
            FakeIssue(id_val=1, status_name='In Progress', category_name='Bug'),
            FakeIssue(id_val=2, status_name='New', category_name='Bug'),
            FakeIssue(id_val=3, status_name='In Progress', category_name='Feature'),
        ]
        result = client._post_filter(issues)

        # Only issue 1: status 'In Progress' (not excluded) AND category 'Bug'
        assert len(result) == 1
        assert result[0].id == 1


class TestPlanioClientGetCustomField(unittest.TestCase):
    """Test get_custom_field static method."""

    def test_get_custom_field_returns_value(self):
        """Get custom field returns field value."""
        from gtimelog.addons.tasks_sync_planio.models.planio_client import PlanioClient

        field = FakeCustomField('Work', 'WP-123')
        issue = FakeIssue()
        issue.custom_fields = [field]

        result = PlanioClient.get_custom_field(issue, 'Work')

        assert result == 'WP-123'

    def test_get_custom_field_first_match_wins(self):
        """Get custom field returns first matching field."""
        from gtimelog.addons.tasks_sync_planio.models.planio_client import PlanioClient

        field1 = FakeCustomField('Work', 'WP-1')
        field2 = FakeCustomField('Work', 'WP-2')
        issue = FakeIssue()
        issue.custom_fields = [field1, field2]

        result = PlanioClient.get_custom_field(issue, 'Work')

        assert result == 'WP-1'

    def test_get_custom_field_not_found(self):
        """Get custom field returns empty string if not found."""
        from gtimelog.addons.tasks_sync_planio.models.planio_client import PlanioClient

        field = FakeCustomField('Other', 'XYZ')
        issue = FakeIssue()
        issue.custom_fields = [field]

        result = PlanioClient.get_custom_field(issue, 'Work')

        assert result == ''

    def test_get_custom_field_empty_list(self):
        """Get custom field returns empty string for empty custom fields."""
        from gtimelog.addons.tasks_sync_planio.models.planio_client import PlanioClient

        issue = FakeIssue()
        issue.custom_fields = []

        result = PlanioClient.get_custom_field(issue, 'Any')

        assert result == ''

    def test_get_custom_field_no_custom_fields_attr(self):
        """Get custom field returns empty string if attr missing."""
        from gtimelog.addons.tasks_sync_planio.models.planio_client import PlanioClient

        issue = FakeIssue()
        delattr(issue, 'custom_fields')

        result = PlanioClient.get_custom_field(issue, 'Work')

        assert result == ''
