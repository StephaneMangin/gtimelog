import os
import sys
import textwrap
import time
import unittest

from gtimelog.addons.base.tests.common import Mixins
from gtimelog.addons.tasks.models.tasklist import TaskList
from gtimelog.addons.timelog.models import TimeCollection


class TestTaskList(Mixins, unittest.TestCase):
    def test_missing_file(self):
        tasklist = TaskList('/nosuchfile')
        assert not tasklist.check_reload()
        tasklist.reload()  # no crash

    def test_parsing_and_ordering(self):
        taskfile = self.write_file(
            'tasks.txt',
            textwrap.dedent("""\
            # comments are skipped
            some task
            other task
            project: do it
            project:fix bugs
            misc: paperwork
        """),
        )
        tasklist = TaskList(taskfile)
        assert tasklist.groups == [
            ('project', ['do it', 'fix bugs']),
            ('misc', ['paperwork']),
            ('Other', ['some task', 'other task']),
        ]
        # also test that the order function works as foreseen
        assert tasklist.order('project: fix bugs') == 4
        assert tasklist.order('unknown task') == sys.maxsize

    def test_unicode(self):
        taskfile = self.write_file('tasks.txt', '\N{SNOWMAN}')
        tasklist = TaskList(taskfile)
        assert tasklist.groups == [('Other', ['☃'])]

    def test_reloading(self):
        taskfile = self.write_file('tasks.txt', 'some tasks\n')
        couple_seconds_ago = time.time() - 2
        os.utime(taskfile, (couple_seconds_ago, couple_seconds_ago))

        tasklist = TaskList(taskfile)
        assert tasklist.groups == [('Other', ['some tasks'])]
        assert not tasklist.check_reload()

        with open(taskfile, 'w') as f:
            f.write('new tasks\n')

        assert tasklist.check_reload()

        assert tasklist.groups == [('Other', ['new tasks'])]

    def test_merge_with(self):
        """Test merging two task lists."""
        # Create first task list (local)
        local_file = self.write_file(
            'local-tasks.txt',
            textwrap.dedent("""\
            Project1: local task 1
            Project1: local task 2
            Local task without group
            Project2: local project2 task
        """),
        )
        local_tasks = TaskList(local_file)

        # Create second task list (remote)
        remote_file = self.write_file(
            'remote-tasks.txt',
            textwrap.dedent("""\
            Project1: remote task 1
            Project2: remote project2 task
            Project3: new remote project
            Local task without group
            Remote task without group
        """),
        )
        remote_tasks = TaskList(remote_file)

        # Merge remote into local
        local_tasks.merge_with(remote_tasks)

        # Verify merged result
        groups_dict = dict(local_tasks.groups)

        # Project1 should have both local and remote tasks
        assert 'Project1' in groups_dict
        assert 'local task 1' in groups_dict['Project1']
        assert 'local task 2' in groups_dict['Project1']
        assert 'remote task 1' in groups_dict['Project1']

        # Project2 should have both local and remote tasks
        assert 'Project2' in groups_dict
        assert 'local project2 task' in groups_dict['Project2']
        assert 'remote project2 task' in groups_dict['Project2']

        # New project from remote should be added
        assert 'Project3' in groups_dict
        assert 'new remote project' in groups_dict['Project3']

        # Other group should have both tasks, but duplicate should appear only once
        assert 'Other' in groups_dict
        assert 'Local task without group' in groups_dict['Other']
        assert 'Remote task without group' in groups_dict['Other']
        assert groups_dict['Other'].count('Local task without group') == 1


class TestSortedGroupedWithTaskList(Mixins, unittest.TestCase):
    def test_sorted_grouped_time_collection(self):
        unsorted_list = (
            (10_000, 'BBB: b', 20),
            (30_000, 'CCC: c', 10),
            (20_000, 'Alone', 12),
            (40_000, 'AAA: a', 15),
        )
        taskfile = self.write_file(
            'tasks.txt',
            textwrap.dedent("""\
            Alone
            # comments are skipped
            BBB: b
            AAA: a
            CCC: c
        """),
        )
        tasklist = TaskList(taskfile)
        sorted_by = {
            'start-time': ('BBB: b', 'Alone', 'CCC: c', 'AAA: a'),
            'name': ('AAA: a', 'Alone', 'BBB: b', 'CCC: c'),
            'duration': ('CCC: c', 'Alone', 'AAA: a', 'BBB: b'),
            'task-list': ('Alone', 'BBB: b', 'AAA: a', 'CCC: c'),
        }

        def tc_sorted(method):
            tc_key = TimeCollection._get_grouped_order_key
            return tuple(name for start_time, name, duration in sorted(unsorted_list, key=tc_key(method, tasklist)))

        assert tc_sorted('start-time') == sorted_by['start-time']
        assert tc_sorted('name') == sorted_by['name']
        assert tc_sorted('duration') == sorted_by['duration']
        assert tc_sorted('task-list') == sorted_by['task-list']
