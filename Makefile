#
# Options
#

PYTHON = python3
FILE_WITH_VERSION = src/gtimelog/__init__.py
FILE_WITH_CHANGELOG = CHANGES.rst

# Let's use the tox-installed coverage because we'll be sure it's there and has
# the necessary plugins.
COVERAGE = .tox/coverage/bin/coverage

#
# Interesting targets
#

manpages = gtimelog.1
mo_dir = src/gtimelog/locale
addons_dir = src/gtimelog/addons
# Discover languages from addon i18n/ dirs (e.g. en, fr, lt, nb, nl)
i18n_langs = $(sort $(basename $(notdir $(wildcard $(addons_dir)/*/i18n/*.po))))
mo_files = $(patsubst %,$(mo_dir)/%/LC_MESSAGES/gtimelog.mo,$(i18n_langs))
schema_dir = src/gtimelog/data
schema_files = $(schema_dir)/gschemas.compiled
runtime_files = $(schema_files) $(mo_files)

.PHONY: all
all: $(manpages) $(runtime_files)       ##: build everything

.PHONY: run
run: $(runtime_files)                   ##: run directly from the source tree
	./gtimelog

.PHONY: test
test:                                   ##: run tests
	tox -p auto

.PHONY: check
check: check-desktop-file check-appstream-metadata ##: run tests and additional checks

.PHONY: check
check-desktop-file:                     ##: validate desktop file
	desktop-file-validate gtimelog.desktop

.PHONY: check
check-appstream-metadata:               ##: validate appstream metadata file
	appstreamcli validate --strict --explain --pedantic gtimelog.appdata.xml


.PHONY: coverage
coverage:                               ##: measure test coverage
	python -m pytest --cov=src/gtimelog --cov-report=term-missing:skip-covered --cov-report=html -q

.PHONY: coverage-diff
coverage-diff: coverage                 ##: find untested code in this branch
	python -m coverage xml
	diff-cover coverage.xml

.PHONY: lint
lint:                                   ##: run ruff linter
	ruff check src/ scripts/ setup.py

.PHONY: format
format:                                 ##: auto-format code with ruff
	ruff check --fix src/ scripts/ setup.py
	ruff format src/ scripts/ setup.py

.PHONY: format-check
format-check:                           ##: check formatting without changing files
	ruff format --check src/ scripts/ setup.py

.PHONY: security
security:                               ##: run security checks (bandit)
	bandit -c pyproject.toml -r src/ -q

.PHONY: complexity
complexity:                             ##: show cyclomatic complexity hotspots
	radon cc src/ -s -a -nc

.PHONY: architecture-check
architecture-check:                     ##: validate modular addon architecture
	$(PYTHON) scripts/module_architecture_check.py
	$(PYTHON) scripts/check_inherit_name_rule.py

.PHONY: inherit-name-check
inherit-name-check:                     ##: enforce _inherit/_name extension convention
	$(PYTHON) scripts/check_inherit_name_rule.py

.PHONY: quality
quality: architecture-check             ##: full quality gate (complexity + coverage + ascii report)
	python scripts/quality_gate.py

.PHONY: pre-commit
pre-commit:                             ##: run all pre-commit hooks on all files
	pre-commit run -a

.PHONY: pre-commit-install
pre-commit-install:                     ##: install pre-commit git hooks
	pre-commit install
	pre-commit install --hook-type pre-push

.PHONY: update-translations
update-translations:                    ##: merge addon .pot files and update all addon .po files
	@merged_pot=$$(mktemp); \
	  msgcat --use-first $$(find $(addons_dir)/*/i18n -name '*.pot') -o $$merged_pot; \
	  for po in $$(find $(addons_dir)/*/i18n -name '*.po'); do \
	    echo "Updating $$po"; \
	    msgmerge -U $$po $$merged_pot; \
	  done; \
	  rm -f $$merged_pot

.PHONY: mo-files
mo-files: $(mo_files)                   ##: merge addon .po and compile to .mo

# For each language, merge all addon i18n/<lang>.po into a single .mo
$(mo_dir)/%/LC_MESSAGES/gtimelog.mo: $(wildcard $(addons_dir)/*/i18n/%.po)
	@mkdir -p $(@D)
	@msgcat --use-first $(wildcard $(addons_dir)/*/i18n/$*.po) | msgfmt -o $@ -

.PHONY: flatpak
flatpak:                                ##: build a flatpak package
	# you may need to install the platform and sdk before this will work
	# flatpak install flathub org.gnome.Platform//3.82 org.gnome.Sdk//3.38
	# note that this builds the code from git master, not your local working tree!
	flatpak-builder --force-clean build/flatpak flatpak/org.gtimelog.GTimeLog.yaml
	# to run it do
	# flatpak-builder --run build/flatpak flatpak/org.gtimelog.GTimeLog.yaml gtimelog

.PHONY: flatpak-install
flatpak-install:                        ##: build and install a flatpak package
	# you may need to install the platform and sdk before this will work
	# flatpak install flathub org.gnome.Platform//3.38 org.gnome.Sdk//3.38
	# note that this builds the code from git master, not your local working tree!
	flatpak-builder --force-clean build/flatpak flatpak/org.gtimelog.GTimeLog.yaml --install --user
	# to run it do
	# flatpak run org.gtimelog.GTimeLog


$(schema_files): $(schema_dir)/org.gtimelog.gschema.xml
	glib-compile-schemas $(schema_dir)

.PHONY: clean
clean:                                  ##: clean build artifacts
	rm -rf temp tmp build gtimelog.egg-info $(runtime_files) $(mo_dir)
	find -name '*.pyc' -delete

include release.mk

.PHONY: distcheck
distcheck: distcheck-wheel    # add to the list of checks defined in release.mk
distcheck: distcheck-appdata  # add to the list of checks defined in release.mk

.PHONY: distcheck-wheel
distcheck-wheel:
	@pkg_and_version=`$(PYTHON) setup.py --name`-`$(PYTHON) setup.py --version` && \
	  unzip -l dist/$$pkg_and_version-py2.py3-none-any.whl | \
	  grep -q gtimelog.mo && \
	  echo "wheel seems to be ok"

APPDATA_FILE = gtimelog.appdata.xml
APPDATA_FORMAT = "<release version="'"'$(changelog_ver)'"'" date="'"'"$(changelog_date)"'"'" />"

.PHONY: distcheck-appdata
distcheck-appdata:
	@ver_and_date=$(APPDATA_FORMAT) && \
	    grep -q "^$$ver_and_date$$" $(APPDATA_FILE) || { \
	        echo "$(APPDATA_FILE) has no entry for $$ver_and_date"; exit 1; }

%.1: %.rst
	rst2man $< > $@

%.5: %.rst
	rst2man $< > $@

.PHONY: update-github-branch-protection-rules
update-github-branch-protection-rules:  ##: update GitHub branch protection rules
	uv run --script .github/update_branch_protection_rules.py
