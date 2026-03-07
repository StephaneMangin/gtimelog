import datetime
from collections import defaultdict

import gtimelog.addons.timelog.services  # noqa: F401
from gtimelog.models import Service


class TimeDistributionService(Service):
    """Extend grouped entries to distribute `***` pauses on a weekly scope."""

    _inherit = 'time.distribution.service'

    def grouped_entries(
        self,
        collection,
        skip_first=True,
        sorted_by='start-time',
        sorted_tasks=None,
        distribute_slack=False,
        proportional=True,
        **kwargs,
    ):
        if not distribute_slack:
            return super().grouped_entries(
                collection,
                skip_first=skip_first,
                sorted_by=sorted_by,
                sorted_tasks=sorted_tasks,
                distribute_slack=distribute_slack,
                proportional=proportional,
                **kwargs,
            )

        work_by_week, slack_by_week, distributable_slack_by_week = self._split_entries_by_week(collection, skip_first)
        work = self._merge_work_by_week(work_by_week, distributable_slack_by_week, proportional)
        slack = self._merge_week_buckets(slack_by_week)

        key_func = collection._get_grouped_order_key(sorted_by, sorted_tasks)
        return sorted(work.values(), key=key_func), sorted(slack.values(), key=key_func)

    @staticmethod
    def _split_entries_by_week(collection, skip_first):
        work_by_week = {}
        slack_by_week = {}
        distributable_slack_by_week = defaultdict(lambda: datetime.timedelta(0))

        for start, _stop, duration, _tags, entry in collection.all_entries():
            if skip_first:
                skip_first = False
                continue

            week_key = start.isocalendar()[:2]
            if '***' in entry:
                distributable_slack_by_week[week_key] += duration
                continue

            entries_by_week = slack_by_week if '**' in entry else work_by_week
            entries = entries_by_week.setdefault(week_key, {})
            TimeDistributionService._merge_entry(entries, entry, start, duration)

        return work_by_week, slack_by_week, distributable_slack_by_week

    def _merge_work_by_week(self, work_by_week, distributable_slack_by_week, proportional):
        merged_work = {}
        for week_key, week_work in work_by_week.items():
            distributable_slack = distributable_slack_by_week.get(week_key, datetime.timedelta(0))
            if distributable_slack > datetime.timedelta(0) and week_work:
                week_work = self._distribute(week_work, distributable_slack, proportional)
            self._merge_entries(merged_work, week_work)
        return merged_work

    @staticmethod
    def _merge_week_buckets(entries_by_week):
        merged = {}
        for week_entries in entries_by_week.values():
            TimeDistributionService._merge_entries(merged, week_entries)
        return merged

    @staticmethod
    def _merge_entries(target, source):
        for entry, (start, name, duration) in source.items():
            TimeDistributionService._merge_entry(target, entry, start, duration, name)

    @staticmethod
    def _merge_entry(entries, entry, start, duration, name=None):
        if entry in entries:
            old_start, old_name, old_duration = entries[entry]
            entries[entry] = (min(start, old_start), old_name, old_duration + duration)
            return
        entries[entry] = (start, name or entry, duration)

    @staticmethod
    def _distribute(work_entries, slack_duration, proportional):
        if not work_entries:
            return work_entries
        if proportional:
            total_secs = sum(d.total_seconds() for _, _, d in work_entries.values())
            if total_secs == 0:
                proportional = False
        if proportional:
            result = {}
            for name, (start, entry, duration) in work_entries.items():
                proportion = duration.total_seconds() / total_secs
                extra = datetime.timedelta(seconds=slack_duration.total_seconds() * proportion)
                result[name] = (start, entry, duration + extra)
            return result

        per_entry = datetime.timedelta(seconds=slack_duration.total_seconds() / len(work_entries))
        return {name: (start, entry, duration + per_entry) for name, (start, entry, duration) in work_entries.items()}
