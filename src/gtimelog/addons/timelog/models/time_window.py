from .time_collection import TimeCollection


class TimeWindow(TimeCollection):
    """A window into a time log."""

    _name = 'time.window'

    def __init__(self, original, min_timestamp, max_timestamp):
        super().__init__(original.virtual_midnight)
        self.min_timestamp = min_timestamp
        self.max_timestamp = max_timestamp
        self.items = [item for item in original.items if min_timestamp <= item[0] < max_timestamp]

    def __repr__(self):
        return f'<TimeWindow: {self.min_timestamp}..{self.max_timestamp}>'
