import datetime

from gtimelog.models import Controller


class Reports(Controller):
    """Generation of reports."""

    _name = 'reports'

    def __init__(self, window, email_headers=True, style='plain'):
        self.window = window
        self.email_headers = email_headers
        self.style = style
        self.distribute_slack = False
        self.proportional = True
        self.duration_formatter = self.env.get('platform.duration.formatter')

    @staticmethod
    def _split_category(entry):
        if ': ' in entry:
            category, task = entry.split(': ', 1)
            return category.strip(), task.strip()
        if entry.endswith(':'):
            return entry.partition(':')[0].strip(), ''
        return None, entry

    def _categorizing_report(self, output, email, who, subject, period_name):
        """A report that displays entries by category.

        Writes a report template in RFC-822 format to output.

        The report looks like
        |                             time
        | Overhead:
        |   Status meeting              43
        |   Mail                      1:50
        | --------------------------------
        |                             2:33
        |
        | Compass:
        |   Compass: hotpatch         2:13
        |   Call with a client          30
        | --------------------------------
        |                             3:43
        |
        | No category:
        |   SAT roundup               1:00
        | --------------------------------
        |                             1:00
        |
        | Total work done this week: 6:26
        |
        | Categories by time spent:
        |
        | Compass       3:43
        | Overhead      2:33
        | No category   1:00

        """
        window = self.window

        if self.email_headers:
            output.write(f'To: {email}\n')
            output.write(f'Subject: {subject}\n')
            output.write('\n')

        items = list(window.all_entries())
        if not items:
            output.write(f'No work done this {period_name}.\n')
            return
        output.write(' ' * 46)
        output.write('                   time\n')

        entries, totals = window.categorized_work_entries(
            distribute_slack=self.distribute_slack,
            proportional=self.proportional,
        )
        total_work = sum(totals.values(), datetime.timedelta(0))
        if entries:
            if None in entries:
                e = entries.pop(None)
                categories = sorted(entries)
                categories.append('No category')
                entries['No category'] = e
                t = totals.pop(None)
                totals['No category'] = t
            else:
                categories = sorted(entries)
            for cat in categories:
                output.write(f'{cat}:\n')

                work = [(entry, duration) for start, entry, duration in entries[cat]]
                work.sort()
                for entry, duration in work:
                    if not duration:
                        continue  # skip empty "arrival" entries

                    entry = entry[:1].upper() + entry[1:]
                    output.write(f'  {entry:<61s}  {self.duration_formatter.format_duration_short(duration):>5s}\n')

                output.write('-' * 70 + '\n')
                output.write(f'{self.duration_formatter.format_duration_short(totals[cat]):>70s}\n')
                output.write('\n')
        output.write(
            f'Total work done this {period_name}: {self.duration_formatter.format_duration_short(total_work)}\n'
        )

        output.write('\n')

        ordered_by_time = [(time, cat) for cat, time in totals.items()]
        ordered_by_time.sort(reverse=True)
        max_cat_length = max([len(cat) for cat in totals])
        line_format = '  %-' + str(max_cat_length + 4) + 's %+5s\n'
        output.write('Categories by time spent:\n')
        for time, cat in ordered_by_time:
            output.write(line_format % (cat, self.duration_formatter.format_duration_short(time)))

        tags = self.window.set_of_all_tags()
        if tags:
            self._report_tags(output, tags)

    def _report_tags(self, output, tags):
        """Helper method that lists time spent per tag.

        Use this to add a section in a report looks similar to this:

        sysadmin:     2 hours 1 min
        www:          18 hours 45 min
        mailserver:   3 hours

        Note that duration may not add up to the total working time,
        as a single entry can have multiple or no tags at all!

        Argument `tags` is a set of tags (string).  It is not modified.
        """
        output.write('\n')
        output.write('Time spent in each area:\n')
        output.write('\n')
        # sum work and slacking time per tag; we do not care in this report
        tags_totals = {}
        for tag in tags:
            spent_working, spent_slacking = self.window.totals(tag)
            tags_totals[tag] = spent_working + spent_slacking
        # compute width of tag label column
        max_tag_length = max([len(tag) for tag in tags_totals])
        line_format = '  %-' + str(max_tag_length + 4) + 's %+5s\n'
        # sort by time spent (descending)
        for tag, spent in sorted(tags_totals.items(), key=(lambda it: it[1]), reverse=True):
            output.write(line_format % (tag, self.duration_formatter.format_duration_short(spent)))
        output.write('\n')
        output.write(
            'Note that area totals may not add up to the period totals,\n'
            'as each entry may be belong to multiple areas (or none at all).\n'
        )

    def _report_categories(self, output, categories):
        """A helper method that lists time spent per category.

        Use this to add a section in a report looks similar to this:

        Administration:  2 hours 1 min
        Coding:          18 hours 45 min
        Learning:        3 hours

        category is a dict of entries (<category name>: <duration>).
        It is not preserved.
        """
        output.write('\n')
        output.write('By category:\n')
        output.write('\n')

        no_cat = categories.pop(None, None)
        items = sorted(categories.items())
        if no_cat is not None:
            items.append(('(none)', no_cat))
        for cat, duration in items:
            output.write(f'{cat:<62s}  {self.duration_formatter.format_duration_long(duration)}\n')
        output.write('\n')

    def _plain_report(self, output, email, who, subject, period_name):
        """Format a report that does not categorize entries.

        Writes a report template in RFC-822 format to output.
        """
        window = self.window

        if self.email_headers:
            output.write(f'To: {email}\n')
            output.write(f'Subject: {subject}\n')
            output.write('\n')

        items = list(window.all_entries())
        if not items:
            output.write(f'No work done this {period_name}.\n')
            return
        output.write(' ' * 46)
        output.write('                time\n')
        work, _slack = window.grouped_entries(
            distribute_slack=self.distribute_slack,
            proportional=self.proportional,
        )
        total_work = sum((duration for _start, _entry, duration in work), datetime.timedelta(0))
        categories = {}
        if work:
            for _start, entry, duration in work:
                if not duration:
                    continue
                entry = entry[:1].upper() + entry[1:]
                output.write(f'{entry:<62s}  {self.duration_formatter.format_duration_long(duration)}\n')
                cat, _task = self._split_category(entry)
                categories[cat] = categories.get(cat, datetime.timedelta(0)) + duration
            output.write('\n')
        output.write(
            f'Total work done this {period_name}: {self.duration_formatter.format_duration_long(total_work)}\n'
        )

        if categories:
            self._report_categories(output, categories)

        tags = self.window.set_of_all_tags()
        if tags:
            self._report_tags(output, tags)

    def weekly_report_subject(self, who):
        week = self.window.min_timestamp.isocalendar()[1]
        return f'Weekly report for {who} (week {week:02d})'

    def weekly_report(self, output, email, who):
        if self.style == 'categorized':
            return self.weekly_report_categorized(output, email, who)
        return self.weekly_report_plain(output, email, who)

    def weekly_report_plain(self, output, email, who):
        """Format a weekly report."""
        subject = self.weekly_report_subject(who)
        return self._plain_report(output, email, who, subject, period_name='week')

    def weekly_report_categorized(self, output, email, who):
        """Format a weekly report with entries displayed  under categories."""
        subject = self.weekly_report_subject(who)
        return self._categorizing_report(output, email, who, subject, period_name='week')

    def monthly_report_subject(self, who):
        month = self.window.min_timestamp.strftime('%Y/%m')
        return f'Monthly report for {who} ({month})'

    def monthly_report(self, output, email, who):
        if self.style == 'categorized':
            return self.monthly_report_categorized(output, email, who)
        return self.monthly_report_plain(output, email, who)

    def monthly_report_plain(self, output, email, who):
        """Format a monthly report ."""
        subject = self.monthly_report_subject(who)
        return self._plain_report(output, email, who, subject, period_name='month')

    def monthly_report_categorized(self, output, email, who):
        """Format a monthly report with entries displayed  under categories."""
        subject = self.monthly_report_subject(who)
        return self._categorizing_report(output, email, who, subject, period_name='month')

    def custom_range_report_subject(self, who):
        date_from = self.window.min_timestamp.strftime('%Y-%m-%d')
        date_to = self.window.max_timestamp - datetime.timedelta(1)
        date_to = date_to.strftime('%Y-%m-%d')
        return f'Custom date range report for {who} ({date_from} - {date_to})'

    def custom_range_report_categorized(self, output, email, who):
        """Format a custom range report with entries displayed under categories."""
        subject = self.custom_range_report_subject(who)
        return self._categorizing_report(output, email, who, subject, period_name='custom range')

    def daily_report_subject(self, who):
        # strftime('%a') would give us translated names, but we want our
        # reports to be standardized and machine-parseable
        weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        weekday = weekday_names[self.window.min_timestamp.weekday()]
        week = self.window.min_timestamp.isocalendar()[1]
        return f'{self.window.min_timestamp:%Y-%m-%d} report for {who} ({weekday}, week {week:0>2})'

    def daily_report(self, output, email, who):
        """Format a daily report.

        Writes a daily report template in RFC-822 format to output.
        """
        window = self.window
        if self.email_headers:
            output.write(f'To: {email}\n')
            output.write(f'Subject: {self.daily_report_subject(who)}\n')
            output.write('\n')
        items = list(window.all_entries())
        if not items:
            output.write('No work done today.\n')
            return
        start, _stop, duration, tags, entry = items[0]
        entry = entry[:1].upper() + entry[1:]
        output.write('{} at {}\n'.format(entry, start.strftime('%H:%M')))
        output.write('\n')
        work, slack = window.grouped_entries(
            distribute_slack=self.distribute_slack,
            proportional=self.proportional,
        )
        total_work = sum((duration for _start, _entry, duration in work), datetime.timedelta(0))
        total_slacking = sum((duration for _start, _entry, duration in slack), datetime.timedelta(0))
        categories = {}
        if work:
            for _start, entry, duration in work:
                entry = entry[:1].upper() + entry[1:]
                output.write(f'{entry:<62s}  {self.duration_formatter.format_duration_long(duration)}\n')
                cat, _task = self._split_category(entry)
                categories[cat] = categories.get(cat, datetime.timedelta(0)) + duration

            output.write('\n')
        output.write(f'Total work done: {self.duration_formatter.format_duration_long(total_work)}\n')

        if categories:
            self._report_categories(output, categories)

        output.write('Slacking:\n\n')

        if slack:
            for _start, entry, duration in slack:
                entry = entry[:1].upper() + entry[1:]
                output.write(f'{entry:<62s}  {self.duration_formatter.format_duration_long(duration)}\n')
            output.write('\n')
        output.write(f'Time spent slacking: {self.duration_formatter.format_duration_long(total_slacking)}\n')

        tags = self.window.set_of_all_tags()
        if tags:
            self._report_tags(output, tags)
