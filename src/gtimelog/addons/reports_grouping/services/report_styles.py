"""Extend report styles service to add 'categorized' style."""

from gtimelog.models import Service


class ReportStylesService(Service):
    """Add categorized style to available report styles."""

    _inherit = 'reports.styles.service'

    def get_available_styles(self):
        """Add 'categorized' to available styles."""
        styles = super().get_available_styles()
        styles.append('categorized')
        return styles
