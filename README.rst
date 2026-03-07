GTimeLog
========

GTimeLog is a modular time-tracking application built on GTK 3. It lets
you record what you work on throughout the day, generate reports, and
export timesheets — all from a simple text-entry interface.

.. note::

   This version is an almost complete architectural rework of the original
   GTimeLog application. The codebase has been refactored into a modular
   addon system inspired by Odoo, but the user-facing ergonomics remain
   unchanged — if you were already using GTimeLog, everything works exactly
   as before (At least i hope ^^).

.. image:: https://raw.github.com/gtimelog/gtimelog/master/docs/gtimelog.png
   :alt: screenshot

.. contents::


How It Works
------------

When you arrive at work, start GTimeLog and type ``arrived **``.
Then start doing something. Whenever you *finish* an activity (or switch
to another one), type its name into the prompt and press Enter.

The key idea: **you name an activity when you stop, not when you start.**

Activities whose name ends with ``**`` are counted as non-work (lunch,
breaks, browsing). Activities ending in ``***`` are completely hidden
from reports. Everything else is billable work.

Categories are expressed with a colon::

  project1: fixing bug #1234
  project2: weekly meeting

Tags can be appended after ``" -- "``::

  project3: deploy staging -- sysadmin www

See `docs/index.rst`_ for the full user guide and `docs/formats.rst`_
for the timelog file format.


Installing
----------

**System packages** (Debian/Ubuntu)::

  sudo apt-get install gtimelog

**Fedora**::

  sudo dnf install gtimelog

**PyPI**::

  pip install gtimelog
  gtimelog

**From source** (development)::

  git clone https://github.com/gtimelog/gtimelog
  cd gtimelog
  python -m venv .venv && source .venv/bin/activate
  pip install -e .
  make all          # compiles GSettings schemas & translations
  ./gtimelog

System requirements:

- Python 3.6+
- PyGObject, GTK+ 3.18+
- GObject-introspection type libraries: Gtk, Gdk, GLib, Gio, GObject,
  Pango, Soup, Secret


Project Structure
-----------------

::

  src/gtimelog/
  ├── __init__.py          # ComponentRegistry, Model/Service/Controller/Hook base classes
  ├── main.py              # Application entry-point, gettext setup
  ├── paths.py             # Resource paths (UI files, icons, locale, schemas)
  ├── utils.py             # GI version checks
  ├── addons/              # ← all behaviour lives here
  │   ├── __init__.py      # AddonRegistry — discovery, dependency ordering, hook system
  │   ├── ui_extensions.py # Odoo-style xpath UI inheritance for .ui files
  │   ├── base/            # Core GTK skeleton, base models, global views
  │   ├── timelog/         # LogView, TaskEntry, date navigation, tick clock
  │   ├── office_hours/    # Time left at work, overtime estimation
  │   ├── tasks/           # Task list model + task pane + remote download
  │   ├── reports/         # Report generation and ReportView widget
  │   ├── reports_csv/     # CSV exports (daily, Odoo timesheet)
  │   ├── reports_ical/    # iCalendar export
  │   ├── mail_sender/     # E-mail sending for reports
  │   ├── odoo_export/     # Odoo v17 timesheet CSV export
  │   └── preferences/     # Preferences dialog
  ├── data/                # GSettings schema
  ├── locale/              # Compiled .mo translation files (auto-generated)
  └── tests/               # Test suite


Architecture
------------

GTimeLog follows a **modular addon architecture** inspired by Odoo.
The core framework provides:

- A **ComponentRegistry** with Odoo-style ``_name`` / ``_inherit``
  inheritance for Models, Services, and Controllers.
- A **Hook system** allowing addons to inject behaviour at named
  extension points (``window_init``, ``log_footer``, ``prefs_init``, …).
- An **XML-based UI extension system** (xpath operations) so addons can
  modify ``.ui`` files without touching the originals.
- An **AddonRegistry** that discovers addon packages, resolves their
  dependency graph, and loads them in order.

Each addon is a Python package inside ``addons/`` containing:

::

  addons/<name>/
  ├── __manifest__.py   # name, version, depends, description
  ├── __init__.py       # imports sub-packages, registers hooks
  ├── models/           # Model / Service classes (_name, _inherit)
  ├── controllers/      # Controller classes, GTK logic
  ├── views/            # .ui files and .ui.xml extension files
  ├── settings/         # GSettings bindings
  ├── i18n/             # .pot / .po translation sources
  ├── data/             # static data files
  └── tests/            # addon-specific tests


Built-in Addons
~~~~~~~~~~~~~~~

================== ============ ===================================================
Addon              Depends on   Description
================== ============ ===================================================
``base``           —            Core GTK skeleton, base models (Entry, TimeLog,
                                TimeCollection, Settings), global views and helpers
``about``          base         About dialog behavior
``preferences``    base         Preferences dialog
``timelog``        base         LogView, TaskEntry, date navigation, tick clock
``tasks``           base,        Task list model (``tasks.txt``), task pane
                   timelog       with tree view, remote task download, secret storage
``office_hours``    base,        Time left at work, estimated week overtime,
                   timelog       "at office today" footer
``slack_distribution`` base,     Distributes ``***`` slack time across work entries
                   timelog       (equal or proportional)
``reports``         base,        Report generation (daily, weekly, monthly),
                   timelog       ReportView widget, customer tasks tree
``mail_sender``     base         E-mail message preparation and SMTP sending
``reports_csv``     base,        CSV export formats (daily, Odoo timesheet)
                   reports
``reports_ical``    base,        iCalendar export
                   reports
================== ============ ===================================================


Extending GTimeLog
~~~~~~~~~~~~~~~~~~

To create a new addon:

1. Create a directory under ``addons/`` (or any path in
   ``GTIMELOG_ADDONS_PATH``).

2. Add a ``__manifest__.py``::

     {
         "name": "My Addon",
         "version": "1.0.0",
         "depends": ["base", "timelog"],
         "description": "Does something useful.",
     }

3. In ``__init__.py``, import your models/controllers and register hooks::

     from gtimelog import Hook

     class MyHooks(Hook):
         def window_init(window):
             # called after the main window is built
             ...

         def log_footer(log_view, total_work, total_slacking):
             # called when the log footer is rendered
             ...

4. To extend an existing model::

     from gtimelog import Model

     class ExtendedTimeLog(Model):
         _inherit = 'time.log'

         def my_new_method(self):
             ...

5. To extend a ``.ui`` file, create ``views/my_changes.ui.xml``::

     <ui_extension target="gtimelog.ui">
       <xpath expr="//object[@id='headerbar']" position="inside">
         <child>
           <object class="GtkButton" id="my_button">
             <property name="label">My Button</property>
             <property name="visible">True</property>
           </object>
         </child>
       </xpath>
     </ui_extension>

  Layer Override Points (OpenObject style)
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  The layered architecture exposes explicit extension points through
  ``component_registry`` and ``_inherit``.

  **Platform layer**

  - ``platform.entry.parser``
  - ``platform.duration.formatter``

  Current addon override example:

  - ``reports.platform.entry.parser`` (inherits ``platform.entry.parser``)

  **Domain layer**

  - ``domain.reports.service``
  - ``domain.tasks.policy``
  - ``domain.timelog.policy``

  Current addon override examples:

  - ``reports.domain.reports.service`` (inherits ``domain.reports.service``)
  - ``tasks.domain.policy`` (inherits ``domain.tasks.policy``)

  **Application layer**

  - ``application.reports.service``
  - ``application.tasks.service``
  - ``application.timelog.service``
  - ``application.export.csv.service``
  - ``application.export.ical.service``
  - ``application.module.activation.service``

  Current addon override examples:

  - ``reports.application.reports.service`` (inherits ``application.reports.service``)
  - ``tasks.application.service`` (inherits ``application.tasks.service``)

  **Integration layer**

  - ``report.mail.delivery``

  Current addon override example:

  - ``mail_sender.report.mail.delivery`` (inherits ``report.mail.delivery``)

  Minimal pattern::

    from gtimelog.models import Service

    class MyOverride(Service):
      _name = 'my.addon.override'
      _inherit = 'application.tasks.service'

      def should_download_after_remote_edit(self, editing_remote_tasks):
        return super().should_download_after_remote_edit(editing_remote_tasks)


Development
-----------

**Run tests**::

  python -m pytest src/gtimelog/tests/ --override-ini="python_files=test_*.py" -q

**Build translations** (from addon ``i18n/`` sources to compiled ``.mo``)::

  make mo-files

**Update translation templates** (merges ``.pot`` and updates ``.po``)::

  make update-translations

**Check modular architecture**::

  make architecture-check

Architecture target: docs/Module_Architecture_Target.md
Dependency matrix: docs/Addon_Dependency_Matrix.md
Migration status: docs/Migration_Status.md

**Measure coverage**::

  python -m coverage run --source=src/gtimelog -m pytest src/gtimelog/tests/ \\
      --override-ini="python_files=test_*.py" -q
  python -m coverage report

**Cyclomatic complexity**::

  radon cc src/gtimelog/ -a -s --exclude='src/gtimelog/tests/*'


Documentation
-------------

- `docs/index.rst`_ — full user guide (activities, categories, reports, …)
- `docs/formats.rst`_ — data file formats (``timelog.txt``, ``tasks.txt``)

.. _docs/index.rst: https://github.com/gtimelog/gtimelog/blob/master/docs/index.rst
.. _docs/formats.rst: https://github.com/gtimelog/gtimelog/blob/master/docs/formats.rst


Resources
---------

Website: https://gtimelog.org

Mailing list: gtimelog@googlegroups.com
(`archive <https://groups.google.com/group/gtimelog>`_)

IRC: #gtimelog on chat.libera.net

Source code: https://github.com/gtimelog/gtimelog

Bug tracker: https://github.com/gtimelog/gtimelog/issues


Credits
-------

GTimeLog was mainly written by Marius Gedminas <marius@gedmin.as>.

Barry Warsaw <barry@python.org> stepped in as a co-maintainer when
Marius burned out.  Then Barry got busy and Marius recovered.

Many excellent contributors are listed in `CONTRIBUTORS.rst`_.

.. _CONTRIBUTORS.rst: https://github.com/gtimelog/gtimelog/blob/master/CONTRIBUTORS.rst
