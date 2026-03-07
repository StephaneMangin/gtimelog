import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from gtimelog.addons.tasks_sync.models.sync_storage import TaskSyncStorage


@dataclass
class FakeTask:
    id: int
    body: str

    def render(self, _template: str):
        return self.body


class TestTaskSyncStorage(unittest.TestCase):
    """Unit tests for synchronization file persistence behavior."""

    def test_update_file_preserves_non_customer_lines(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = Path(tmpdir) / 'remote-tasks.txt'
            filename.write_text('OTHER: keep me\nACME: ASYNC keep\nACME: old line\n', encoding='utf-8')

            storage = TaskSyncStorage(str(filename))
            tasks = [FakeTask(2, 'ACME: new second\n'), FakeTask(1, 'ACME: new first\n')]
            storage.update_file(tasks, 'ACME', '{subject}')

            assert filename.read_text(encoding='utf-8') == (
                'OTHER: keep me\nACME: ASYNC keep\nACME: new first\nACME: new second\n'
            )
