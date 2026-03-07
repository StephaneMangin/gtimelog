"""Service to manage available report styles based on loaded addons."""

from gtimelog.models import Service


class ReportStylesService(Service):
    """Provides the list of available report styles based on loaded addons."""

    _name = 'reports.styles.service'

    def get_available_styles(self):
        """Return list of available report styles.
        
        Child addons can extend this method to add their own styles.
        
        Returns:
            list: List of style names
        """
        return ['plain']

