import re

from gtimelog.models import Model


class Entry(Model):
    """
    Represents a single time log entry, handling parsing of the entry string.
    This object is iterable for backward compatibility with tuple unpacking.
    """

    _name = 'entry'
    # Regex pattern for parsing time log entries
    # Format: Customer: [REF] Project / Phase -> #123 Task title / comment
    # The -> and everything after it is optional
    # Groups: customer, ref, project, phase, task, title, comment
    ENTRY_REGEX = re.compile(
        r'^(?:\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\s*)?'
        r'(?P<customer>[^:]+):\s*'
        r'(?:\[(?P<ref>[^\]]+)\]\s*)?'
        r'(?P<project>.+?)'
        r'(?:\s*/\s*(?P<phase>[^/]+?))?'
        r'(?:'
        r'\s*->\s*'
        r'(?:#(?P<task>\d+)\s+)?'
        r'(?P<title>[^/]+?)'
        r'(?:\s*/\s*(?P<comment>.+?))?'
        r')?\s*$'
    )

    def __init__(self, start, stop, duration, tags, entry):
        self.start = start
        self.stop = stop
        self.duration = duration
        self.tags = tags
        self.entry = entry  # Raw entry string
        self._parsed_data = self._parse()

    def _parse(self):
        """Parse the entry string and return the parsed data."""
        match = self.ENTRY_REGEX.match(self.entry.strip())
        if match:
            return match.groupdict()
        return {}  # Return empty dict if no match

    @property
    def customer(self):
        """The customer part of the entry."""
        return self._parsed_data.get('customer')

    @property
    def ref(self):
        """The reference part of the entry."""
        return self._parsed_data.get('ref')

    @property
    def project(self):
        """The project part of the entry."""
        return self._parsed_data.get('project')

    @property
    def phase(self):
        """The phase part of the entry."""
        return self._parsed_data.get('phase')

    @property
    def task(self):
        """The task number part of the entry."""
        return self._parsed_data.get('task')

    @property
    def title(self):
        """The title part of the entry."""
        return self._parsed_data.get('title')

    @property
    def comment(self):
        """The comment part of the entry."""
        return self._parsed_data.get('comment')

    def __repr__(self):
        return f"Entry(start={self.start}, stop={self.stop}, entry='{self.entry}')"

    def __iter__(self):
        """Allow unpacking for backward compatibility."""
        return iter((self.start, self.stop, self.duration, self.tags, self.entry))
