import logging

from gtimelog.models import Controller

log = logging.getLogger('gtimelog.addons.base')


class Exports(Controller):
    """Base class for export functionality.

    Child addons inherit from this class and provide their own export behavior.
    The base class does not define or assume any concrete export method names.
    It only exposes shared data-access helpers through the window object.

    Each child addon remains responsible for implementing the export API
    that matches its own format and feature set.
    """

    _name = 'exports'

    def __init__(self, window):
        """Initialize exporter with window context.

        Args:
            window: Window-like object exposing export data providers used by
                   helper methods in this base class.

                   Expected optional attributes/callables:
                   - all_entries(): iterable of entry tuples
                   - grouped_entries(): grouped work/slack entries
                   - date: current date in view
                   - time_range: tuple of (start_date, end_date)
        """
        self.window = window

    # ========================================================================
    # Helper methods available to all export implementations
    # ========================================================================

    def get_all_entries(self) -> list:
        """Helper: Get all time log entries in the current view.

        Returns:
            List of (start, stop, duration, tags, entry) tuples from window.
        """
        if hasattr(self.window, 'all_entries') and callable(self.window.all_entries):
            return list(self.window.all_entries())
        return []

    def get_grouped_entries(self) -> tuple[list, list]:
        """Helper: Get entries grouped into work and slack.

        Returns:
            Tuple of (work_entries, slack_entries) lists.
        """
        if hasattr(self.window, 'grouped_entries') and callable(self.window.grouped_entries):
            return self.window.grouped_entries()
        return [], []

    def get_current_date(self):
        """Helper: Get the current date in the UI view.

        Returns:
            datetime.date object or None.
        """
        return getattr(self.window, 'date', None)

    def get_time_range(self) -> tuple | None:
        """Helper: Get the current time range in the UI view.

        Returns:
            Tuple of (start_date, end_date) or None.
        """
        return getattr(self.window, 'time_range', None)
