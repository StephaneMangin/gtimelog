import json
import tempfile
import unittest
from pathlib import Path

from gtimelog.addons.tasks_sync_planio.models.planio_project_mapping import PlanioProjectMapping


class TestPlanioProjectMapping(unittest.TestCase):
    """Unit tests for Planio mapping JSON persistence."""

    def test_ensure_mapping_creates_default_conversion_entry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = Path(tmpdir) / 'projects_mapping.json'
            mapping = PlanioProjectMapping(str(filename))
            result = mapping.ensure_mapping('My Planio Project')

            assert result == 'My Planio Project - A CONVERTIR'
            saved = json.loads(filename.read_text(encoding='utf-8'))
            assert saved == [{'planio_name': 'My Planio Project', 'odoo_name': 'My Planio Project - A CONVERTIR'}]

    def test_ensure_mapping_reuses_existing_value(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = Path(tmpdir) / 'projects_mapping.json'
            filename.write_text(
                json.dumps([{'planio_name': 'Project A', 'odoo_name': 'Mapped Project A'}]),
                encoding='utf-8',
            )

            mapping = PlanioProjectMapping(str(filename))
            assert mapping.ensure_mapping('Project A') == 'Mapped Project A'
