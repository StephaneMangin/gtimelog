from gtimelog.models import Service


class EntryParser(Service):
    """Addon-level extension point for platform entry parser."""

    _inherit = 'platform.entry.parser'
    OVERRIDE_SOURCE = 'reports-addon-platform'

    def parse(self, raw_entry):
        return super().parse(raw_entry)
