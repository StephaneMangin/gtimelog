import sys

from gtimelog.addons.base.models.time_utils import get_mtime
from gtimelog.models import Model


class TaskList(Model):
    """Task list.
    You can have a list of common tasks in a text file that looks like this
        Arrived **
        Reading mail
        Project1: do some task
        Project2: do some other task
        Project1: do yet another task
    These tasks are grouped by their common prefix (separated with ':').
    Tasks without a ':' are grouped under "Other".
    """

    _name = 'task.list'
    other_title = 'Other'
    loading_callback = None
    loaded_callback = None
    error_callback = None

    def __init__(self, filename):
        self.filename = filename
        self.load()

    def check_reload(self):
        mtime = get_mtime(self.filename)
        if mtime != self.last_mtime:
            self.load()
            return True
        return False

    def load(self):
        groups = {}
        task_order = {}
        others = []
        self.last_mtime = get_mtime(self.filename)
        try:
            with open(self.filename, encoding='utf-8') as f:
                for index, line in enumerate(f):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if ':' in line:
                        group, task = [s.strip() for s in line.split(':', 1)]
                        groups.setdefault(group, []).append(task)
                        task_order[group + ': ' + task] = index
                    else:
                        others.append(line)
                        task_order[line] = index
        except OSError:
            pass
        self.groups = list(groups.items())
        if others:
            self.groups.append((self.other_title, others))
        self.task_order = task_order

    def reload(self):
        self.load()

    def merge_with(self, other_tasklist):
        """Merge another TaskList into this one.

        Tasks from other_tasklist are appended after existing tasks.
        Duplicate tasks are skipped.

        Args:
            other_tasklist: TaskList instance to merge
        """
        if not other_tasklist or not hasattr(other_tasklist, 'groups'):
            return

        # Convert groups to dict for easier merging
        groups_dict = dict(self.groups) if self.groups else {}

        # Track existing tasks to avoid duplicates
        existing_tasks = set()
        for group_name, tasks in self.groups:
            for task in tasks:
                if group_name == self.other_title:
                    existing_tasks.add(task)
                else:
                    existing_tasks.add(f'{group_name}: {task}')

        # Merge groups from other tasklist
        max_order = max(self.task_order.values()) if self.task_order else 0

        for group_name, tasks in other_tasklist.groups:
            for task in tasks:
                # Build full task name for duplicate check
                full_task = task if group_name == self.other_title else f'{group_name}: {task}'

                # Skip duplicates
                if full_task in existing_tasks:
                    continue

                # Add task to group
                if group_name not in groups_dict:
                    groups_dict[group_name] = []
                groups_dict[group_name].append(task)

                # Update order
                max_order += 1
                self.task_order[full_task] = max_order

        # Rebuild groups list
        self.groups = list(groups_dict.items())

    def order(self, value):
        return self.task_order.get(value, sys.maxsize)
