from gettext import gettext as _

from gi.repository import GObject, Gtk

from gtimelog.addons.base.helpers import mark_time as _mark_time


def mark_time(what=None):
    _mark_time(what)


class TaskListView(Gtk.TreeView):
    tasks = GObject.Property(type=object, nick='Tasks', blurb='The task list (an instance of TaskList)')

    def __init__(self):
        Gtk.TreeView.__init__(self)
        self.task_store = Gtk.TreeStore(str, str)
        self.set_model(self.task_store)
        column = Gtk.TreeViewColumn(_('Tasks'), Gtk.CellRendererText(), text=0)
        self.append_column(column)
        self.connect('notify::tasks', self.tasks_changed)

    def get_task_for_row(self, path):
        return self.task_store[path][1]

    def tasks_changed(self, *args):
        mark_time('loading task list')
        self.task_store.clear()
        if self.tasks is None:
            mark_time('task list empty')
            return
        for group_name, group_items in self.tasks.groups:
            if group_name == self.tasks.other_title:
                t = self.task_store.append(None, [_('Other'), ''])
            else:
                t = self.task_store.append(None, [group_name, group_name + ': '])
            for item in group_items:
                task = item if group_name == self.tasks.other_title else group_name + ': ' + item
                self.task_store.append(t, [item, task])
        self.expand_all()
        mark_time('task list loaded')
