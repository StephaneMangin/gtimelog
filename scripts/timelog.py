#!/usr/bin/env python
from __future__ import print_function, with_statement

import datetime
import readline  # noqa: make raw_input() friendlier

from past.builtins import raw_input

while True:
    try:
        what = raw_input("> ")
    except EOFError:
        print
        break
    ts = datetime.datetime.now()
    line = "%s: %s" % (ts.strftime("%Y-%m-%d %H:%M"), what)
    print(line)
    with open("timelog.txt", "a+") as f:
        f.write(line)
