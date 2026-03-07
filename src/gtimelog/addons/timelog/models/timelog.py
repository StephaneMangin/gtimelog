import datetime
import re
from operator import itemgetter

from gtimelog.addons.base.models.time_utils import (
    different_days,
    first_of_month,
    get_mtime,
    next_month,
    parse_datetime,
    round_dt,
    virtual_day,
)
from gtimelog.addons.timelog.models.time_collection import TimeCollection
from gtimelog.addons.timelog.models.time_window import TimeWindow


class TimeLog(TimeCollection):
    """Time log.
    A time log contains a time window for today, and can add new entries at
    the end.
    """

    _name = 'time.log'

    def __init__(self, filename, virtual_midnight, rounding_time=0, rounding_time_force_above=False):
        super().__init__(virtual_midnight)
        self.filename = filename
        self.rounding_time = rounding_time
        self.rounding_time_force_above = rounding_time_force_above
        self.reread()

    def virtual_today(self):
        return virtual_day(datetime.datetime.now(), self.virtual_midnight)

    def check_reload(self):
        mtime = get_mtime(self.filename)
        if mtime != self.last_mtime:
            self.reread()
            return True
        return False

    def reread(self):
        self.day = self.virtual_today()
        self.last_mtime = get_mtime(self.filename)
        try:
            if hasattr(self.filename, 'read'):
                self.filename.seek(0)
                self.items = self._read(self.filename)
            else:
                with open(self.filename, encoding='utf-8') as f:
                    self.items = self._read(f)
        except OSError:
            self.items = []
        self.window = self.window_for_day(self.day)

    def _read(self, f):
        items = []
        for line in f:
            time, sep, entry = line.partition(': ')
            if not sep:
                continue
            try:
                time = parse_datetime(time)
            except ValueError:
                continue
            entry = entry.strip()
            items.append((time, entry))
        items.sort(key=itemgetter(0))
        return items

    def window_for(self, dt_min, dt_max):
        return TimeWindow(self, dt_min, dt_max)

    def window_for_day(self, date):
        dt_min = datetime.datetime.combine(date, self.virtual_midnight)
        dt_max = dt_min + datetime.timedelta(1)
        return self.window_for(dt_min, dt_max)

    def window_for_week(self, date):
        monday = date - datetime.timedelta(date.weekday())
        dt_min = datetime.datetime.combine(monday, self.virtual_midnight)
        dt_max = dt_min + datetime.timedelta(7)
        return self.window_for(dt_min, dt_max)

    def window_for_month(self, date):
        first_of_this_month = first_of_month(date)
        first_of_next_month = next_month(date)
        dt_min = datetime.datetime.combine(first_of_this_month, self.virtual_midnight)
        dt_max = datetime.datetime.combine(first_of_next_month, self.virtual_midnight)
        return self.window_for(dt_min, dt_max)

    def window_for_date_range(self, dt_min, dt_max):
        dt_min = datetime.datetime.combine(dt_min, self.virtual_midnight)
        dt_max = datetime.datetime.combine(dt_max, self.virtual_midnight)
        dt_max = dt_max + datetime.timedelta(1)
        return self.window_for(dt_min, dt_max)

    def remove_last_entry(self):
        self.check_reload()
        if not self.window.items:
            return None
        with open(self.filename, encoding='utf-8') as f:
            lines = f.readlines()
        for _idx, line in enumerate(reversed(lines), start=1):
            time, sep, entry = line.partition(': ')
            if not sep:
                continue
            try:
                time = parse_datetime(time)
            except ValueError:
                continue
            last_entry = entry.strip()
            break
        else:
            return None
        lines[-_idx] = '##' + lines[-_idx]
        with open(self.filename, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        self.reread()
        return last_entry

    def raw_append(self, line, need_space):
        with open(self.filename, 'a', encoding='utf-8') as f:
            if need_space:
                f.write('\n')
            f.write(line + '\n')
        self.last_mtime = get_mtime(self.filename)

    def get_rounding_delta_and_method(self, entry):
        if '**' in entry:
            method = 'down'
        elif self.rounding_time_force_above:
            method = 'up'
        else:
            method = 'average'
        delta = datetime.timedelta(minutes=self.rounding_time)
        return delta, method

    def get_entry_time(self, entry, now=None):
        if not now:
            now = datetime.datetime.now().replace(second=0, microsecond=0)
        if self.rounding_time:
            delta, method = self.get_rounding_delta_and_method(entry)
            now = round_dt(now, delta, method)
        return now

    def append(self, entry, now=None):
        now = self.get_entry_time(entry, now)
        self.check_reload()
        need_space = False
        last = self.last_time()
        if last and different_days(now, last, self.virtual_midnight):
            need_space = True
        self.items.append((now, entry))
        self.window.items.append((now, entry))
        line = '{}: {}'.format(now.strftime('%Y-%m-%d %H:%M'), entry)
        self.raw_append(line, need_space)

    def valid_time(self, time):
        if time > datetime.datetime.now():
            return False
        last = self.last_time()
        return not (last and time < last)

    def parse_correction(self, entry):
        now = None
        date_match = re.match(r'(\d\d?):(\d\d)\s+', entry)
        delta_match = re.match(r'[\-+]([1-9]\d?|1\d\d)\s+', entry)
        if date_match:
            h = int(date_match.group(1))
            m = int(date_match.group(2))
            if 0 <= h < 24 and 0 <= m < 60:
                now = datetime.datetime.combine(self.virtual_today(), datetime.time(h, m))
                if now.time() < self.virtual_midnight:
                    now += datetime.timedelta(1)
                if self.valid_time(now):
                    entry = entry[date_match.end() :]
                else:
                    now = None
        if delta_match:
            seconds = int(delta_match.group()) * 60
            now = self.window.last_time() if seconds >= 0 else datetime.datetime.now().replace(second=0, microsecond=0)
            if now is not None:
                now += datetime.timedelta(seconds=seconds)
                if self.valid_time(now):
                    entry = entry[delta_match.end() :]
                else:
                    now = None
        return entry, now
