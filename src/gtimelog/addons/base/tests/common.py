import datetime
import doctest
import os
import re
import shutil
import tempfile
from io import StringIO

from gtimelog.addons.timelog.models import TimeLog


class Checker(doctest.OutputChecker):
    """Doctest output checker that can deal with unicode literals."""

    def check_output(self, want, got, optionflags):
        got = re.sub(r"""\bu('[^']*'|"[^"]*")""", r'\1', got)
        got = re.sub(r'datetime[.]timedelta[(]seconds=(\d+)[)]', r'datetime.timedelta(0, \1)', got)
        return doctest.OutputChecker.check_output(self, want, got, optionflags)


class Mixins:
    """Mixin providing temp dir and file helpers for tests."""

    tempdir = None

    def mkdtemp(self):
        if self.tempdir is None:
            self.tempdir = tempfile.mkdtemp(prefix='gtimelog-test-')
            self.addCleanup(shutil.rmtree, self.tempdir)
        return self.tempdir

    def tempfile(self, filename='timelog.txt'):
        return os.path.join(self.mkdtemp(), filename)

    def write_file(self, filename, content):
        filename = os.path.join(self.mkdtemp(), filename)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return filename


def make_time_window(file=None, dt_min=None, dt_max=None, vm=datetime.time(2)):
    """Create a TimeWindow from sample data for testing."""
    if file is None:
        file = StringIO()
    return TimeLog(file, vm).window_for(dt_min, dt_max)
