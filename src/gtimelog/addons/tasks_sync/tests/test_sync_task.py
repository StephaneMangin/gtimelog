import unittest

from gtimelog.addons.tasks_sync.models.sync_task import SyncTask


class TestSyncTaskRender(unittest.TestCase):
    """Validate generic SyncTask rendering placeholders."""

    def test_render_uses_generic_fields_only(self):
        task = SyncTask(
            id=7,
            project_name='Project X',
            category='Bug',
            subject='Fix issue',
            status='In Progress',
            description='Important fix',
        )

        rendered = task.render('{project_name} | {category} | {subject} | {status} | {description} | #{id}')

        assert rendered == 'Project X | Bug | Fix issue | In Progress | Important fix | #7\n'
