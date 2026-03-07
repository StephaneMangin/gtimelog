from gtimelog.models import Service


class ReportsDomainService(Service):
    """Addon-level extension point for report domain service."""

    _inherit = 'domain.reports.service'
    OVERRIDE_SOURCE = 'reports-addon-domain'

    def parse_entry_line(self, entry):
        return super().parse_entry_line(entry)
