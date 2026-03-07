"""Extend report styles service to add 'performance' style."""

from gtimelog.models import Service


class ReportStylesService(Service):
    """Add performance style to available report styles."""

    _inherit = 'reports.styles.service'

    def get_available_styles(self):
        """Add 'performance' to available styles."""
        styles = super().get_available_styles()
        styles.append('performance')
        return styles
