from gtimelog.models import Service, component_registry


class ReportsApplicationService(Service):
    """Application service for report preparation workflows."""

    _name = 'application.reports.service'

    def __init__(self, domain_service=None):
        self.domain_service = domain_service or component_registry.get('domain.reports.service')()

    def parse_entry_line(self, entry):
        """Parse one entry line to structured report fields."""
        return self.domain_service.parse_entry_line(entry)

    def build_customer_tree(self, work_entries):
        """Build structured customer/project/category/task tree."""
        return self.domain_service.build_customer_tree(work_entries)

    def render_customer_tree(self, output, customer_tree):
        """Render structured customer tree to output."""
        return self.domain_service.render_customer_tree(output, customer_tree)
