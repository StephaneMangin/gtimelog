from gtimelog.models import Service


class TimeDistributionService(Service):
    """Compute grouped entries with optional distribution policies.

    Default implementation keeps historical behavior (no `***` redistribution).
    Addons can extend this service via ``_inherit = 'time.distribution.service'``.
    """

    _name = 'time.distribution.service'

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
        del distribute_slack, proportional, kwargs
        work = {}
        slack = {}
        for start, _stop, duration, _tags, entry in collection.all_entries():
            if skip_first:
                skip_first = False
                continue
            if '***' in entry:
                continue
            entries = slack if '**' in entry else work
            if entry in entries:
                old_start, _old_entry, old_duration = entries[entry]
                start = min(start, old_start)
                duration += old_duration
            entries[entry] = (start, entry, duration)
        key_func = collection._get_grouped_order_key(sorted_by, sorted_tasks)
        work = sorted(work.values(), key=key_func)
        slack = sorted(slack.values(), key=key_func)
        return work, slack
