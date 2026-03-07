import datetime
import re
from gettext import gettext as _

from gi.repository import GLib, GObject, Gtk, Pango

from gtimelog.addons import registry as addons_registry
from gtimelog.addons.base.helpers import (
    format_duration,
    format_percentage,
)
from gtimelog.addons.base.models.time_utils import (
    as_minutes,
    as_seconds,
    different_days,
)


class LogView(Gtk.TextView):
    timelog = GObject.Property(type=object, default=None, nick='Time log', blurb='Time log object')

    date = GObject.Property(type=object, default=None, nick='Date', blurb='Date to show (None tracks today)')

    showing_today = GObject.Property(
        type=bool, default=True, nick='Showing today', blurb='Currently visible time range includes today'
    )

    detail_level = GObject.Property(
        type=str,
        default='chronological',
        nick='Detail level',
        blurb='Detail level to show (chronological/grouped/summary)',
    )

    time_range = GObject.Property(
        type=str, default='day', nick='Time range', blurb='Time range to show (day/week/month)'
    )

    log_order = GObject.Property(
        type=str,
        default='start-time',
        nick='Log order',
        blurb='Log order of tasks/groups (start-time/name/duration/task-list)',
    )

    rounding_time = GObject.Property(type=int, default=0, nick='Rounding Time', blurb='Round time using this value')

    rounding_time_force_above = GObject.Property(
        type=bool, default=False, nick='Rounding Time Force Above', blurb='Force rounding up'
    )

    current_task = GObject.Property(type=str, nick='Current task', blurb='Current task in progress')

    now = GObject.Property(type=object, default=None, nick='Now', blurb='Current date and time')

    filter_text = GObject.Property(
        type=str, default='', nick='Filter text', blurb='Show only tasks matching this substring'
    )

    grouped_entries_ordering_source = GObject.Property(
        type=object,
        nick='Grouped entries ordering source',
        blurb='Addon-provided ordering source for grouped entries',
    )

    expected_work_hours = GObject.Property(
        type=float,
        default=0,
        nick='Expected Work Hours',
        blurb='Expected amount of work hours for the current day',
    )

    expected_presence_hours = GObject.Property(
        type=float,
        default=0,
        nick='Expected Presence Hours',
        blurb='Expected amount of presence hours for the current day',
    )

    expected_workdays = GObject.Property(
        type=str,
        default='Monday,Tuesday,Wednesday,Thursday,Friday',
        nick='Expected Workdays',
        blurb='Expected workdays list (comma-separated day names)',
    )

    distribute_unassigned_time = GObject.Property(
        type=bool,
        default=False,
        nick='Distribute Unassigned Time',
        blurb='Enable distribution of unassigned time marked with ***',
    )

    proportional_distribution = GObject.Property(
        type=bool,
        default=True,
        nick='Proportional Distribution',
        blurb='Distribute unassigned time proportionally based on duration',
    )

    def __init__(self):
        Gtk.TextView.__init__(self)
        self._footer_mark = None
        self._update_pending = False
        self._footer_update_pending = False
        self.set_up_tabs()
        self.set_up_tags()
        self.connect('notify::timelog', self.queue_update)
        self.connect('notify::date', self.queue_update)
        self.connect('notify::showing-today', self.queue_update)
        self.connect('notify::detail-level', self.queue_update)
        self.connect('notify::time-range', self.queue_update)
        self.connect('notify::log-order', self.queue_update)
        self.connect('notify::rounding-time', self.queue_footer_update)
        self.connect('notify::rounding-time-force-above', self.queue_footer_update)
        self.connect('notify::current-task', self.queue_footer_update)
        self.connect('notify::now', self.queue_footer_update)
        self.connect('notify::filter-text', self.queue_update)
        self.connect('notify::grouped-entries-ordering-source', self.queue_update)
        self.connect('notify::distribute-unassigned-time', self.queue_update)
        self.connect('notify::proportional-distribution', self.queue_update)
        addons_registry.trigger_hook('log_view_init', self)

    def queue_update(self, *args):
        if not self._update_pending:
            self._update_pending = True
            GLib.idle_add(self.populate_log)

    def queue_footer_update(self, *args):
        if not self._footer_update_pending:
            self._footer_update_pending = True
            GLib.idle_add(self.update_footer)

    def set_up_tabs(self):
        pango_context = self.get_pango_context()
        em = pango_context.get_font_description().get_size()
        tabs = Pango.TabArray.new(2, False)
        tabs.set_tab(0, Pango.TabAlign.LEFT, 9 * em)
        tabs.set_tab(1, Pango.TabAlign.LEFT, 19.5 * em)
        self.set_tabs(tabs)

    def set_up_tags(self):
        buffer = self.get_buffer()
        buffer.create_tag('today', foreground='#204a87')
        buffer.create_tag('duration', foreground='#ce5c00')
        buffer.create_tag('percentage', foreground='#204a87')
        buffer.create_tag('time', foreground='#4e9a06')
        buffer.create_tag('highlight', foreground='#4e9a06')
        buffer.create_tag('slacking', foreground='gray')

    def get_time_window(self):
        if self.timelog is None:
            raise RuntimeError('timelog not initialized')
        if self.time_range == 'day':
            return self.timelog.window_for_day(self.date)
        if self.time_range == 'week':
            return self.timelog.window_for_week(self.date)
        if self.time_range == 'month':
            return self.timelog.window_for_month(self.date)
        return None

    def get_last_time(self):
        if self.timelog is None:
            raise RuntimeError('timelog not initialized')
        return self.timelog.window.last_time()

    def populate_log(self):
        self._update_pending = False
        self.get_buffer().set_text('')
        if self.timelog is None:
            return
        window = self.get_time_window()

        if self.detail_level == 'chronological':
            total = self._populate_chronological(window)
        elif self.detail_level == 'grouped':
            total = self._populate_grouped(window)
        elif self.detail_level == 'summary':
            total = self._populate_summary(window)
        else:
            return

        self._write_filter_footer(window, total)
        self.reposition_cursor()
        self.add_footer()
        self.scroll_to_end()

    def _populate_chronological(self, window):
        total = datetime.timedelta(0)
        prev = None
        for item in window.all_entries():
            first_of_day = prev is None or different_days(prev, item.start, self.timelog.virtual_midnight)
            if first_of_day and prev is not None:
                self.w('\n')
            if self.time_range != 'day' and first_of_day:
                self.w(_('{0:%A, %Y-%m-%d}\n').format(item.start))
            if self.filter_text in item.entry:
                self.write_item(item)
                total += item.duration
            prev = item.start
        return total

    def _populate_grouped(self, window):
        work, slack = window.grouped_entries(
            sorted_by=self.log_order,
            sorted_tasks=self.grouped_entries_ordering_source,
            distribute_slack=self.distribute_unassigned_time,
            proportional=self.proportional_distribution,
        )
        total = datetime.timedelta(
            seconds=sum([as_seconds(item[2]) for item in work + slack if self.filter_text in item[1]])
        )
        for _start, entry, duration in work + slack:
            if self.filter_text in entry:
                percentage = as_minutes(duration) / as_minutes(total)
                self.write_group(entry, duration, percentage)
        return total

    def _populate_summary(self, window):
        _entries, totals = window.categorized_work_entries(
            distribute_slack=self.distribute_unassigned_time,
            proportional=self.proportional_distribution,
        )
        no_cat = totals.pop(None, None)
        categories = sorted(totals.items())
        if no_cat is not None:
            categories = [('no category', no_cat), *categories]
        total = datetime.timedelta(
            seconds=sum([as_seconds(category[1]) for category in categories if self.filter_text in category[0]])
        )
        for category, duration in categories:
            if self.filter_text in category:
                percentage = as_minutes(duration) / as_minutes(total)
                self.write_group(category, duration, percentage)
        return total

    def _write_filter_footer(self, window, total):
        if not self.filter_text:
            return
        self.w('\n')
        args = [
            (self.filter_text, 'highlight'),
            (format_duration(total), 'duration'),
        ]
        if self.time_range != 'day':
            work_days = window.count_days() or 1
            per_diem = total / work_days
            args.append((format_duration(per_diem), 'duration'))
            self.wfmt(_('Total for {0}: {1} ({2} per day)'), *args)
        else:
            weekly_window = self.timelog.window_for_week(self.date)
            work_days_in_week = weekly_window.count_days() or 1
            week_work, week_slacking = weekly_window.totals(filter_text=self.filter_text)
            week_total = week_work + week_slacking
            args.append((format_duration(week_total), 'duration'))
            per_diem = week_total / work_days_in_week
            args.append((format_duration(per_diem), 'duration'))
            self.wfmt(_('Total for {0}: {1} ({2} this week, {3} per day)'), *args)
        self.w('\n')

    def entry_added(self, same_day):
        if self.detail_level == 'chronological' and same_day and not self.filter_text:
            self.delete_footer()
            self.write_item(self.timelog.last_entry())
            self.add_footer()
            self.scroll_to_end()
        else:
            self.populate_log()

    def reposition_cursor(self):
        where = self.get_buffer().get_end_iter()
        where.backward_cursor_position()
        self.get_buffer().place_cursor(where)

    def scroll_to_end(self):
        GLib.idle_add(self._scroll_to_end)

    def _scroll_to_end(self):
        buffer = self.get_buffer()
        self.scroll_to_iter(buffer.get_end_iter(), 0, False, 0, 0)

    def write_item(self, item):
        self.w(format_duration(item.duration), 'duration')
        self.w('\t')
        period = _('({0:%H:%M}-{1:%H:%M})').format(item.start, item.stop)
        self.w(period, 'time')
        self.w('\t')
        tag = 'slacking' if '**' in item.entry else None
        self.w(item.entry + '\n', tag)

    def write_group(self, entry, duration, percentage=0):
        self.w(format_duration(duration), 'duration')
        tag = 'slacking' if '**' in entry else None
        self.w('\t' + format_percentage(percentage), 'percentage')
        self.w('  \t' + entry + '\n', tag)

    def w(self, text, tag=None):
        """Write some text at the end of the log buffer."""
        buffer = self.get_buffer()
        if tag:
            buffer.insert_with_tags_by_name(buffer.get_end_iter(), text, tag)
        else:
            buffer.insert(buffer.get_end_iter(), text)

    def wfmt(self, fmt, *args):
        """Write formatted text at the end of the log buffer.

        Accepts the same kind of format string as Python's str.format(),
        e.g. "Hello, {0}".

        Each argument should be a tuple (value, tag_name).
        """
        for bit in re.split(r'({\d+(?::[^}]*)?})', fmt):
            if bit.startswith('{'):
                spec = bit[1:-1]
                idx, _colon, fmt = spec.partition(':')
                value, tag = args[int(idx)]
                if fmt:
                    value = format(value, fmt)
                self.w(value, tag)
            else:
                self.w(bit)

    def update_footer(self):
        self._footer_update_pending = False
        if self._footer_mark is None:
            return
        self.delete_footer()
        self.add_footer()

    def delete_footer(self):
        buffer = self.get_buffer()
        buffer.delete(buffer.get_iter_at_mark(self._footer_mark), buffer.get_end_iter())
        buffer.delete_mark(self._footer_mark)
        self._footer_mark = None

    def add_footer(self):
        buffer = self.get_buffer()
        self._footer_mark = buffer.create_mark('footer', buffer.get_end_iter(), True)
        window = self.get_time_window()
        total_work, total_slacking = window.totals()

        self.w('\n')
        if self.time_range == 'day':
            fmt1 = _('Total work done: {0} ({1} this week, {2} per day)')
            fmt2 = _('Total work done: {0} ({1} this week)')
        elif self.time_range == 'week':
            fmt1 = _('Total work done this week: {0} ({1} per day)')
            fmt2 = _('Total work done this week: {0}')
        elif self.time_range == 'month':
            fmt1 = _('Total work done this month: {0} ({1} per day)')
            fmt2 = _('Total work done this month: {0}')
        args = [(format_duration(total_work), 'duration')]
        if self.time_range == 'day':
            weekly_window = self.timelog.window_for_week(self.date)
            week_total_work, _week_total_slacking = weekly_window.totals()
            work_days = weekly_window.count_days()
            args.append((format_duration(week_total_work), 'duration'))
            per_diem = week_total_work / max(1, work_days)
            args.append((format_duration(per_diem), 'duration'))
            self.wfmt(fmt1, *args)
        else:
            if self.time_range == 'week':
                work_days = window.count_days()
                if work_days > 1:
                    per_diem = total_work / work_days
                    args.append((format_duration(per_diem), 'duration'))
                    self.wfmt(fmt1, *args)
                else:
                    self.wfmt(fmt2, args[0], (format_duration(total_work), 'duration'))
            else:
                self.wfmt(fmt2, args[0], (format_duration(total_work), 'duration'))

        self.w('\n')
        if total_slacking:
            self.wfmt(_('Time spent slacking: {0}'), (format_duration(total_slacking), 'duration'))
            self.w('\n')
        addons_registry.trigger_hook('log_footer', self, total_work, total_slacking)
