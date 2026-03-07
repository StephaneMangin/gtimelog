from gtimelog.models import Service


class ReportsApplicationService(Service):
    """Addon-level extension point for report application service."""

    _inherit = 'application.reports.service'
    OVERRIDE_SOURCE = 'reports-addon-application'

    def build_customer_tree(self, work_entries):
        return super().build_customer_tree(work_entries)
