import re

from gtimelog.models import Service


class EntryParser(Service):
    """Parse a raw timelog entry line into structured fields."""

    _name = 'platform.entry.parser'

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

    def parse(self, raw_entry):
        """Return parsed dict from one raw entry line; empty dict on failure."""
        if not raw_entry or not isinstance(raw_entry, str):
            return {}
        match = self.ENTRY_REGEX.match(raw_entry.strip())
        if not match:
            return {}
        return match.groupdict()
