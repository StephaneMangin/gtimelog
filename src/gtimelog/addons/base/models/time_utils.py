import datetime
import os
import re


def as_seconds(duration):
    """Convert a datetime.timedelta to an integer number of seconds."""
    return duration.days * 24 * 60 * 60 + duration.seconds


def as_minutes(duration):
    """Convert a datetime.timedelta to an integer number of minutes."""
    return duration.days * 24 * 60 + duration.seconds // 60


def as_hours(duration):
    """Convert a datetime.timedelta to a float number of hours."""
    return duration.days * 24.0 + duration.seconds / (60.0 * 60.0)


def format_duration(duration):
    """Format a datetime.timedelta with minute precision."""
    h, m = divmod(as_minutes(duration), 60)
    return f'{h} h {m} min'


def format_duration_short(duration):
    """Format a datetime.timedelta with minute precision."""
    h, m = divmod((duration.days * 24 * 60 + duration.seconds // 60), 60)
    return f'{h}:{m:02d}'


def format_duration_long(duration):
    """Format a datetime.timedelta with minute precision, long format."""
    h, m = divmod((duration.days * 24 * 60 + duration.seconds // 60), 60)
    if h and m:
        return f'{h} hour{"s" if h != 1 else ""} {m} min'
    if h:
        return f'{h} hour{"s" if h != 1 else ""}'
    return f'{m} min'


def parse_datetime(dt):
    """Parse a datetime instance from 'YYYY-MM-DD HH:MM' formatted string."""
    if len(dt) != 16 or dt[4] != '-' or dt[7] != '-' or dt[10] != ' ' or dt[13] != ':':
        raise ValueError(f'bad date time: {dt!r}')
    try:
        year = int(dt[:4])
        month = int(dt[5:7])
        day = int(dt[8:10])
        hour = int(dt[11:13])
        minute = int(dt[14:])
    except ValueError:
        raise ValueError(f'bad date time: {dt!r}') from None
    return datetime.datetime(year, month, day, hour, minute)


def parse_time(t):
    """Parse a time instance from 'HH:MM' formatted string."""
    m = re.match(r'^(\d+):(\d+)$', t)
    if not m:
        raise ValueError(f'bad time: {t!r}')
    hour, minute = map(int, m.groups())
    return datetime.time(hour, minute)


def virtual_day(dt, virtual_midnight):
    """Return the "virtual day" of a timestamp.

    Timestamps between midnight and "virtual midnight" (e.g. 2 am) are
    assigned to the previous "virtual day".
    """
    if dt.time() < virtual_midnight:  # assign to previous day
        return dt.date() - datetime.timedelta(1)
    return dt.date()


def different_days(dt1, dt2, virtual_midnight):
    """Check whether dt1 and dt2 are on different "virtual days".

    See virtual_day().
    """
    return virtual_day(dt1, virtual_midnight) != virtual_day(dt2, virtual_midnight)


def first_of_month(date):
    """Return the first day of the month for a given date."""
    return date.replace(day=1)


def prev_month(date):
    """Return the first day of the previous month."""
    if date.month == 1:
        return datetime.date(date.year - 1, 12, 1)
    return datetime.date(date.year, date.month - 1, 1)


def next_month(date):
    """Return the first day of the next month."""
    if date.month == 12:
        return datetime.date(date.year + 1, 1, 1)
    return datetime.date(date.year, date.month + 1, 1)


def uniq(items):
    """Return list with consecutive duplicates removed."""
    result = items[:1]
    for item in items[1:]:
        if item != result[-1]:
            result.append(item)
    return result


def get_mtime(filename):
    """Return the modification time of a file, if it exists.

    Returns None if the file doesn't exist.
    """
    if hasattr(filename, 'read'):
        return None
    try:
        return os.stat(filename).st_mtime
    except OSError:
        return None


def round_dt(dt, date_delta=datetime.timedelta(minutes=0), to='average'):
    """
    Round a datetime object to a multiple of a timedelta
    dt : datetime.datetime object, default now.
    dateDelta : timedelta object, we round to a multiple of this, default 0 minute.
    from:  http://stackoverflow.com/questions/3463930/how-to-round-the-minute-of-a-datetime-object-python
    """
    round_to = date_delta.total_seconds()
    seconds = (dt - dt.min).seconds

    if seconds % round_to == 0 and dt.microsecond == 0:
        rounding = (seconds + round_to / 2) // round_to * round_to
    else:
        if to == 'up':
            # // is a floor division, not a comment on following line (like in javascript):
            rounding = (seconds + dt.microsecond / 1000000 + round_to) // round_to * round_to
        elif to == 'down':
            rounding = seconds // round_to * round_to
        else:
            rounding = (seconds + round_to / 2) // round_to * round_to

    return dt + datetime.timedelta(0, rounding - seconds, -dt.microsecond)
