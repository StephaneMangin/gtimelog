Contributing to GTimeLog
========================

Contributions are welcome, and not just code patches.  I'd love to see

* user interface design sketches
* icons
* documentation
* translations
* installers for Mac OS X and Windows


Bugs
----

Please `use GitHub <https://github.com/gtimelog/gtimelog/issues>`_ to
report bugs or feature requests.

We also have an older issue tracker on `Launchpad
<https://bugs.launchpad.net/gtimelog/>`_.  Some bugs haven't been moved
over to GitHub yet.

You may also contact Marius Gedminas <marius@gedmin.as> or Barry Warsaw
<barry@python.org> by email.


Source code
-----------

It's on GitHub: https://github.com/gtimelog/gtimelog

Get the latest version with ::

    $ git clone https://github.com/gtimelog/gtimelog

Run it without installing ::

    $ cd gtimelog
    $ make
    $ ./gtimelog


Development setup
-----------------

Install the pre-commit hooks (required once per clone)::

    $ pip install pre-commit
    $ pre-commit install
    $ pre-commit install --hook-type pre-push

Or use the Makefile shortcut::

    $ make pre-commit-install

This installs git hooks that automatically run **ruff** (linting +
formatting), **bandit** (security), **xenon** (complexity gate), XML
validation, and manifest checks on every commit.  Coverage is checked on
``git push``.


Code quality tools
------------------

All tooling is configured in ``pyproject.toml``.

**Ruff** (replaces flake8, isort, black, pyupgrade, pydocstyle)::

    $ ruff check src/                # lint
    $ ruff check --fix src/          # lint + auto-fix
    $ ruff format src/               # format
    $ make lint                      # lint via Makefile
    $ make format                    # auto-fix + format

**Security** (bandit)::

    $ make security

**Complexity** (radon / xenon)::

    $ make complexity                # show hotspots
    $ make quality                   # full ASCII quality gate report

**Pre-commit** (all hooks at once)::

    $ pre-commit run -a              # run everything
    $ make pre-commit                # same via Makefile


Tests
-----

Run the test suite with ::

    $ python -m pytest

or, to test against all supported Python versions ::

    $ pip install tox
    $ tox

Run with coverage::

    $ make coverage

The full quality gate (complexity + coverage + ASCII report)::

    $ make quality
