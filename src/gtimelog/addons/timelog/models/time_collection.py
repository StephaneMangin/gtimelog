import datetime

from gtimelog.addons.base.models.entry import Entry
from gtimelog.addons.base.models.time_utils import different_days
from gtimelog.models import Model


class TimeCollection(Model):
    """A collection of timestamped events.
    self.items is a list of (timestamp, event_title) tuples.
    """

    _name = 'time.collection'

    def __init__(self, virtual_midnight):
        self.items = []
        self.virtual_midnight = virtual_midnight

    def last_time(self):
        if not self.items:
            return None
        return self.items[-1][0]

    def last_entry(self):
        if not self.items:
            return None
        stop = self.items[-1][0]
        entry = self.items[-1][1]
        start = stop if len(self.items) == 1 else self.items[-2][0]
        if different_days(start, stop, self.virtual_midnight):
            start = stop
        duration = stop - start
        entry, tags = self._split_entry_and_tags(entry)
        return Entry(start, stop, duration, tags, entry)

    def all_entries(self):
        stop = None
        for item in self.items:
            start = stop
            stop = item[0]
            entry = item[1]
            if start is None or different_days(start, stop, self.virtual_midnight):
                start = stop
            duration = stop - start
            entry, tags = self._split_entry_and_tags(entry)
            yield Entry(start, stop, duration, tags, entry)

    @staticmethod
    def _split_entry_and_tags(entry):
        if ' -- ' in entry:
            entry, tags_bundle = entry.split(' -- ', 1)
            entry = entry.rstrip()
            tags = set(tags_bundle.split())
            if '***' in tags:
                entry += ' ***'
                tags.remove('***')
            elif '**' in tags:
                entry += ' **'
                tags.remove('**')
        else:
            tags = set()
        return entry, tags

    @staticmethod
    def split_category(entry):
        if ': ' in entry:
            cat, tsk = entry.split(': ', 1)
            return cat.strip(), tsk.strip()
        if entry.endswith(':'):
            return entry.partition(':')[0].strip(), ''
        return None, entry

    def set_of_all_tags(self):
        all_tags = set()
        for entry in self.all_entries():
            all_tags.update(entry.tags)
        return all_tags

    def count_days(self):
        count = 0
        last = None
        for entry in self.all_entries():
            if last is None or different_days(last, entry.start, self.virtual_midnight):
                last = entry.start
                count += 1
        return count

    def grouped_entries(self, skip_first=True, sorted_by='start-time', sorted_tasks=None, **kwargs):
        service_cls = self.env['time.distribution.service']
        return service_cls().grouped_entries(
            self,
            skip_first=skip_first,
            sorted_by=sorted_by,
            sorted_tasks=sorted_tasks,
            **kwargs,
        )

    def categorized_work_entries(self, skip_first=True, **kwargs):
        work, _slack = self.grouped_entries(skip_first=skip_first, **kwargs)
        entries = {}
        totals = {}
        for start, entry, duration in work:
            cat, task = self.split_category(entry)
            entry_list = entries.get(cat, [])
            entry_list.append((start, task, duration))
            entries[cat] = entry_list
            totals[cat] = totals.get(cat, datetime.timedelta(0)) + duration
        return entries, totals

    def totals(self, tag=None, filter_text=None):
        total_work = total_slacking = datetime.timedelta(0)
        for _start, _stop, duration, tags, entry in self.all_entries():
            if tag is not None and tag not in tags:
                continue
            if filter_text is not None and filter_text not in entry:
                continue
            if '***' in entry:
                continue
            if '**' in entry:
                total_slacking += duration
            else:
                total_work += duration
        return total_work, total_slacking

    @classmethod
    def _get_grouped_order_key(cls, sorted_by, sorted_tasks):
        if sorted_by == 'start-time':
            return None
        if sorted_by == 'name':
            return lambda x: x[1]
        if sorted_by == 'duration':
            return lambda x: (x[2], x[0], x[1])
        if sorted_by == 'task-list':
            return lambda x: (sorted_tasks.order(x[1]), x[1])
        return None
