import logging
import sys
import time
from gettext import gettext as _

from gtimelog.addons.base.models.time_utils import as_minutes

DEBUG = '--debug' in sys.argv


if DEBUG:

    def mark_time(what=None, _prev=None):
        if _prev is None:
            _prev = [0, 0]
        t = time.time()
        if what:
            pass
        else:
            _prev[1] = t
        _prev[0] = t
else:

    def mark_time(what=None):
        pass


log = logging.getLogger('gtimelog')


def format_duration(duration):
    """Format a datetime.timedelta with minute precision (i18n version)."""
    h, m = divmod(as_minutes(duration), 60)
    return _('{0} h {1} min').format(h, m)


def format_percentage(percentage):
    """Format a float to readable percentage."""
    return f'{percentage:.1%}'


def isascii(s):
    return all(0 <= ord(c) <= 127 for c in s)


def copy_properties(src, dest):
    """Copy GObject properties from *src* widget to *dest* widget."""
    from gi.repository import GObject

    blacklist = (
        'events',
        'child',
        'parent',
        'input-hints',
        'buffer',
        'tabs',
        'completion',
        'model',
        'type',
        'progress-',
        'primary-icon-',
        'secondary-icon-',
    )
    rw_flags = GObject.ParamFlags.READWRITE
    for prop in src.props:
        if prop.flags & GObject.ParamFlags.DEPRECATED != 0:
            continue
        if prop.flags & rw_flags != rw_flags:
            continue
        if prop.name.startswith(blacklist):
            continue
        setattr(dest.props, prop.name, getattr(src.props, prop.name))


def swap_widget(builder, name, replacement):
    """Replace a Glade widget with a custom subclass instance."""
    from gi.repository import Gtk

    original = builder.get_object(name)
    copy_properties(original, replacement)
    parent = original.get_parent()
    if isinstance(parent, Gtk.Box):
        expand, fill, padding, pack_type = parent.query_child_packing(original)
        position = parent.get_children().index(original)
    parent.remove(original)
    parent.add(replacement)
    if isinstance(parent, Gtk.Box):
        parent.set_child_packing(replacement, expand, fill, padding, pack_type)
        parent.reorder_child(replacement, position)
    original.destroy()


def make_option(long_name, short_name=None, flags=0, arg=None, arg_data=None, description=None, arg_description=None):
    """Create a GLib.OptionEntry."""
    from gi.repository import GLib

    if arg is None:
        arg = GLib.OptionArg.NONE
    option = GLib.OptionEntry()
    option.long_name = long_name.lstrip('-')
    option.short_name = 0 if not short_name else short_name.lstrip('-')
    option.flags = flags
    option.arg = int(arg)
    option.arg_data = arg_data
    option.description = description
    option.arg_description = arg_description
    return option
